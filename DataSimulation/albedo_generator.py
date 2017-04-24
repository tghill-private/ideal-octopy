#!/usr/bin/env python
"""
Generates the simulated albedo map

Uses perlin noise from the noise module to generate a 2D array
of correlated noise, and classifies by the values in thresholds
to produce an array of 0s, 1s, and 2s representing different
surface albedos
"""

import noise
import numpy as np

from matplotlib import pyplot as plt
import os
import argparse

base = 1.6

thresholds = [-0.5, 1.0]

def simulate(base=base, size=1200):
    print 'Simulating surface albedo'
    shape = (size, size)
    surf_albedo = np.zeros(shape)
    print 'Generating coherent noise'
    for x in range(size):
        for y in range(size):
            xp = x/(2*float(size))
            yp = y/(2*float(size))
            rval = noise.snoise2(xp, yp, base=base)
            rval2 = noise.snoise2(xp, yp, base=base+1)
            surf_albedo[x,y]=0.5*(rval+rval2)
            
    surf_albedo-=np.mean(surf_albedo)
    surf_albedo/=np.mean(np.abs(surf_albedo))
    
    final_albedo = np.zeros(shape)
    final_albedo[surf_albedo>thresholds[1]]=2
    final_albedo[surf_albedo<thresholds[1]]=1
    final_albedo[surf_albedo<thresholds[0]]=0
    
    np.savetxt('../Data/albedo_map', final_albedo)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('base', type=float, default=base, nargs='?')
    args = parser.parse_args()
    simulate(base=base)