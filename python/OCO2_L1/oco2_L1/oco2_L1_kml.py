#!/usr/bin/env python
"""
Makes KML files for OCO2 level 1b hdf5 data files.

This is based on the tools developed for making kmls for L2 Xco2 data,
but has been adapted for making L1 kmls.

lat_range argument specifies the range of data to plot

Polygons are plotted with the correct footprints for all footprints
within the latitude range. Polygons have transparent fill (alpha='00'),
and a medium grey outline.

<ExtendedData> has tags for sounding latitude, sounding longitude, 
solar zenith, solar azimuth, sounding zenith, sounding azimuth.


Command Line Interface:
python oco2_L1_kml.py input_file output_file time [latitudes]
Args:
    input_file: file name of OCO2 Level 1 file
    output_file: file name to save kmz as
    time: time, formatted as YYYY-mm-dd for MODIS data
    --latitudes or -lat: 2 arguments, giving minimum and maximum
    latitude to show
"""

import h5py
import os
import sys
import argparse
import datetime as dt
import zipfile

import KML
import KMLFormats

"""
NOTE:

the operation mode should be read using path
  'Metadata/OperationMode'
but the files I had to test this with did not have this field.

Update the file_paths dictionary with
    op_mode='Metadata/Operationmode',

uncomment the line
# op_mode = datasets['operation_mode'][i,j],

and remove the line assigning
op_mode = 'ND'

to read the operation mode correctly
"""

module_description = 'Creates KML files to map OCO2-L1 data in Google Earth'

# add 'op_mode':'Metadata/OperationMode' to read operation mode correctly
file_paths = {'vertex_latitude':'FootprintGeometry/footprint_vertex_latitude',
              'vertex_longitude':'FootprintGeometry/footprint_vertex_longitude',
              'sounding_latitude':'SoundingGeometry/sounding_latitude',
              'sounding_longitude':'SoundingGeometry/sounding_longitude',
              'sounding_solar_azimuth':'SoundingGeometry/sounding_solar_azimuth',
              'sounding_solar_zenith':'SoundingGeometry/sounding_solar_zenith',
              'sounding_zenith':'SoundingGeometry/sounding_zenith',
              'sounding_azimuth':'SoundingGeometry/sounding_azimuth',
              'operation_mode':'Metadata/OperationMode'}

poly_fill_colour = '00ffffff' # white, opacity=0

def plot(file, output_file, time, lat_range):
    """Makes KML files for mapping OCO-2 L1 data.
    
    time must be formatted as YYYY-mm-dd
    """
    
    print "Opening file", file
    L1_data = h5py.File(file, 'r')
    
    datasets = {}
    for (name, path) in file_paths.iteritems():
        datasets[name] = L1_data[path]
    
    dim = len(datasets['vertex_latitude'])
    
    kml_description = KMLFormats.oco2_header_description.format(time)
    print "Making KML"
    kml = KML.KML(description=kml_description)
    root_folder = KML.Folder('Footprint Outlines')
    kml.add_folder(root_folder)
    
    for i in range(dim):
        for j in range(8):
            sounding_lat = datasets['sounding_latitude'][i,j]
            if lat_range[0]<=sounding_lat<=lat_range[1]:
                lats = datasets['vertex_latitude'][i,j][0]
                lons = datasets['vertex_longitude'][i,j][0]
                sounding_lon = datasets['sounding_longitude'][i,j]
                solar_zenith = datasets['sounding_solar_zenith'][i,j]
                solar_azimuth = datasets['sounding_solar_azimuth'][i,j]
                sounding_zenith = datasets['sounding_zenith'][i,j]
                sounding_azimuth = datasets['sounding_azimuth'][i,j]
                op_mode = datasets['operation_mode'][0]
                
                poly = KML.Polygon(lats, lons, i+j, poly_fill_colour, outline=True)
                poly.add_data(KML.DataPoint('Sounding Latitude', sounding_lat))
                poly.add_data(KML.DataPoint('Sounding Longitude', sounding_lon))
                poly.add_data(KML.DataPoint('Solar Zenith Angle', solar_zenith))
                poly.add_data(KML.DataPoint('Solar Azimuth Angle', solar_azimuth))
                poly.add_data(KML.DataPoint('Sounding Zenith Angle', sounding_zenith))
                poly.add_data(KML.DataPoint('Sounding Azimuth Angle', sounding_azimuth))
                poly.add_data(KML.DataPoint('File', os.path.split(file)[1]))
                poly.add_data(KML.DataPoint('Operation Mode', op_mode))
                
                root_folder.add_object(poly)
    kml.write(output_file)
    L1_data.close()
    print "Saved file as", output_file
    
def main():
    parser = argparse.ArgumentParser(description=module_description)
    parser.add_argument('input_file', help='OCO2 Level 1 file to map')
    parser.add_argument('output_file', help='File name for output kmz')
    parser.add_argument('time', help='time formatted as YYYY-mm-dd')
    parser.add_argument('-lat','--latitudes', help='latitude range to plot', nargs=2, default=[-90,90], type=float)
    args = parser.parse_args()
    plot(args.input_file, args.output_file, args.time, args.latitudes)
    
if __name__ == "__main__":
    main()