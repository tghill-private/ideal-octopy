import argparse

import numpy as np
from matplotlib import pyplot as plt

full_array_file = '../Data/albedo_map_full_scale'
discrete_array_file = '../Data/albedo_map'

_full_cmap = 'Spectral_r'
_discrete_cmap = 'Spectral_r'

thresholds = [-0.5, 1.0]

def main():
    full_array = np.loadtxt(full_array_file)
    discrete_array = np.loadtxt(discrete_array_file)
    
    fig, (ax1, ax2) = plt.subplots(ncols=2, figsize=(8,4))
    
    p1 = ax1.imshow(full_array, origin='lower', cmap=_full_cmap, vmin=-1.5, vmax=1.5)
    p2 = ax2.imshow(discrete_array, origin='lower', cmap=_discrete_cmap, vmin=0, vmax=2)
    
    cbar1 = fig.colorbar(p1, ax=ax1, orientation='vertical', fraction=0.046, pad=0.04)
    
    ax1.contour(full_array, thresholds, colors='k', linestyles='-')
    
    ax1.set_title('Full Dynamic Range')
    ax2.set_title('Discrete')
    
    fig.suptitle('Simulated Albedo Bias')
    fig.subplots_adjust(wspace=0.5, right=0.9)
    fig.savefig('albedo_plots.png', dpi=600, bbox_inches='tight')
    
if __name__ == '__main__':
    main()