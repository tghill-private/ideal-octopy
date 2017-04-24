#!/usr/bin/env python
"""
HourlyEmissionsPlot.py

Creates a time-series plot for hourly emisisons before and after an Overpass.

Uses the AMPD to get hourly emissions for 36 hours before and 12 hours
after an overpass. It creates a time series plot for the emissions,
indicating the daily average emissions (the emissions used for the model).

Plots can only be made for the few overpasses that we have hourly
emissions data downloaded for.


Usage (Command-Line Interface):
./HourlyEmissionsPlot.py overpass file_name [--units]

Args:
    overpass: name of an overpass to use (eg. Gavin20150730)
    file_name: file name to save the plot as (eg. HourlyEmissions.png)
    units: default 'k_t/day': units to use for emissions on plot
"""

import datetime as dt
from matplotlib import pyplot as plt
import matplotlib as mpl
import argparse
import os

import Emissions
import Overpasses
import Formats

# set mathtext font to be the same as regular font
mpl.rcParams['mathtext.default'] = 'regular'

## Constants:
hours_before = 36
hours_after = 12

legend_prop = {'size':8}

units_display = {'k_t/day':'Kt CO$_2$/day',
                 'K_t/day':'Kt CO$_2$/day',
                 'M_t/yr' :'Mt CO$_2$/year',
                 'g/s'    :'g CO$_2$/s' }

def total_time_between(t1, t2):
    """Returns the total time in hours from t1 to t2.
    
    If t2 is greater than t1, returns negative. In
    other words, t2 is the 'reference' event
    to compare t1 to.
    """
    seconds = (t1-t2).total_seconds()
    return seconds/3600.

def plot(time, fig_name, units='k_t/day'):
    """Creates the hourly emissions plot for Time time.
    
    Args:
        time: a Time instance
        fig_name: file name to save the plot as
        units ['k_t/day']: units to show emissions in
    """
    floor_time = time + dt.timedelta(minutes=-time.minute)
    
    print "Getting daily emissions"
    daily_emissions = time.source.get_emissions(time)(units)
    
    hours = range(-hours_before, hours_after+2)
    time_deltas = [dt.timedelta(hours=hr) for hr in hours]
    times = [(floor_time + td) for td in time_deltas]
    
    fname = Emissions.hourly_database_file_fmt % (''.join(['ampd_',time.short, time.strftime(Emissions.hourly_database_datefmt)]))
    
    print "Getting hourly emissions"
    try:
        emissions = [Emissions.get_hourly_emissions(t, units=units, file=fname) for t in times]
    except IOError:
        print t
        # raise IOError("No daily emissions file for %s" % time)
        raise
    
    x_ax = [total_time_between(measurement_time, time) for measurement_time in times]
    
    print "Creating plot"
    plot_title = "Hourly Emissions For %s" % time
    fig, ax = plt.subplots(figsize=(8,5))
    
    if units in units_display:
        units_label = units_display[units]
    else:
        units_label = units
    
    ax.set_xlabel("Time from Overpass (hours)", fontname=Formats.globalfont)
    ax.set_ylabel("Emissions (%s)" % units_label, fontname=Formats.globalfont)
    ax.set_xlim(-37,13)

    ax.plot(x_ax, emissions, marker=".", label="Hourly Reported Emissions")
    ax.axvline(0., color='g') # label="Overpass Time"
    ax.axhline(daily_emissions, color='k', ls='--', label="Daily Reported Emissions")
    # ax.legend(prop=legend_prop)
    
    ymin, ymax = ax.get_ylim()
    ax.set_ylim(0,ymax)
    fig.suptitle(plot_title, fontname=Formats.globalfont)
    
    dir = os.path.dirname(os.path.realpath(fig_name))
    if not os.path.exists(dir):
        print "Directory '%s' does not exists" % dir
        try:
            os.mkdir(dir)
            print "Made directory '%s'" % dir
        except:
            print "Could not make directory '%s'"
            fig_name = os.path.split(fig_name)[1]
    plt.savefig(fig_name, dpi=600)
    print "Plot saved as", fig_name

def main():
    """Parses command line arguments and creates plot.
    
    CLI arguments are overpass, file_name, and --units (optional).
    Attempts to make save directory if the directory doesn't exist.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('overpass', help='which overpass to plot emissions for')
    parser.add_argument('file_name', help='File to save plot as')
    parser.add_argument('-u', '--units', default='k_t/day', help='Units')
    args = parser.parse_args()
    
    try:
        overpass = getattr(Overpasses, args.overpass)
    except AttributeError:
        raise AttributeError('Overpass "%s" does not exist' % args.overpass)
    
    return plot(overpass, args.file_name, args.units)

if __name__ == "__main__":
    main()