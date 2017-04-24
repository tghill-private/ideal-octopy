"""
Module emissions for reading emissions from the emissions database.

Class emissions reads the emissions using the default units.
"""

import numpy as np
import csv
import datetime as dt

co2_header = 'CO2_MASS (tons)'
date_header = 'OP_DATE'

db_units = 'st/day'
db_fmt = '%m-%d-%Y'

import Units

class emissions(object):
    """Reads daily emissions data for a given source.
    
    Attributes:
    * emissions: 1D array of emissions in kt/day
    * times: 1D array of times, in hours since 2014-01-01
    """
    default_units = 'k_t/day'
    
    def __init__(self, source, units = default_units):
        """Plots a yearly time series given a datafile data.
        
        data should be a ampd csv with data from
        only one source in it
        """
        self.units = units
        self.source = source
        
        daily_emissions = {}
        data = '/home/tim/EmissionsDatabase/ampd_%s.csv' % source
        with open(data, 'r') as input:
            reader = csv.reader(input)
            header = next(reader)
            header = np.array([s.strip().strip('\n') for s in header])
            for row in reader:
                row = np.array(row)
                time = row[header==date_header][0]
                F = row[header==co2_header][0]
                if F == '':
                    F = 0.
                else:
                    F = float(F)
                F = Units.SciVal(F, db_units)(units)
                if time in daily_emissions:
                    daily_emissions[time] += F
                else:
                    daily_emissions[time] = F
        
        days = np.array([])
        emissions = np.array([])
        weeks = np.array([])
        
        # convert times to a list of days from the beginning of the file
        t0 = dt.datetime(2014, 1, 1)
        for (t, f) in daily_emissions.iteritems():
            date = dt.datetime.strptime(t, db_fmt)
            t = date - t0
            days = np.append(days, t.days)
            weeks = np.append(weeks, int(int(date.strftime('%j'))//7))
            emissions = np.append(emissions, f)
        
        # sort times, emissions by times
        sort_indices = np.argsort(days)
        
        emissions = emissions[sort_indices]
        weeks = weeks[sort_indices]
        days = days[sort_indices]
        
        # exclude any days where emissions are zero
        slice = emissions>0
        emissions = emissions[slice]
        days = days[slice]
        weeks = weeks[slice]
        
        self.times = days
        self.weeks = weeks
        self.days = days
        self.emissions = emissions.astype(float)