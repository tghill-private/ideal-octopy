#!/usr/bin/env python
"""
Module simulates a footprint bias for simulated data
"""

import numpy as np
from matplotlib import pyplot as plt

titlefont = 12
subtitlefont = 10
ticklabelfont = 8

def biased_array(shape, strength=1., rstrength=0.4):
    nrows, ncols = shape
    
    col_biases = np.linspace(-strength, strength, ncols)
    col_noise = 2*(np.random.random((ncols,))-0.5)*rstrength*strength
    col_biases+=col_noise
    
    row_biases = np.linspace(-strength, strength, nrows)
    row_noise = 2*(np.random.random((nrows,))-0.5)*rstrength*strength
    row_biases+=row_noise
    
    col_bias_factors, row_bias_factors = np.meshgrid(col_biases, row_biases)
    
    np.savetxt('/home/tim/DataSimulation/Data/column_bias', col_bias_factors)
    np.savetxt('/home/tim/DataSimulation/Data/row_bias', row_bias_factors)
    return row_bias_factors, col_bias_factors
    
def plot_biased_arrays(rbias, cbias, cm='RdYlBu_r'):
    fig, (ax1, ax2) = plt.subplots(ncols=2)
    fig.suptitle('Simulated Row and Column Footprint Biases', fontsize=titlefont)
    ax1.set_title('Column Biases', fontsize=subtitlefont)
    ax2.set_title('Row Biases', fontsize=subtitlefont)
    ax1.tick_params(labelsize=ticklabelfont)
    ax2.tick_params(labelsize=ticklabelfont)
    cax = fig.add_axes([0.2,0.1,0.6,0.05])
    vmin, vmax = -1.5, 1.5
    cbar_ticks = np.linspace(vmin, vmax, 7)
    cbar_ticks_str = ['%.2f' % f for f in cbar_ticks]
    im1 = ax1.pcolormesh(cbias, vmin=vmin, vmax=vmax, cmap=cm)
    im2 = ax2.pcolormesh(rbias, vmin=vmin, vmax=vmax, cmap=cm)
    plt.subplots_adjust(bottom=0.2, top=0.9)
    cbar = fig.colorbar(im1, cax=cax, orientation='horizontal', ticks=cbar_ticks)
    cbar.ax.tick_params(labelsize=ticklabelfont)
    cbar.ax.set_xticklabels(cbar_ticks_str)
    
    cax_x1 = (-1.-vmin)/(vmax-vmin)
    cax_x2 = (1.-vmin)/(vmax-vmin)
    
    cbar.ax.plot([cax_x1, cax_x1],[0.,1.], ls='-', color='k', lw=1)
    cbar.ax.plot([cax_x2, cax_x2],[0.,1.], ls='-', color='k', lw=1)
    fig.savefig('footprint_biases', dpi=400)
    
    
if __name__ == '__main__':
    r, c = biased_array((1200,1200))
    plot_biased_arrays(r, c)