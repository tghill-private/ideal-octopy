"""
Module KML.py

KML files are saved as zipped, compressed .kmz files to save space.

Objects you can include are Overlays, Polygons, and Placemarks.
Each element can be added to specified folders, in any given
structure.

Since no strings are written until the final KML.write() call,
objects can be made and modified in any order, and the changes
will always be written to the kml file.

Example:
kml = KML(name='Example', description='Put description here')

subfolder = Folder("Subfolder", "First subfolder")

lats = [1, 1, 2, 2, 1]
lons = [2, 3, 3, 2, 2]
id = "Square"
colour='aaff9f3d' # hex colour
poly = Polygon(lats, lons, id, colour)

subfolder.add_object(poly)

kml.add_object(poly)

kml.write('test.kmz')


KML Reference: https://developers.google.com/kml/documentation/kmlreference
"""

import os
import zipfile
from StringIO import StringIO

import KMLFormats as Formats
import Geometry

modis_description_fmt = Formats.oco2_header_description.format(Formats.modis_time_fmt)
# The description that includes the download link for MODIS data

default_cmin = 390
default_cmax = 410
default_cbar_name = "colour_bar.png"

class KML(object):
    """Makes a file following the KML standard for use in Google Earth.
    
    This class supports hierarchial files, with one or many layers
    of folders and subfolders.
    """
    def __init__(self, name="", description=""):
        self.description = description
        self.folders = {'':Folder("Root", "Root Folder")}
        self.name = name
        self.auxillary_files = []
    
    def add_folder(self, folder, ref_name=None):
        """Creates a folder in the kml document"""
        key = ref_name if ref_name else folder.name
        if key in self.folders:
            raise KeyError("Folder '%s' is already in KML" % key)
        
        else:
            self.folders[key] = folder
    
    def add_object(self, element, folder='', file=None):
        """Adds any type of object as long as it has a write method"""
        if folder in self.folders:
            self.folders[folder].add_object(element)
            if file:
                self.auxillary_files.append(file)
        if hasattr(element, 'files'):
            if hasattr(element.files, '__iter__'):
                self.auxillary_files.extend(element.files)
            else:
                self.auxillary_files.append(element.files)
        else:
            raise KeyError("Folder '%s' does not exist in KML" % folder)
        
        
    def write(self, fname):
        """Writes a KML object to a compressed zip archive"""
        absolute_path = os.path.abspath(fname)
        save_dir = os.path.dirname(absolute_path)
        
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)
        
        if self.name=="":
            self.name = os.path.splitext(os.path.split(fname)[1])[0]
        
        header = Formats.file_header.format(name=self.name, description=self.description)
        footer = Formats.file_footer
        
        kml_output = StringIO()
        kml_output.write(header)
        root_contents = self.folders.pop("").contents
        kml_output.write(''.join([item.write() for item in root_contents]))
        kml_output.write(''.join([folder.write() for folder in self.folders.values()]))
        kml_output.write(footer)
        
        with zipfile.ZipFile(fname, 'w', compression=zipfile.ZIP_DEFLATED) as kmz:
            kml_name = fname.replace('.kmz','.kml')
            kmz.writestr(kml_name, kml_output.getvalue())
            for file in self.auxillary_files:
                kmz.write(file, os.path.split(file)[1])

class Folder(object):
    """Folder objects to be added to KML objects.
    
    Once a Folder is made, it can be added to a KML
    object using the KML.add_object() method
    """
    def __init__(self, name, description=""):
        self.name = name
        self.description = description
        self.contents = []
    
    def write(self):
        header = Formats.folder_header.format(name=self.name, description=self.description)
        footer = Formats.folder_footer
        body = ''.join([item.write() for item in self.contents])
        return ''.join([header, body, footer])
    
    def add_object(self, element):
        self.contents.append(element)
    
    def __repr__(self):
        return "'Folder('%s', '%s')" % (self.name, self.description)
    
    def __str__(self):
        return "<Folder '%s'>" % self.name
    
class Overlay(object):
    """Creates a string corresponding to a KML overlay.
    
    Uses wind_arrow and colour_scale functions to make the
    wind arrows and colour scales in the KML files.
    
    Can add to a folder or KML object using their
    respectve add_object methods.
    """
    def __init__(self, text, files=[]):
        self.text = text
        self.files = files
    
    def write(self):
        return self.text
    
