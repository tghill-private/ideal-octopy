#!/usr/bin/env python
"""
This is the main script for estimating standard deviation of yearly emissions.

This script uses the derived scale factors to remove the seasonal cycle,
and estimates the standard deviation of yearly emissions. Using this
standard deviation, we can easily estimate sample sizes or uncertainties
"""

import os

import numpy as np
from matplotlib import pyplot as plt
from scipy import stats
from etools import emissions
from etools import smoothing
from etools import statstools
from etools import weeklyfactors


_leg_prop = {   'size':10,
            }
            
p = 0.95

est_err = 0.15

total_std = lambda x: np.sqrt(x**2 + est_err**2)

def fit(sources, fname, units = 'k_t/day', window=31, order=3):
    Y = np.array([])
    X = np.array([])
    weeks = np.array([])
    for source in sources:
        obs_emissions = emissions.emissions(source)
        X = np.append(X, obs_emissions.times)
        mean_emissions = np.mean(obs_emissions.emissions)
        Y = np.append(Y, obs_emissions.emissions/mean_emissions)
        weeks = np.append(weeks, obs_emissions.weeks)
    
    sort_indices = np.argsort(X)
    Y = Y[sort_indices].astype(float)
    X = X[sort_indices]
    weeks = weeks[sort_indices].astype(int)
    
    scale_factors = weeklyfactors.factors[weeks]
    residuals = Y/scale_factors - 1
    
    regr = stats.linregress(X, residuals)
    
    print 'Regression on (X, residuals):'
    print regr
    slope, intcpt, r, _, _= regr
    fit_regr = intcpt + X*slope
    
    fig1, (a1, a2) = plt.subplots(ncols=2, figsize=(8,4))
    a1.plot(X, Y, ls='', marker='.', markersize=1, color='b')
    a1.plot(X, scale_factors, ls='-', marker='', color='r', label='Scale factors')
    a1.legend(prop=_leg_prop)
    a1.set_title('Data with fitted response')
    
    a2.set_title('Residuals')
    a2.plot(X, residuals, ls='', marker='.', markersize=1, color='b')
    a2.plot(X, fit_regr, color='g')
    a2.axhline(color='k')
    a2.text(0.05, 0.995, '$y = {:.3e} {:+.3e}x$'.format(intcpt, slope),
                transform = a2.transAxes, verticalalignment='top')
    a1.set_ylabel('Emissions (%s)' % units)
    fig1.savefig(fname, dpi=500)
    fig1.clf()
    
    # compare original and baseline-fit qq-plots
    qqfname = '_qq'.join(os.path.splitext(fname))
    fig3, (c1, c2, c3) = plt.subplots(ncols=3, figsize=(12,4))
    statstools.qqnorm(c1, Y - 1)
    statstools.qqnorm(c2, residuals)
    statstools.qqnorm(c3, residuals - fit_regr)
    c1.set_title('Raw emissions')
    c2.set_title('Fitted response')
    c3.set_title('Removed regression line')
    
    fig3.suptitle('Raw and de-seasonalized qqplots', fontsize=14)
    fig3.subplots_adjust(wspace=0.4, top=0.85)
    fig3.savefig(qqfname, dpi=500)
    fig3.clf()
    
    std = np.std(Y, ddof=1)
    response_std = np.std(residuals, ddof=1)
    sample_std = total_std(std)
    response_sample_std = total_std(response_std)
    regr_std = total_std(np.std(residuals - fit_regr, ddof=1))
    n = len(X)
    
    a = stats.chi2.ppf((1-p)/2., n-1)
    b = stats.chi2.ppf((1+p)/2., n-1)
    
    lower = lambda x: np.sqrt( (n-1)*(x**2)/b )
    upper = lambda x: np.sqrt( (n-1)*(x**2)/a )
    
    stds = (sample_std, response_sample_std, regr_std)
    
    print '\nSample Standard Deviation:', stds[0], lower(stds[0]), upper(stds[0])
    print 'After removing seasonal cycle:', stds[1], lower(stds[1]), upper(stds[1])
    print 'After removing regression line:', stds[2], lower(stds[2]), upper(stds[2])
    
    
if __name__ == '__main__':
    srcs = ['Amos',
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
            'Westar']
    # srcs = ['Westar']
    fit(srcs, 'global_mean_scalefactors.png')
