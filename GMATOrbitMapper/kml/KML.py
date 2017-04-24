"""
Module KMLv2.py

This module makes KML files tailored for OCO-2 Sat Data, but can be general.

The underlying idea is of course everything is a class, and every type
of thing that can be made in the KML (Folder, polygon, wind arrows
overlays, etc), have a write() method. This way it is
completely general what objects go where.

KML Reference: https://developers.google.com/kml/documentation/kmlreference

** Updated 3 April 2017 to use io.ByteIO objects for the colour bar instead
of writing it to a file and adding that file to the kmz archive.
"""

from abc import ABCMeta, abstractmethod, abstractproperty
import os
import zipfile
from StringIO import StringIO
import shutil

import numpy as np

import KMLFormats as Formats
from namespace import Namespace

default_cmin = 390
default_cmax = 410
default_cbar_name = "colour_bar.png"

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
    
class KMLStyle(object):
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
    
    @abstractproperty
    def tag(self):
        """Require attribute "tag" for writing styleUrl in other object"""
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
        self.styles = []
    
    def add_folder(self, folder, ref_name=None):
        key = ref_name if ref_name else folder.name
        if key in self.folders:
            raise KeyError("Folder '%s' is already in KML" % key)
        
        else:
            self.folders[key] = folder
    
    def add_object(self, element, folder='', file=None):
        """Adds any type of object as long as it has a write method"""
        if hasattr(element, 'files'):
            if hasattr(element.files, '__iter__'):
                self.auxillary_files.extend(element.files)
            else:
                self.auxillary_files.append(element.files)
        
        if hasattr(element, 'byte_objects'):
            if element.byte_objects:
                if np.ndim(element.byte_objects)==1:
                    self.byte_objects.append(element.byte_objects)
                elif np.ndim(element.byte_objects)==2:
                    self.byte_objects.extend(element.byte_objects)
                else:
                    raise TypeError('"byte_objects" must be 1- or 2-dimensional')
        
        if hasattr(element, 'style'):
            if element.style!=None:
                self.styles.append(element.style)
        
        if folder in self.folders:
            self.folders[folder].add_object(element)
            if file:
                self.auxillary_files.append(file)
        else:
            raise KeyError("Folder '%s' does not exist in KML" % folder)
        
        
    def write(self, fname):
        """Saves the KML and associated files (wind arrow
        files, colour-bar file, etc.) to a compressed zipped archive
        to be opened in Google Earth"""
        absolute_path = os.path.abspath(fname)
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
                required_files.append(name)
                with open(name, 'w') as byte_obj:
                    dst = os.path.join(save_dir, os.path.split(name)[1])
                    print 'Writing %s to %s' % (name, dst)
                    byte_obj.write(obj.getvalue())
            
            with open(fname, 'w') as kml_output:
                kml_output.write(header)
                kml_output.write(''.join([styl.write() for styl in self.styles]))
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
            kml_output.write(''.join([styl.write() for styl in self.styles]))
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

class Coord(KMLObject):
    """Returns a string giving KML Coordinates from given coordinates
    coordinate tag, containing the four coordinates passed to it"""
    def __init__(self, coord):
        """Fields: coord
        coord is list of (lon, lat [,alt]):"""
        self.coord = coord
    
    def write(self):
        coordinates = ' '.join([','.join([str(t) for t in triple])
                                    for triple in self.coord])
        return coordinates

class LineStyle(KMLObject):
    defaults = Namespace(
            colour = 'ffffffff',
            id = 'StyleID',
            width = 2,
            )
    def __init__(self, **kwargs):
        self.args = LineStyle.defaults
        self.args.update(**kwargs)
        self.tag = Formats.StyleUrl.format(url=self.args.id)
    
    def write(self):
        return Formats.LineStyle.format(**self.args.asdict())

class LineString(KMLObject):
    defaults = Namespace(
            name = '',
            description = '',
            styletag = '',
            extrude = 1,
            tesselate = 1,
            style = None,
            coordinates = None,
        )
            
    def __init__(self, coordinates,  **kwargs):
        self.args = LineString.defaults
        self.args.update(**kwargs)
        self.args.update(coordinates = coordinates.write())
        self.style = self.args.style
        if self.style:
            self.args.update(styletag = self.style.tag)
    
    def write(self):
        return Formats.LineString.format(**self.args.asdict())
        
class PolyStyle(KMLObject):
    defaults = Namespace(
            fillcolour = 'ffa9a9a9',
            linecolour = 'ffa9a9a9',
            linewidth = 1,
            style = ''
        )
    def __init__(self, id, **kwargs):
        self.args = PolyStyle.defaults
        self.args.update(style=id, **kwargs)
        self.tag = Formats.StyleUrl.format(url=id)
        
    def write(self):
        return Formats.PolyStyle.format(**self.args.asdict())
        
class _OuterBoundary(KMLObject):
    
    def __init__(self, coord):
        self.coord = coord
    
    def write(self):
        return Formats.OuterBoundary.format(coordinates = self.coord.write())

