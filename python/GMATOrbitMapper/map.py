#!/usr/bin/env python
"""
Script to plot GMAT Orbit data in a Google Earth KMZ.

This script includes every other point that exists in the GMAT
files, and includes a limited number of rows to avoid crashing
Google Earth when you try to open it

Command Line Interface:

map.py [-h] [-i INDICES INDICES] [-o OUTPUT] [-c COLOUR] [-w WIDTH]
              [-n NAME]
              orbit_file

Args:
    * orbit_file: path name to the orbit file you want to map
    * -o --output (optional): path name to output kmz file. Defaults
        to the input file with the extension changed to 'kmz'
    * -c --colour: GE hex-string (aabbggrr) giving the colour to
        use for the line string
    * -w --width: Integer line width for Google Earth
    * -n --name: Name to display in Google Earth
    * -i --indices: (length-2) first and last rows to plot
"""

import argparse
import os

from kml import KML
from kml import namespace

defaults = namespace.Namespace(
indices = [0, 2000],
output = None,
colour = 'FF0000FF',
width = 4,
name = 'GMAT Orbit',
)

def map(orbit_data, output_file, colour, width, indices):
    """Maps GMAT data from the file orbit_data as a KMZ file"""
    print "Creating map for orbit file", orbit_data
    coords = []
    if not os.path.exists(orbit_data):
        raise IOError('File "%s" does not exist' % orbit_data)
    with open(orbit_data, 'r') as orbit:
        for i,row in enumerate(orbit):
            if indices[0]<=i<=indices[1] and i%2==0:
                try:
                    lat, lon = [float(x) for x in row.split()[:2]]
                except:
                    print row
                    print i
                    raise
                coords.append((lon, lat))
            else:
                pass
    
    line_style = KML.LineStyle(colour=colour, width=width, id='GroundTrack')
    
    print "Making KML"
    coord = KML.Coord(coords)
    track = KML.LineString(coord, style=line_style,
        name = 'GMAT Orbit Track',
        description = 'Ground track for GMAT orbit from file %s' %
                        os.path.split(orbit_data)[-1])
    
    map = KML.KML(name='GMAT Orbit')
    map.add_object(track)
    
    if output_file is None:
        output_file = os.path.join(os.path.splitext(orbit_data)[0], '.kmz')
    map.write(output_file)
    print "File saved as", os.path.realpath(output_file)
    
def main():
    """Command-line interface for script"""
    parser = argparse.ArgumentParser()
    parser.add_argument('orbit_file',
        help = 'Path to GMAT orbit file to map')
    parser.add_argument('-i', '--indices',
        help = 'Lines from orbit file to plot',
        default = defaults.indices, nargs=2, type=int)
    parser.add_argument('-o', '--output',
        help='File path to save kmz file as (default to same dir as orbit file)',
        default = None)
    parser.add_argument('-c','--colour', help='Hex colour to use (aabbggrr)',
        default = defaults.colour)
    parser.add_argument('-w', '--width',
        help = 'Relative line width to plot',
        default = defaults.width, type=int)
    parser.add_argument('-n', '--name',
        help='Name for KML document to show in Google Earth',
        default = defaults.name)
    
    args = parser.parse_args()
    
    map(args.orbit_file, args.output, args.colour, args.width, args.indices)

if __name__ == '__main__':
    main()