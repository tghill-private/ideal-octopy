#!/usr/bin/env python
"""
seasonal.py derives weekly emission scale factors from US EPA data

It uses three years of US EPA daily emissions data for 29 plants
for a sample size of 87 plant-years
"""

import numpy as np
from matplotlib import pyplot as plt
import matplotlib as mpl

from etools import emissions
from etools import Units

mpl.rcParams['mathtext.default'] = 'regular'

week_length = 52.

def weekly(sources):
    all_weeks = np.array([])
    all_emissions = np.array([])
    
    for source in sources:
        print 'Reading', source, 'emissions'
        emi = emissions.emissions(source)
        all_weeks = np.append(all_weeks, emi.weeks)
        avg = np.mean(emi.emissions.astype(float))
        all = emi.emissions.astype(float)
        all_emissions = np.append(all_emissions, all/avg)
    
    sort_indices = np.argsort(all_weeks)
    
    sorted_weeks = all_weeks[sort_indices]
    sorted_emissions = all_emissions[sort_indices]
    
    boxplot_emissions = []
    err_bars = []
    factors = np.array([], dtype=float)
    for wk in np.unique(sorted_weeks):
        slice = sorted_weeks==wk
        weekly_emissions = sorted_emissions[slice]
        avg_emissions = np.mean(weekly_emissions)
        factors = np.append(factors, avg_emissions)
        boxplot_emissions.append(weekly_emissions)
        err_bars.append(np.std(weekly_emissions, ddof=1))
    
    boxplot_emissions = np.array(boxplot_emissions)
    err_bars = np.array(err_bars)
    renorm_factor = week_length/np.sum(factors)
    factors = factors*renorm_factor
    
    # with open('factors.txt', 'w') as output:
        # output.write('\n'.join([str(f) for f in factors]))
    
    fig, ax = plt.subplots()
    
    # ax.boxplot(boxplot_emissions)
    # ax.plot(factors)
    ebars = ax.errorbar(np.linspace(0,week_length,week_length+1), factors,
                yerr=err_bars, color='b', ecolor = 'grey')
    ebars[-1][0].set_linestyle('-')
    ax.set_xlabel('Week of year')
    ax.set_ylabel('Emission scale factors')
    ax.set_ylim(0., 2.)
    ax.set_xlim(0-1, week_length+1)
    ax.set_xticks(np.arange(0,week_length,4))
    ax.axhline(1.0, color='g', ls='--')
    ax.set_title('Weekly scale factors with 1-$\sigma$ error bars')
    
    fig.savefig('emission_scale_factors_errbar.png', dpi=600)
    
if __name__ == '__main__':
    weekly(['Amos',
            'Baldwin',
            'Belews',
            'Bowen',
            'Bridger',
            'Colstrip',
            'Conemaugh',
            'Crystal',
            'Cumberland',
            'Gavin',
            'Ghent',
            'Gibson',
            'Harrison',
            'Intermountain',
            'Kyger',
            'Labadie',
            'Laramie',
            'Mansfield',
            'Martin',
            'Miller',
            'Monroe',
            'Mountaineer',
            'Navajo',
            'Oak',
            'Paradise',
            'Parish',
            'Rockport',
            'Scherer',
            'Sherburne',
            'Westar'])
    # weekly(['Belews', 'Bowen'])