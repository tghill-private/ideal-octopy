#!/usr/bin/env python
"""
Generates arrays for different swath widths/shapes for sampling
the simulated data as if the satellite wasn't a complete
imaging satellite
"""

import numpy as np
from matplotlib import pyplot as plt

def main():
    cm = 'Greys'
    sample = np.ones((1200, 400))
    nosample = np.zeros((1200,400))
    
    x_ax = np.linspace(0, 60, 1200)
    y_ax = np.linspace(0, 60, 1200)
    
    s1 = np.array([sample, nosample, nosample]).reshape(1200,1200).T
    s2 = np.array([nosample, sample, nosample]).reshape(1200,1200).T
    s3 = np.array([nosample, nosample, sample]).reshape(1200,1200).T
    s4 = np.zeros((1200,1200))
    left_edge_start = 600
    width=400
    for row in range(1200):
        if row%3==0:
            left_edge_start-=1
        s4[row,left_edge_start:left_edge_start+width+1]=1
    
    fig, axes = plt.subplots(nrows=2, ncols=2)
    ((ax1, ax2), (ax3, ax4)) = axes
    xticks = [0,20,40,60]
    yticks = [0,20,40,60]
    for ax in np.array(axes).flatten():
        ax.set_xticks(xticks)
        ax.set_yticks(yticks)
    
    fig.suptitle('Swath Location Masks')
    
    ax1.pcolormesh(x_ax, y_ax, s1, cmap=cm)
    ax1.set_title('"Left" Mask')
    ax1.set_ylabel('Distance (km)')
    
    ax2.pcolormesh(x_ax, y_ax, s2, cmap=cm)
    ax2.set_title('"Center" Mask')
    
    ax3.pcolormesh(x_ax, y_ax, s3, cmap=cm)
    ax3.set_title('"Right" Mask')
    ax3.set_xlabel('Distance (km)')
    ax3.set_ylabel('Distance (km)')
    
    ax4.pcolormesh(x_ax, y_ax, s4, cmap=cm)
    ax4.set_title('"Diagonal" Mask')
    ax4.set_xlabel('Distance (km)')
    
    fig.savefig('swath_masks.png', dpi=400)
    
    np.savetxt('/home/tim/DataSimulation/Data/swath_mask_left', s1)
    np.savetxt('/home/tim/DataSimulation/Data/swath_mask_middle', s2)
    np.savetxt('/home/tim/DataSimulation/Data/swath_mask_right', s3)
    np.savetxt('/home/tim/DataSimulation/Data/swath_mask_diag', s4)
    
if __name__ == '__main__':
    main()