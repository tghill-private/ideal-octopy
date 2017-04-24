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

from etools import smoothing
from etools import emissions

units = 'k_t/day'

ls = '-'
marker = '.'
colour = 'b'

xlabel = 'Days from 2014-01-01'
ylabel = 'Emissions (%s)'
title = 'Emissions Timeseries'


import numpy as np 
import pylab 

def timeseries(source, fname, plot_units, window=31, order=3):
    """Plots a yearly time series given a datafile data.
    
    data should be a ampd csv with data from
    only one source in it
    """
    daily_emissions = {}
    data = '/home/tim/EmissionsDatabase/ampd_%s.csv' % source
    fname = fname if fname else 'figures/timeseries_%s.png' % source
    print 'Opening emissions file', data
    obs_emissions = emissions.emissions(source)
    
    src_emissions = obs_emissions.emissions
    times = obs_emissions.times
    
    kw = dict(  ls=ls,
                color=colour,
                marker=marker,
            )
    
    fig, axes = plt.subplots()
    axes.plot(times, src_emissions, ls='', color=colour, marker=marker)
    axes.set_ylabel('Emissions (Kt/day)')
    axes.set_xlabel(xlabel)
    
    fig.suptitle('%s Emissions' % source)
    plt.subplots_adjust(hspace=0.05, top=0.95)
    fig.savefig(fname, dpi=600)
    print 'Saved timeseries as', fname
    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', help='Source to analyze emissions from')
    parser.add_argument('--units', help='Units to plot emissions in',
                                 default=units)
    parser.add_argument('fname', help='Optional file name to save to',
                                default=None, nargs='?')
    args = parser.parse_args()
    timeseries(args.source, args.fname, args.units)

if __name__ == '__main__':
    main()