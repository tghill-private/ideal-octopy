"""
Module Emissions.py

This module reads daily and hourly emissions from the data
downloaded from https://ampd.epa.gov/ampd/

The data is stored in the directory "/home/tim/EmissionsDatabase/"
in CSV format, with one file for each plant.

This module reads these emissions CSV files, and
returns the emissions for a specific location and time.
"""

import datetime as dt
import re
import csv
import os

import Units
from Units import SciVal
import TIMES
import data


## Overall constants
date_header = 'Date'
hour_header = 'Hour'
unit_header = 'Unit ID'
co2_header = 'CO2 (short tons)'

hourly_date_header = 'OP_DATE'
hourly_hour_header = 'OP_HOUR'
hourly_unit_header = 'UNITID'
hourly_co2_header = 'CO2_MASS (tons)' # actually short tons

## Constants for daily emissions
database_units = 'st/day'

# some files are '%d/%m/%Y' and some are '%Y-%m-%d'
#  because of excel formatting the CSVs. Check which
#  format with these regular expressions to parse
#  the time with the right format
slash_re = re.compile('^[0-9]{2}[/][0-9]{2}[/][0-9]{4}$')
slash_timefmt = '%d/%m/%Y'
hyphen_re = re.compile('^[0-9]{4}[-][0-9]{2}[-][0-9]{2}$')
hyphen_timefmt = '%Y-%m-%d'

us_hyphen_re = re.compile('^[0-9]{2}[-][0-9]{2}[-][0-9]{4}$')
us_hyphen_timefmt = '%m-%d-%Y'

date_key_fmt = hyphen_timefmt
daily_database_file_fmt = os.path.join(data.daily_emissions, '%s.csv')


## Constants for hourly emissions
hourly_database_units = 'st/hr'
slash_hourly_re = re.compile('^[0-9]{2}[/][0-9]{2}[/][0-9]{4}[-][0-2][0-9]$')
slash_hourly_timefmt = '%d/%m/%Y-%H'

hyphen_hourly_re = re.compile('^[0-9]{4}[-][0-9]{2}[-][0-9]{2}[-][0-2][0-9]$')
hyphen_hourly_timefmt = '%Y-%m-%d-%H'

us_hyphen_hourly_re = re.compile('^[0-9]{2}[-][0-9]{2}[-][0-9]{4}[-][0-2][0-9]$')
us_hyphen_hourly_timefmt = '%m-%d-%Y-%H'

date_hour_key_fmt = hyphen_timefmt + "-%H"
hourly_database_file_fmt = os.path.join(data.hourly_emissions, '%s.csv')
hourly_database_datefmt = "%Y%m%d"



def get_daily_emissions(time, units=Units._model_units, temporal_factors=False):
    """Returns the EPA daily reported CO2 emissions data.
    
    Uses the EPA data downloaded to /home/tim/EmissionsDatabase in csv
    form, and returns the daily emissions on the day indicated by time.
    Multiplies by TIMES temporal factors if temporal_factors is True.
    
    Args:
        time: a PST.Time instance or subclass of, or
              string formatted as '%Y-%m-%d'
        units: a string corresponding to valid units according to the Units module
               (default 'g/s')
        temporal_factors: a bool controlling whether or not to multiply
            by the TIMES daily and weekly scale factors (default False)
    
    Returns:
        A SciVal instance with the specified units (default 'g/s')
        corresponding to that days emissions as reported by EPA
    
    Raises:
        IOError if the required file does not exist (ie, not USA source)
        ValueError if an incorrect date format is specified
        TypeError if an invalid type is passed as time
    """
    if isinstance(time, dt.datetime):
        key = time.strftime(date_key_fmt)
    
    elif type(date)!=str:
        raise TypeError("'date' must be a datetime object or a string formatted matching '%Y-%m-%d'")
    
    elif not hyphen_re.match(date):
        raise ValueError("'date' does not match '%Y-%m-%d format'")
    
    else:
        key = time
    
    all_emissions = {}
    csv_name = daily_database_file_fmt % ('ampd_'+time.short)
    with open(csv_name, 'r') as data:
        emissions_reader = csv.reader(data, delimiter=',')
        headers = [s.strip() for s in next(emissions_reader)]
        date_col= headers.index(hourly_date_header)
        unit_col = headers.index(hourly_unit_header)
        co2_col = headers.index(hourly_co2_header)
        
        for row in emissions_reader:
            if row==[]:
                pass
            else:
                date = row[date_col]
                unit = row[unit_col]
                raw_co2 = row[co2_col]
                co2 = SciVal(0, database_units) if raw_co2=="" else SciVal(float(raw_co2), database_units)
                if slash_re.match(date):
                    day = dt.datetime.strptime(date, slash_timefmt)
                elif hyphen_re.match(date):
                    day = dt.datetime.strptime(date, hyphen_timefmt)
                elif us_hyphen_re.match(date):
                    day = dt.datetime.strptime(date, us_hyphen_timefmt)
                else:
                    raise ValueError("Format: %s" % date)
                date_key = day.strftime(date_key_fmt)
                if date_key in all_emissions:
                    all_emissions[date_key]+=co2
                else:
                    all_emissions[date_key] = co2
    if temporal_factors:
        daily, weekly = TIMES.Factors(time)
        factor = daily*weekly
    else:
        factor = 1.
    
    return all_emissions[key](units)*factor
        

