"""
Module providing additional stats functionality to python.

First made to make qqplots.
"""

from matplotlib import pyplot as plt
import matplotlib as mpl
import numpy as np
from scipy import stats

from namespace import Namespace

mpl.rcParams['mathtext.default'] = 'regular'

qqdefaults = Namespace(
quantiles = (25, 75),

s = 8,
linewidths = 0.5,

line_colour = 'r',

xlim = None,
ylim = None,

xlabel = 'Normal Quantiles',
ylabel = 'Observed Quantiles',
title = 'Observed-Normal QQ-Plot',

grid = False,

)

def qqnorm(ax, dataset, **kwargs):
    """Plots a quantile-quantile plot for dataset against N(0,1) quantiles.
    
    Calculates the observed quantiles for dataset, and plots these against
    theoretical quantiles calculated for a N(0, 1) distribution.
    
    Plots a straight line through the data, using the fixed points of
    the 25% and 75% quantiles of the observed data and the
    theoretical Normal distribution.
    
    qqplots are expected to be straight if the observed data fits the chosen
    theoretical distribution. There is deviation expected at the end points.
    
    The p-value for the hypothesis H0: The data follows a Normal distribution
    is calcualted using the scipy.stats.kstest implementation of the
    Kolmogorov Smirnov test
        (https://en.wikipedia.org/wiki/Kolmogorov-Smirnov_test)
    
    The p-value is added on to the qq-plot.
    
    Args:
        * ax: a matplotlib Axes instance to plot on to
        * dataset: a 1D numpy.ndarray with observed data for
                    1 continuous variable
        * matplotlib.pyplot keyword arguments for scatter and line plots
    
    Effects:
        * plots a qq-plot comparing observed to theoretical N(0,1)
            quantiles onto the axis ax. Calculates the p-value for
            H0: The data follows a Normal distribution. Uses the
            
    """
    params = qqdefaults
    params.update(**kwargs)

    
    obs_quantiles = stats.rankdata(dataset)/float(len(dataset))
    
    theoretical = np.array([stats.norm.ppf(q) for q in obs_quantiles])
    mask = np.logical_and(theoretical!=np.inf, theoretical!=-np.inf)
    
    obs_qauntiles = obs_quantiles[mask]
    dataset = dataset[mask]
    theoretical = theoretical[mask]
    # calculate 25% and 75% percentiles to fit line
    obs_lower, obs_upper = np.percentile(dataset, params.quantiles)
    
    norm_quantiles = (params.quantiles[0]/100., params.quantiles[1]/100.)
    norm_lower, norm_upper = stats.norm.ppf(norm_quantiles)
    
    slope = (obs_upper - obs_lower)/(norm_upper - norm_lower)
    intercept = obs_lower - slope*norm_lower
    
    print 'Fitted line:', 'y = %s*x + %s' % (slope, intercept)
    
    r, p = stats.pearsonr(dataset, theoretical)
    print r
    print np.std(dataset)
    print np.std(theoretical)
    
    ax.scatter(theoretical, dataset, s=params.s, linewidths=params.linewidths)
    ax.plot(theoretical, slope*theoretical + intercept, color=params.line_colour)
    ax.text(0.05, 0.95, 'r$^2$: {:.4f}'.format(r*r), transform=ax.transAxes)
    ax.set_xlabel(params.xlabel)
    ax.set_ylabel(params.ylabel)
    ax.set_title(params.title)
    
    if params.xlim:
        ax.set_xlim(params.xlim)
    if params.ylim:
        ax.set_ylim(params.ylim)
        
    ax.grid(params.grid)
    
    return ax