class Polygon:
    """Creates Polygons for use in a KML file.
    
    Inlcudes method to add ExtendedData to the polygon (we use
    this for showing different bias correction, surface pressure, etc
    """
    def __init__(self, lats, lons, id, colour, outline=False):
        """Fields are:
        * lats, an iterable of corner latitudes for the polygon, in any order (same order as lons)
        * lons, an iterable of corner longitudes for the polygon in any order (same order as lats)
        * id, the sounding id; used for style id and polygon name
        * colour, the colour to use for this polygon
        """
        self.boundary = 1 if outline else 0
        self.boundary_colour = 'ffa9a9a9' if outline else '000000'
        self.coordinates = Coord(list(lats),list(lons),750)
        self.name = id
        self.data = Data()
        self.colour = colour
    
    def __repr__(self):
        return self.header+self.body+self.footer

    def add_data(self, data):
        dtype_err = "data is urecognized type '%s'; must be Data or DataPoint"
        if isinstance(data, DataPoint):
            self.data.add_data_field(data)
        elif isinstance(data, Data):
            self.data = data
        else:
            raise TypeError(dtype_err % type(data))

    def add_all_data(self, data_list):
        for data_obj in data_list:
            self.data.add_data_field(data_obj)
            
    def write(self):
        header = Formats.Poly_Head.format(name=self.name, fill_color=self.colour,
                               outline=self.boundary, line_color=self.boundary_colour)
        body = Formats.Poly_Body.format(name=self.name)
        footer = Formats.Poly_Foot.format(color=self.colour)
        poly_string = "".join([header, self.data.write(), body,
                               self.coordinates.write(), footer])
        return poly_string

class DataPoint(object):
    """Represents KML data, storing name and value"""
    def __init__(self, name, value):
        self.name = name
        self.value = str(value)
    
    def write(self):
        return Formats.Data_Format.format(name=self.name, value=self.value)
    
    def __repr__(self):
        return "<DataPoint '%s': '%s'>" % (self.name, self.value)
    
    def __str__(self):
        return "DataPoint field '%s'" % self.name

class Data(object):
    """Stores many DataPoint objects, and represents
    data points as a string to add to KML file.
    """
    def __init__(self):
        self.data_fields = []
        
    def add_data_field(self, data):
        self.data_fields.append(data)
    
    def add_new_data(self, name, value):
        new_data = DataPoint(name, value)
        self.data_fields.append(new_data)
    
    def write(self):
        body = "".join([data.write() for data in self.data_fields])
        header = Formats.Data_Header
        footer = Formats.Data_Footer
        return "".join([header, body, footer])
        
class Placemark(object):
    """Makes a KML Placemark object"""
    def __init__(self, name, lat, lon):
        self.name = name
        self.coordinates = (lat, lon)
    
    def write(self):
        lat, lon = self.coordinates
        placemark = Formats.placemark.format(name, lon, lat)
        return placemark
            
class Coord:
    """Computes the convex hull order of four coordinate points, and returns a string formatted as a KML
    coordinate tag, containing the four coordinates passed to it"""
    def __init__(self, lat_list, lon_list, alt=750):
        """Fields: lats, lons, altitude.
        lats: list of corner latitudes
        lons: list of corner longitudes
        alt: altitude for the final ploygons in Google Earth"""
        points = [(lon_list[0],lat_list[0]),
                  (lon_list[1],lat_list[1]),
                  (lon_list[2],lat_list[2]),
                  (lon_list[3],lat_list[3]) ]
        arranged = Geometry.convex_hull(points)
        
        if len(arranged)<=3:
            kml_coord = ''
            coord = ''
        else:
            v1 = '{0},{1},{2} '.format(arranged[0][0],arranged[0][1],alt)
            v2 = '{0},{1},{2} '.format(arranged[1][0],arranged[1][1],alt)
            v3 = '{0},{1},{2} '.format(arranged[2][0],arranged[2][1],alt)
            v4 = '{0},{1},{2} '.format(arranged[3][0],arranged[3][1],alt)
            kml_coord = v1+v2+v3+v4+v1
            coord = Formats.polygon_coordinates.format(coord=kml_coord)
        
        self.coord = coord
    
    def write(self):
        return self.coord
        
