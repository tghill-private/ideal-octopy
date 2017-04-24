#!/usr/bin/env python
"""
Script for plotting qq-plot of observed quantiles vs. Normal quantiles
"""

import csv
import argparse
import datetime as dt

from matplotlib import pyplot as plt
import numpy as np
import scipy
import scipy.stats as stats

from etools import statstools
from etools import Units
from etools import emissions

units = 'k_t/day'

import numpy as np 
import pylab 

def qq(source, fname, plot_units):
    """Plots a qq-plot of the given source's emissions.
    
    The figure is saved using the file path fname, and
    is plotted using the units given by plot_units.
    """
    data = '/home/tim/EmissionsDatabase/ampd_%s.csv' % source
    fname = fname if fname else 'figures/emissions_qq_%s.png' % source
    source_emissions = emissions.emissions(source, units=plot_units)
    
    # exclude any days where emissions are zero
    E = source_emissions.emissions
    times = source_emissions.times
    
    fig, (ax1, ax2) = plt.subplots(ncols=2, figsize=(8, 4))
    statstools.qqnorm(ax1, E)
    
    ax2.hist(E)
    ax2.set_title('Histogram of Daily Emissions')
    ax2.set_xlabel('Emissions')
    ax2.set_ylabel('Frequency')
    
    plt.subplots_adjust(wspace=0.4)
    
    fig.savefig(fname, dpi=600)
    fig.clf()
    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', help='Source to analyze emissions from')
    parser.add_argument('--units', help='Units to plot emissions in',
                                 default=units)
    parser.add_argument('fname', help='Optional file name to save to',
                                default=None, nargs='?')
    args = parser.parse_args()
    qq(args.source, args.fname, args.units)

if __name__ == '__main__':
    main()