class _InnerBoundary(KMLObject):
    
    def __init__(self, coord):
        self.coord = coord
    
    def write(self):
        return Formats.InnerBoundary.format(coordinates = self.coord.write())

class Polygon(KMLObject):
    defaults = Namespace(
            name = '',
            description = '',
            styleUrl = '',
            altitudeMode = 'relativeToGround',
            tessellate = '1',
            outerBoundary = '',
            innerBoundary = '',
            extrude = 0,
            data = '',
            LookAt = None,
        )
    
    def __init__(self, outerBoundary, innerBoundary=None,
                    style=None, **kwargs):
        outerBoundary = _OuterBoundary(outerBoundary)
        
        self.args = Polygon.defaults
        self.args.update(**kwargs)
        self.args.update(outerBoundary = outerBoundary.write())
        self.data = Data()
        
        if style:
            self.style = style
            self.args.update(styleUrl = style.tag)
            
        if innerBoundary:
            innerBoundary = _InnerBoundary(innerBoundary)
            self.args.update(innerBoundary = innerBoundary.write())
        
    def add_data(self, data):
        if hasattr(data, '__iter__'):
            for dta in data:
                self.data.add_data_field(dta)
        else:
            self.data.add_data_field(data)

    def write(self):
        lookat = self.args.LookAt
        if lookat:
            lookat = lookat.write()
        else:
            lookat = ''
        self.args.update(LookAt = lookat)
        self.args.update(data = self.data.write())
        return Formats.Polygon.format(**self.args.asdict())
        
class IconStyle(KMLObject):
    defaults = Namespace(
            scale = 1.3,
            x = 20,
            y = 2,
            xunits = 'pixels',
            yunits = 'pixels',
            id = '',
            icon = 'http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png'
        )
    
    def __init__(self, id, **kwargs):
        self.args = IconStyle.defaults
        self.args.update(id=id, **kwargs)
        self.tag = Formats.StyleUrl.format(url=id)
    
    def write(self):
        return Formats.IconStyle.format(self.args.asdict())


class Placemark(KMLObject):
    yellow_pushpin = IconStyle('yellow-pushpin')
    defaults = Namespace(
            name = 'Placemark',
            lon = '',
            lat = '',
            altitude = 0,
            heading = 0,
            tilt = 0,
            range = 0,
            styleUrl = '',
            LookAt = None,
        )
    
    def __init__(self, name, lat, lon,
                        style=yellow_pushpin, **kwargs):
        self.args = Placemark.defaults
        self.args.update(name=name, lat=lat, lon=lon, **kwargs)
        self.args.update(styleUrl = style.tag)
        
        if not self.args.LookAt:
            lookat = LookAt(self.args.lat, self.args.lon)
            self.args.LookAt = lookat
    
    def write(self):
        self.args.update
        self.args.update(LookAt = self.args.LookAt.write())
        placemark = Formats.placemark.format(**self.args.asdict())
        return placemark
        
class LookAt(KMLObject):
    defaults = Namespace(
            lon = '',
            lat = '',
            altitude = 0,
            tilt = 0,
            range = 25.e3,
            heading = 0,
            altitudeMode = 'relativeToGround',
        )
    
    def __init__(self, lat, lon, **kwargs):
        self.args = LookAt.defaults
        self.args.update(lat=lat, lon=lon, **kwargs)
    
    def write(self):
        return Formats.LookAt.format(**self.args.asdict())
        
class GroundOverlay(KMLObject):
    defaults = Namespace(
            name = '',
            drawOrder = 1,
            href = '',
            viewBoundScale = 0.75,
            north = None,
            east = None,
            west = None,
            south = None,
            rotation = 0,
            data = Data(),
            description = '',
            colour = 'ffffffff',
        )
    
    def __init__(self, north, east, south, west, href, **kwargs):
        self.args = GroundOverlay.defaults
        self.args.update(   north = north,
                            east = east,
                            south = south,
                            west = west,
                            href = href,
                            **kwargs
                        )
    
    def add_data(self, data):
        self.args.data.append(data)
    
    def write(self):
        self.args.update(data = self.args.data.write())
        return Formats.GroundOverlay.format(**self.args.asdict())
        
class ScreenOverlay(KMLObject):
    defaults = Namespace(
            name = '',
            description = '',
            href = '',
            
            xOverlay = 0,
            yOverlay = 1,
            xunitsOverlay='fraction',
            yunitsOverlay='fraction',
            
            xScreen = 0.01,
            yScreen = 0.99,
            xunitsScreen = 'fraction',
            yunitsScreen = 'fraction',
            
            xsize = 0.5,
            ysize = 0.1,
            xunits = 'fraction',
            yunits = 'fraction',
            
            xRotation = 0.5,
            yRotation = 0.5,
            xunitsRotation = 'fraction',
            yunitsRotation = 'fraction',
            
            rotation = 0,
        )
    
    def __init__(self, href, **kwargs):
        self.args = ScreenOverlay.defaults
        self.args.update(href = href, **kwargs)
    
    def write(self):
        return Formats.ScreenOverlay.format(**self.args.asdict())