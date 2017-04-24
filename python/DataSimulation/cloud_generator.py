#!/usr/bin/env python
import noise
import numpy as np

from matplotlib import pyplot as plt
import os

base = 3.5

def simulate(base, size=1200):
    """Simulates terrain height and creates 3D plot for the terrain"""
    print "Simulating terrain at %s x %s resolution" % (size, size)
    dim = size
    array_shape = (dim, dim)
    terrain_factor = np.zeros(array_shape)
    print "Generating coherent noise..."
    for x in range(dim):
        for y in range(dim):
            terrain_factor[x,y]+=noise.snoise2(x/float(dim) ,y/float(dim), base=base)
    
    terrain_factor[terrain_factor<0]=0.  
    max_ratio = np.max(terrain_factor)
    terrain_factor = terrain_factor/max_ratio
    
    # fig, ax = plt.subplots()
    # im = ax.imshow(terrain_factor, cmap='rainbow', origin='lower', vmin=0., vmax=1.)
    # ax.set_xlabel('Column')
    # ax.set_ylabel('Row')
    # ax.set_title('Simulated Cloud Fraction')
    # cbar = fig.colorbar(im)
    # cbar.ax.plot([0,1],[0.25,0.25], color='k')
    # ax.contour(terrain_factor, [0.25], colors='k', ls='--')
    # fig.savefig('Data/cloud_mask_full_colours.png', dpi=750)
    # plt.clf()
    
    terrain_factor = np.ma.masked_greater(terrain_factor, 0.25)
    
    print 'Generating cloud mask from random array'
    cloud_mask = np.zeros(array_shape)
    cloud_mask[terrain_factor<0.25]=1
    print cloud_mask
    fig, ax = plt.subplots()
    im = ax.imshow(cloud_mask, origin='lower', cmap='Greys')
    fig.colorbar(im, ax=ax)
    fig.savefig('terrain_test.png')
    
    np.savetxt('cloud_mask', cloud_mask)
    
if __name__ == '__main__':
    simulate(base, 1200)