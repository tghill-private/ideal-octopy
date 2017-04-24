"""
Module KMLv2.py

This module makes KML files tailored for OCO-2 Sat Data, but can be general.

The underlying idea is of course everything is a class, and every type
of thing that can be made in the KML (Folder, polygon, wind arrows
overlays, etc), have a write() method. This way it is
completely general what objects go where.

KML Reference: https://developers.google.com/kml/documentation/kmlreference
"""

from abc import ABCMeta, abstractmethod
import os
import zipfile
from StringIO import StringIO

import ReadWinds
import KMLFormats as Formats
import Geometry
import PST
import data
import shutil

modis_description_fmt = Formats.oco2_header_description.format(time=Formats.modis_time_fmt)
# The description that includes the download link for MODIS data

default_cmin = 390
default_cmax = 410
cbar_href = "colour_bar.png"

class KMLObject(object):
    """An Abstract Base Class for deriving KML Object classes.
    
    Enforces that each derived class must have a write method
    so that it is possible to write the final KML file. Derived
    classes should be KML Overlays, Polygons, Placemarks, etc.
    """
    __metaclass__ = ABCMeta
    def __init__(self):
        pass
    
    @abstractmethod
    def write(self):
        """Write a string representing the object using KML standards.
        
        Each derived class must implement this method so that
        the final KML can be created.
        """
        pass

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
        self.byte_objects = []
    
    def add_folder(self, folder, ref_name=None):
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
        else:
            raise KeyError("Folder '%s' does not exist in KML" % folder)
        if hasattr(element, 'files'):
            if hasattr(element.files, '__iter__'):
                self.auxillary_files.extend(element.files)
            else:
                self.auxillary_files.append(element.files)
        if hasattr(element, 'byte_object'):
            self.byte_objects.append(element.byte_object)
        
        
    def write(self, fname):
        """Saves the KML and associated files (wind arrow
        files, colour-bar file, etc.) to a compressed zipped archive
        to be opened in Google Earth"""
        absolute_path = os.path.realpath(fname)
        save_dir = os.path.dirname(absolute_path)
        
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)
        
        if self.name=="":
            self.name = os.path.splitext(os.path.split(fname)[1])[0]
        
        header = Formats.file_header.format(name=self.name,
                                            description=self.description)
        footer = Formats.file_footer
        
        extension = os.path.splitext(fname)[1]
        
        if extension=='.kml':
            save_dir = os.path.dirname(fname)
            required_files = [os.path.split(f)[1] for f in self.auxillary_files]
            for name, obj in self.byte_objects:
                dst = os.path.join(save_dir, os.path.split(name)[1])
                required_files.append(dst)
                with open(dst, 'w') as byte_obj:
                    print 'Writing', dst
                    byte_obj.write(obj.getvalue())
            
            with open(fname, 'w') as kml_output:
                kml_output.write(header)
                root_contents = self.folders.pop("").contents
                kml_output.write(''.join([itm.write() for itm in root_contents]))
                kml_output.write(''.join([folder.write() for folder in self.folders.values()]))
                kml_output.write(footer)
            
            for file in self.auxillary_files:
                dst = os.path.join(save_dir, os.path.split(file)[1])
                print 'Copying file %s to %s' % (file, dst)
                shutil.copy(file, dst)
            
            print 'Auxillary Files to Download:'
            print '\n'.join(required_files)
            
        elif extension=='.kmz':
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
                for byte_name, byte_object in self.byte_objects:
                    kmz.writestr(byte_name, byte_object.getvalue())
                    
        else:
            raise TypeError("Supported Extensions are '.kml', '.kmz'")

class Folder(KMLObject):
    """Folder objects to be added to KML objects.
    
    Once a Folder is made, it can be added to a KML
    object using the KML.add_object() method
    """
    def __init__(self, name, description=""):
        self.name = name
        self.description = description
        self.contents = []
    
    def write(self):
        header = Formats.folder_header.format(name=self.name,
                                              description=self.description)
        footer = Formats.folder_footer
        body = ''.join([item.write() for item in self.contents])
        return ''.join([header, body, footer])
    
    def add_object(self, element):
        self.contents.append(element)
    
    def __repr__(self):
        return "'Folder('%s', '%s')" % (self.name, self.description)
    
    def __str__(self):
        return "<Folder '%s'>" % self.name
    
