"""
Module fits a sine curve to noisy emissions data.

Using the scipy.optimize.leastsq function, it assumes
a yearly period and fits for the amplitude, phase
shift, and mean of a sine curve. It needs
prior estimates and refines these estimates.
"""

import numpy as np
from scipy import optimize
from matplotlib import pyplot as plt

def fit_sine(x, y, priors, fname, plot=True):
    a, phase, mean = priors
    w = 2*np.pi/365.
    optimize_func = lambda v: v[0]*np.sin(w*(x + v[1])) + v[2] - y
    
    plot_func = lambda v: v[0]*np.sin(w*(x + v[1])) + v[2]
    
    fitted = optimize.leastsq(optimize_func, priors)
    
    if plot:
        fig, ax = plt.subplots()
        ax.set_xlabel('Time')
        ax.set_ylabel('Emissions')
        
        ax.plot(x, y, ls='', marker='.', color='b')
        
        ax.plot(x, plot_func(priors), ls='-', marker=' ', color='r',
                                    label='Prior estimate')
        ax.plot(x, plot_func(fitted[0]), ls='-', marker='', color='g', 
                                    label='Fitted estimate')
        ax.legend()
        
        fig.savefig(fname, dpi=600)
        fig.clf()
    
    return (fitted, (plot_func(priors), plot_func(fitted[0])))

if __name__ == '__main__':
    # Test to prove this works
    X = np.arange(0, 3*366.)
    Y = np.sin((2*np.pi/365.)*X) + np.random.normal(0, 5, X.shape) + 12
    priors = (Y.std(ddof=1), 90, Y.mean())
    results = fit_sine(X, Y, priors, '../CurveFitDemo.png')
    print "Priors:", priors
    print "Fitted:", results[0]