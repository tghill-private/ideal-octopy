#!/bin/usr/env python
"""
Simulates a terrain map for simulating biases in Xco2 data.

Uses noise package to generate 2D coherent noise and create
a gridded array simulating terrain height.

The height array is normalized to be between 0 and 1, corresponding
to only positive elevations, and can be easily scaled to match
any magnitude of any height changes you want.

The array is saved (using numpy.savetxt) to the file 'simulated_terrain'.

_____________________________________________________________________

Command Line Interface:
Args:
 * size: side length of the resulting array
 
Usage:
python terrain_generator.py 1200
"""

import argparse
import os

import noise
import numpy as np

base = 0.25 # determined empirically from trying different values

def simulate(size):
    """Simulates terrain height and creates 3D plot for the terrain"""
    print "Simulating terrain at %s x %s resolution" % (size, size)
    dim = size
    array_shape = (dim, dim)
    terrain_factor = np.zeros(array_shape)
    print "Generating coherent noise..."
    for x in range(dim):
        for y in range(dim):
            terrain_factor[x,y]+=noise.snoise2(x/float(dim) ,y/float(dim), base=base)
    
    print "Normalizing terrain array"
    terrain_factor[terrain_factor<0]=0.  
    max_ratio = np.max(terrain_factor)
    terrain_factor = terrain_factor/max_ratio
    
    print "Saving array..."
    np.savetxt('/home/tim/DataSimulation/Data/simulated_terrain', terrain_factor)
    print 'Saved terrain array as', os.path.realpath('simulated_terrain')
        

def main():
    """Parses command line arguments and calls simulate function to
    generate a terrain map
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--size', help='Side length of terrain map array', type=int, default=1200)
    args = parser.parse_args()
    simulate(size=args.size)
    
if __name__ == "__main__":
    main()