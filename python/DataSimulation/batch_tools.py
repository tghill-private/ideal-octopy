#!/usr/bin/env python
"""
Script for running data simulation experiment with different
parameters and repeating runs
"""

import numpy as np
from matplotlib import pyplot as plt

import data_simulation
import boxplot
import biases

header = 'Simulated Emissions,2x2 km,4x4 km,7x7 km,10x10 km\n'
emissions_labels = boxplot.emissions_labels

repeats = 2

def _parse_results_array(results):
    """Turns the results from one run into a csv-writeable string"""
    rows = ''
    for i,row in enumerate(results):
        results_str = ','.join([str(float(e)) for e in row])
        rows+=(','.join([emissions_labels[i], results_str])+'\n')
    return rows

def analyze(repeats, fname, boxplot_name, plumeplot_name, **kwargs):
    """Writes results, makes boxplot, and makes simulation plot.
    
    Repeats the experiment 'repeats' times, making a simulation
    plot for only the first run. Makes a boxplot for the emission
    results. Saves data to a csv for later use.
    """
    data = []
    with open(fname,'w') as output:
        output.write(header)
        for x in range(repeats):
            r = data_simulation.sim(plumeplot_name, **kwargs)
            plumeplot_name='' # only plot the first time
            
            parsed = _parse_results_array(r)
            output.write(parsed)
            
            dataset = np.insert(r, 0, emissions_labels, axis=1)
            data.extend(dataset)
    data = np.array(data)
    boxplot.boxplot(data, boxplot_name)
    
def batch_process(repeats, names, biases, fmt='png'):
    """Runs different biases multiple times to get results.
    
    repeats is an int indicating how many times to repeat.
    names is a list of the names to save the csv files as
    biases is a list of dictionaries giving keyword arguments
        to control what biases to use
    fmt is the file format to use for the figures
    """
    for (name, bias) in zip(names, biases):
        boxplot_name = name.replace('csv',fmt)
        plumeplot_name = boxplot_name[:-4] + '_sim' + boxplot_name[-4:]
        # plumeplot_name = plumeplot_name.replace(fmt, 'png')
        print 'Saving results table as', name
        print 'Saving boxplot as', boxplot_name
        print 'Saving plume sim plot as', plumeplot_name
        analyze(repeats, name, boxplot_name, plumeplot_name, **bias)
        
if __name__ == '__main__':
    batch_process(repeats, ['eps_test.csv'], [biases.no_bias_constant], fmt='eps')