def get_hourly_emissions(time, units=Units._model_units, temporal_factors=False, file=None):
    """Returns the EPA hourly reported CO2 emissions data.
    
    Uses the EPA data downloaded to /home/tim/EmissionsDatabase in csv
    form, and returns the hourly emissions for time indicated by time.
    Multiplies by TIMES temporal factors if temporal_factors is True.
    
    Args:
        time: a PST.Time instance or subclass of, or
              string formatted as '%Y-%m-%d-%H'
        units: a string corresponding to valid units according to the Units module
               (default 'g/s')
        temporal_factors: a bool controlling whether or not to multiply
            by the TIMES daily and weekly scale factors (default False)
    
    Returns:
        A SciVal instance with the specified units (default 'g/s')
        corresponding to the hourly emissions as reported by EPA
    
    Raises:
        IOError if the required file does not exist (ie, not USA source)
        ValueError if an incorrect date format is specified
        TypeError if an invalid type is passed as time
    """
    if isinstance(time, dt.datetime):
        time_key = time.strftime(date_hour_key_fmt)
    elif type(time)!=str:
        raise TypeError("'date' must be a datetime instance or a formatted string")
    elif not hyphen_hourly_re.match(time):
        raise ValueError("'date' '%s' does not match '%Y-%m-%d-%H format'" % time)
    else:
        time_key = time
    
    if file:
        csv_name = file
    else:
        csv_name = hourly_database_file_fmt % (''.join(['ampd_', time.short, time.strftime(hourly_database_datefmt)]))
    
    all_emissions = {}
    with open(csv_name,'r') as data:
        emissions_reader = csv.reader(data, delimiter=',')
        headers = [s.strip() for s in next(emissions_reader)]
        date_col= headers.index(hourly_date_header)
        hour_col= headers.index(hourly_hour_header)
        unit_col = headers.index(hourly_unit_header)
        co2_col = headers.index(hourly_co2_header)
        
        for row in emissions_reader:
            if row==[]:
                pass
            else:
                date = row[date_col]
                hour = int(row[hour_col])
                date = date + '-%.2d' % hour
                if slash_hourly_re.match(date):
                    day = dt.datetime.strptime(date, slash_hourly_timefmt)
                elif hyphen_hourly_re.match(date):
                    day = dt.datetime.strptime(date, hyphen_hourly_timefmt)
                elif us_hyphen_hourly_re.match(date):
                    day = dt.datetime.strptime(date, us_hyphen_hourly_timefmt)
                else:
                    raise ValueError("Format: %s" % date)
                
                date_key = day.strftime(date_hour_key_fmt)
                hour = int(row[hour_col])
                unit = row[unit_col]
                raw_co2 = row[co2_col]
                co2 = 0 if raw_co2=="" else float(raw_co2)
                co2 = Units.SciVal(co2, hourly_database_units)
                
                key = day.strftime(date_hour_key_fmt)
                if key in all_emissions:
                    all_emissions[key]+=co2
                else:
                    all_emissions[key] = co2
            
    if temporal_factors:
        daily, weekly = TIMES.Factors(time)
        factor = daily*weekly
    else:
        factor = 1.
    return all_emissions[time_key](units)*factor
    
if __name__ == "__main__":
    from Overpasses import *
    print get_daily_emissions(Gavin20150730)
    print get_daily_emissions(Belews20150621)
