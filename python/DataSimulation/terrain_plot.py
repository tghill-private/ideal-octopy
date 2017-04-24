#!/bin/usr/env python
"""
Creates imshow and 3D surface plots for a terrain map array.

Function imshow_terrain creates an imshow plot, and
plot_3d_terrain makes a 3D surface plot. Both of these
together give a good way to visualize the terrain
being used to create a bias in the Xco2
emissions estimation

Command line interface:
python terrain_plot.py [terrain array file name] [type of plot]

type of plot can be 'both', 'imshow', or '3d'
"""

import os
import argparse

import numpy as np
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def imshow_terrain(terrain_file):
    terrain = np.loadtxt(terrain_file)
    fig, ax = plt.subplots()
    
    image = ax.imshow(terrain, origin='lower')
    ax.set_xlabel('Column')
    ax.set_ylabel('Row')
    
    ax.set_title('Terrain Height (Normalized to 1)')
    
    cbar = fig.colorbar(image, ax=ax)
    cbar.set_label('Height (relative units)')
    
    im_name, _ = os.path.splitext(terrain_file)
    figname = im_name + '_imshow' + '.png'
    fig.savefig(figname, dpi=600)
    print 'Plot saved as', os.path.realpath(figname)

def plot_3d_terrain(terrain_file):
    terrain = np.loadtxt(terrain_file)
    dim = terrain.shape[0]
    X = np.linspace(0., 60., dim)
    Y = np.linspace(0., 60., dim)
    X, Y = np.meshgrid(X, Y)
    fig = plt.figure()
    nax = fig.gca(projection='3d')
    nax.set_title('Normalized Terrain Height (relative units)')
    nax.set_xlabel('x')
    nax.set_ylabel('y')
    nax.set_zlabel('Height (relative units)')
    nplt = nax.plot_surface(X, Y, terrain, cmap='gist_ncar', lw=0.1)
    fig.colorbar(nplt, ax=nax) 
    im_name, _ = os.path.splitext(terrain_file)
    figname = im_name + '_3d' + '.png'
    plt.savefig(figname, dpi=400)   
    print 'Plot saved as', os.path.realpath(figname)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('terrain_file', help='file to take terrain data from')
    parser.add_argument('type', help='type of plot to make')
    args = parser.parse_args()
    file = args.terrain_file
    if args.type=='both':
        imshow_terrain(file)
        plot_3d_terrain(file)
    elif args.type=='imshow':
        imshow_terrain(file)
    elif args.type=='3d':
        plot_3d_terrain(file)
    else:
        raise TypeError("'type' must be one of 'both', '3d', or 'imshow'")
    
if __name__ == '__main__':
    main()