class Overlay(KMLObject):
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
    
    @staticmethod
    def wind_arrow(overpass, lat=None, lon=None, size=0.02,
                                sources=['MERRA', 'ECMWF', 'GEM', 'Average']):
        """Creates a string which draws wind arrows in final KML file"""
                        
        
        arrows = ""
        input_lat = str(lat) if lat else "None"
        input_lon = str(lon) if lon else "None"
        
        if overpass.MERRA==overpass.ECMWF:
            w = PST.AllWinds(overpass)
            
            try:
                w.get_winds()
                wind_source = w
            
            except:
                wind_source = overpass

        else:
            # use winds from overpass instance
            wind_source = overpass
            
        MERRA_updated = wind_source.MERRA
        MERRA_beginning = wind_source.MERRA_beginning
        GEM = wind_source.GEM
        ECMWF_old = wind_source.ECMWF_old
        ECMWF = wind_source.ECMWF
        avg = wind_source.Average
        avg_old = wind_source.Average_old
        avg_beginning = wind_source.Average_beginning
        
        if ECMWF.speed>0.001:
            ECMWF_old = PST.Wind((0,0),0)
            avg_old = PST.Wind((0,0),0)
            
        source_map = {  'MERRA':(MERRA_updated, 'MERRA', 'MERRA'),
                        'ECMWF':(ECMWF,"ECMWF","ECMWF"),
                        'Average':(avg, "Average", "Average"),
                        'GEM':(GEM, 'GEM', 'GEM')
                    }
        winds = [source_map[src] for src in sources]
        wind_files = set([])
        
        lat = overpass.lat if lat==None else lat
        lon = overpass.lon if lon==None else lon

        # try:
            # gem_new = ReadWinds.get_gem_highres(overpass.time)
        # except IOError:
            # pass
        # except:
            # raise
        # else:
            # winds.append((gem_new,'GEM Forecast','GEM'))
        
        # try:
            # ecmwf_new = ReadWinds.get_ecmwf_highres(overpass.time,True)[0]
        # except IOError:
            # pass
        # except:
            # raise
        # else:
            # winds.append((ecmwf_new,'ECMWF (0.3 degree)','ECMWF'))
        
        winds_to_show = [w for w in winds if w[0].speed>0.001]
        winds_to_show = sorted(winds_to_show, key=lambda l: l[0].speed, reverse=True)
            
        for index,(wind,wind_source,wind_arrow_source) in enumerate(winds_to_show):
            speed = wind.speed
            north = lat + speed*size
            south = lat - speed*size
            east = lon + speed*size
            west = lon - speed*size
            heading = -90 - wind.bearing
            arrow = Formats.Arrow_Format.format(windsource=wind_source,
                                                description=str(wind),
                                                N=north, S=south,
                                                E=east, W=west,
                                                rotation=heading,
                                                arrow=wind_arrow_source,
                                                draworder=index+20)
            wind_file = os.path.join(data.kml_images, 
                                            'arrow_%s.png' % wind_arrow_source)
            wind_files.add(wind_file)
            arrows += arrow
        
        return Overlay(arrows, list(wind_files))
    
    @staticmethod
    def colour_scale(cbar, description="", width=0.5, height=0.08, x=0.05):
        scale = Formats.scale.format(   cbar=cbar_href,
                                        description=description,
                                        width=width, 
                                        height=height,
                                        x=x)
        cscale = Overlay(scale)
        cscale.byte_object = (cbar_href, cbar)
        
        return cscale
        
        
class Polygon(KMLObject):
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
        header = Formats.Poly_Head.format(style=self.name,
                                          fillcolour=self.colour,
                                          outline=self.boundary,
                                          linecolour=self.boundary_colour)
        body = Formats.Poly_Body.format(style=self.name)
        footer = Formats.Poly_Foot.format(fillcolour=self.colour)
        poly_string = "".join([header, self.data.write(), body,
                               self.coordinates.write(), footer])
        return poly_string

class DataPoint(KMLObject):
    def __init__(self, name, value):
        self.name = name
        self.value = str(value)
    
    def write(self):
        return Formats.Data_Format.format(name=self.name, value=self.value)
    
    def __repr__(self):
        return "<DataPoint '%s': '%s'>" % (self.name, self.value)
    
    def __str__(self):
        return "DataPoint field '%s'" % self.name
        
        
class Data(KMLObject):
    def __init__(self):
        self.data_fields = []
    
    def get_data(self, index, full_file, attrs=Formats.paths):
        for full_file_path, data_name in attrs:
            value = full_file[full_file_path][index]
            data_point = DataPoint(data_name, value)
            self.data_fields.append(data_point)
        
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

        
class Placemark(KMLObject):
    def __init__(self, name, lat, lon):
        self.name = name
        self.coordinates = (lat, lon)
    
    def write(self):
        lat, lon = self.coordinates
        placemark = Formats.placemark.format(name=name,
                                             lon=lon,
                                             lat=lat)
        return placemark
            
class Coord(KMLObject):
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
            coord = Formats.polygon_coordinates.format(coordinates=kml_coord)
        
        self.coord = coord
    
    def write(self):
        return self.coord
        
