#!/usr/bin/env python
"""
Script for plotting all estimated emissions as a 
scatter plot/box plot for all biases
"""

import csv

import numpy as np
import scipy.stats
from matplotlib import pyplot as plt

import boxplot

resolutions = ['full', '2x2', '4x4', '7x7', '10x10']

colours = ['b', 'g']
labels = ['Albedo', 'Noise']

def analyze(files):
    tab = ' '*Dataset.spacing
    data = []
    for file in files:
        with open(file, 'r') as results:
            reader = csv.reader(results)
            header = next(reader)
            results = [row for row in reader]
        data.extend(results)
    data = np.array(data)
    print data.shape
    
    boxplot.boxplot(data, 'all_boxplot.png')
    
    sim_emissions = np.unique(data[:,0])
    results = {F:None for F in sim_emissions}
    for F in results.keys():
        results[F]={resolutions[col]:data[:,col][data[:,0]==F] for col in range(1, 5)}
    
    sorted_emissions = sorted(sim_emissions, key=lambda i: int(i))
    for sim_emi in sorted_emissions:
        print '%s Mt/yr Simulated Source' % sim_emi
        print tab, Dataset.header
        val = results[sim_emi]
        for res in resolutions[1:]:
            elist = val[res]
            d = Dataset(elist)
            print str(res).ljust(Dataset.spacing), d.display()
        print ''
            
class Dataset(object):
    """Calculates statistical numerical measures of center, spread of data.
    
    Class Attributes:
     * spacing=8: column width in pretty output
     * headers: Header titles for pretty output
     * header: joined, spaced headers to print
    
    Instance Attributes:
    """
    spacing = 8
    headers = ['mean', 'sd', 'min', 'q lower', 'median', 'q upper', 'max']
    header= ''.join([h.ljust(spacing) for h in headers])
    def __init__(self, collection):
        data = np.array(collection.astype(float))
        self.data = data
        if collection.ndim!=1:
            raise TypeError('Dataset must consume a 1-D iterable')
        
        median = np.median(data)
        lower_quartile = scipy.stats.scoreatpercentile(data, 25)
        upper_quartile = scipy.stats.scoreatpercentile(data, 75)
        
        self.min = np.min(data)
        self.max = np.max(data)
        self.median = median
        self.lower_quartile = lower_quartile
        self.upper_quartile = upper_quartile
        
        self.std = np.std(data)
        self.mean = np.mean(data)
        
        self.header = Dataset.header
    
    def __repr__(self):
        return 'Dataset(%s)' % self.data.__repr__()
    
    def __str__(self):
        return '<Dataset(%s) % self.data.__str__()>' % self.data.__str__()
    
    def display(self):
        summary = [self.mean, self.std, self.min, self.lower_quartile,
                    self.median, self.upper_quartile, self.max]
        return ''.join([('%.3f'%x).ljust(Dataset.spacing) for x in summary])


if __name__ == '__main__':
    analyze(['../results_30_repeats/tables/albedo.csv',
            '../results_30_repeats/tables/cloudmask.csv',
            '../results_30_repeats/tables/footprint.csv',
            '../results_30_repeats/tables/interference.csv',
            '../results_30_repeats/tables/topography.csv',
            '../results_30_repeats/tables/wind_bias.csv',
            '../results_30_repeats/tables/defaults.csv',
            '../results_30_repeats/tables/stability_bias.csv'])