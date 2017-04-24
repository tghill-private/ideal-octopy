#!/usr/bin/env python
"""
Plots a histogram of the simulated enhancements.

This should show how trustworthy the observations
would be. We need something to show how hard it
would be to actually be able to detect the 10x10 km
resolution enhancements
"""

from matplotlib import pyplot as plt
import numpy as np
import argparse

import arrtools
import data_simulation

titles = ['2x2 km$^2$', '4x4 km$^2$', '7x7 km$^2$', '10x10 km$^2$']

def hist_plot(data_file, title, plot_name, noise_strength=1.):
    """Plots a histogram of the simulated emissions from the provided data file"""
    data = np.loadtxt(data_file)
    shape = data.shape
    regrid_factors = [int(2.e3/50.), int(4.e3/50.), int(7.e3//50.), int(10.e3/50.)]
    fig, axes = plt.subplots(nrows=2, ncols=2)
    for i,(ax, factor) in enumerate(zip(axes.flatten(), regrid_factors)):
        averaged = arrtools.average(data, factor)
        reduced = arrtools.reduce(averaged, factor)
        val_min = 0.05
        val_max = 0.05*(max(averaged.flatten()/0.05 + 1))
        histogram = ax.hist(reduced.flatten(), bins=20, range=(val_min,val_max))
        ax.set_xlabel('Simulated Enhancement (ppm)')
        ax.set_ylabel('Observations')
        ax.set_title(titles[i])
    axes = axes.flatten()
    ticks = axes[3].get_xticks()
    axes[3].set_xticks(ticks[::2])
    fig.suptitle(title)
    plt.subplots_adjust(top=0.9, hspace=0.4, wspace=0.25)
    fig.savefig(plot_name, dpi=600)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', help='sim. enhancement file to make histogram for')
    parser.add_argument('title', help='title of plot')
    parser.add_argument('fig_name', help='File name of figure')
    args = parser.parse_args()
    hist_plot(args.file, args.title, args.fig_name)
    
if __name__ == '__main__':
    main()