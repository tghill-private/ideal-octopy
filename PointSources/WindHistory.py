"""
WindHistory.py

Module for plotting the historical (-3 days) and future (+1 day)
wind speed and direction for a given overpass.

Plots both speed and direction as time series on x-y axes
"""

import datetime as dt
import os

from matplotlib import pyplot as plt
from matplotlib import dates
import matplotlib.lines as mlines
from matplotlib.legend_handler import HandlerLine2D
import matplotlib as mpl
import numpy

import Formats
import PST
import ReadWinds

# set mathtext font to be the same as regular font
mpl.rcParams['mathtext.default'] = 'regular'

# constants for getting winds and setting ticks
_hours_back = 18
_hours_forward = 6
_ECMWF_step = 3
_ECMWF_best_step = 6
_MERRA_step = 3
_GEM_step = 6
_round = 3600*_ECMWF_step
_num_x_ticks = 9

# font sizes and tick string formatting
_plot_fmt = dates.DateFormatter("%d-%H")
_labelfont = 10
_ticksize = 8
_title = 10
_maintitle = 12
_adjust_params = {'hspace':0.2, 'top':0.925}
_leg_loc = (0., 1.05, 1., 0.)
_leg_prop = {   'size':10,
                'family':'Free'
            }

_xlabel = 'Hours from Overpass Time'
_ylabel_dir = "Wind direction ($^{\circ}$)"
_ylabel_speed = 'Wind speed (m/s)'

# plot style constants
_marker = '.'
_cap = ''
_time_indicator_colour = 'g'
_time_indicator_lw = 0.5
_direction_colour = 'g'
_ylim = (0,360)
_ecmwf_col = 'r'
_merra_col = 'b'
_gem_col = 'Orange'
_dpi = 500

def dhour(t1, t2):
    """ returns the number of hours from time t1 to time t2 """
    return (t2 - t1).total_seconds()/3600.

def historical(overpass, save_name, ylim=None, grid=False, wind_sources=["MERRA", "ECMWF", "GEM"], steps=False):
    """Plots times series of wind direction and windspeed before and after an overpass.
    
    Gets wind data for 18 hours before and 6 hours after an overpass for
    all wind fields in wind_sources.
    
    Option "steps" will plot MERRA horizontally if True, else will connect
    MERRA wind speed and direction points.
    """
    # absolute times:
    t_min = overpass.time.round(_round) + dt.timedelta(hours=-_hours_back)
    t_max = overpass.time.round(_round) + dt.timedelta(hours=_hours_forward)
    
    # these are the times you open a file for
    best_ecmwf_times = [(t_min + dt.timedelta(hours=x*_ECMWF_best_step)) for x in numpy.arange(float(_hours_back+_hours_forward)/_ECMWF_best_step + 0.1)]
    ecmwf_times = [(t_min + dt.timedelta(hours=x*_ECMWF_step)) for x in numpy.arange(float(_hours_back+_hours_forward)/_ECMWF_step + 1)]
    merra_times = [(t_min + dt.timedelta(hours=(x*_MERRA_step + 1.5))) for x in numpy.arange(float(_hours_back+_hours_forward)/_MERRA_step)]
    gem_times = [(t_min + dt.timedelta(hours=x*_GEM_step)) for x in numpy.arange(float(_hours_back+_hours_forward)/_GEM_step + 1)]
    
    xticks = numpy.linspace(-_hours_back, _hours_forward, _num_x_ticks)
    
    legend_handles = []
    legend_labels = []
    handle_map = {}
    
    fig, (ax1, ax2) = plt.subplots(nrows=2, sharex=True)
    
    if "ECMWF" in wind_sources:
        ecmwf_handle = mlines.Line2D([], [], color=_ecmwf_col,
                                        marker=_marker, label='ECMWF')
        legend_handles.append(ecmwf_handle)
        legend_labels.append('ECMWF')
        # handle_map.update({ecmwf_handle: HandlerLine2D(numpoints=2)})
        try:
            ecmwf_speeds = []
            ecmwf_bearings = []
            ecmwf_x = []
            for time in best_ecmwf_times:
                w = ReadWinds.get_new_ecmwf(time, interp=False, return_stability=False)[0]
                ecmwf_speeds.append(w.speed)
                ecmwf_bearings.append(w.bearing)
                ecmwf_x.append(dhour(overpass.time,time))
        except Exception as exc:
            ecmwf_speeds = []
            ecmwf_bearings = []
            ecmwf_x = []
            for time in ecmwf_times:
                w = ReadWinds.get_ecmwf(time, interp=False, return_stability=False)
                ecmwf_speeds.append(w.speed)
                ecmwf_bearings.append(w.bearing)
                ecmwf_x.append(dhour(overpass.time,time))
            print "Using old ECMWF"
            print "Exception:"
            print exc
            
        ax1.plot(ecmwf_x, ecmwf_speeds, marker=_marker, color=_ecmwf_col) 
        ax2.plot(ecmwf_x, ecmwf_bearings, marker=_marker, color=_ecmwf_col)
    
    if "MERRA" in wind_sources:
        merra_handle = mlines.Line2D([], [], color=_merra_col,
                                        marker=_marker, label='MERRA')
        legend_handles.append(merra_handle)
        legend_labels.append('MERRA')
        merra_speeds = []
        merra_bearings = []
        merra_x = [dhour(overpass.time,time) for time in merra_times]
        for i,time in enumerate(merra_times):
            x = merra_x[i]
            w = ReadWinds.get_merra(time)
            merra_speeds.append(w.speed)
            merra_bearings.append(w.bearing)
            if steps:
                ax1.plot([x-1.5, x+1.5], [w.speed, w.speed],
                            marker=_cap, color=_merra_col)
                
                ax2.plot([x-1.5, x+1.5],[w.bearing, w.bearing],
                            marker=_cap, color=_merra_col)
        
        ls = '' if steps else '-'
        if steps:
            handle_map.update({merra_handle: HandlerLine2D(numpoints=1)})
        ax1.plot(merra_x,merra_speeds,marker=_marker, color=_merra_col, ls=ls)
        ax2.plot(merra_x,merra_bearings,marker=_marker, color=_merra_col, ls=ls)
    
    if "GEM" in wind_sources:
        gem_handle = mlines.Line2D([], [], color=_gem_col,
                                        marker=_marker, label='GEM')
        legend_handles.append(gem_handle)
        legend_labels.append('GEM')
        # handle_map.update({gem_handle: HandlerLine2D(numpoints=2)})
        gem_speeds = []
        gem_bearings = []
        gem_x = []
        for time in gem_times:
            try:
                w = ReadWinds.get_gem(time, interp=False)
                gem_speeds.append(w.speed)
                gem_bearings.append(w.bearing)
                gem_x.append(dhour(overpass.time, time))
            except Exception as e:
                print "Exception:", e
        ax1.plot(gem_x,gem_speeds, marker=_marker, color=_gem_col)
        ax2.plot(gem_x, gem_bearings, marker=_marker, color=_gem_col)


    ax1.set_xticks(xticks)
    Formats.set_tickfont(ax1)
    Formats.set_tickfont(ax2)
    ax1.set_xlim(-_hours_back, _hours_forward)
    ax1.axvline(color=_time_indicator_colour, lw=_time_indicator_lw)
    time_indicator_handle = mlines.Line2D([], [], color=_time_indicator_colour,
                                lw=_time_indicator_lw, label='Overpass Time')
    legend_handles.append(time_indicator_handle)
    legend_labels.append('Overpass Time')
    leg = plt.legend(legend_handles, legend_labels,
                handler_map=handle_map,
                bbox_to_anchor=(_leg_loc),
                loc=3 , ncol=4, mode="expand",
                borderaxespad=0.1, prop=_leg_prop)
    ax1.set_ylabel(_ylabel_speed, fontsize=_labelfont, fontname=Formats.globalfont)
    ax1.grid(grid)

    ax2.set_xticks(xticks)
    ax2.set_xlim(-_hours_back, _hours_forward)
    ax2.axvline(color=_time_indicator_colour, lw=_time_indicator_lw)
    ax2.set_ylabel(_ylabel_dir, fontsize=_labelfont, fontname=Formats.globalfont)
    ax2.set_xlabel(_xlabel, fontsize=_labelfont, fontname=Formats.globalfont)
    if ylim:
        ax2.set_ylim(ylim)
    ax2.grid(grid)
    
    # set legend font to Formats.globalfont
    legtext = leg.get_texts()
    plt.setp(legtext, fontname=Formats.globalfont)
    
    plt.suptitle("Wind speed and direction for {0}".format(overpass.info), fontsize=_maintitle, fontname=Formats.globalfont)
    plt.subplots_adjust(**_adjust_params)
    
    plt.savefig(save_name, dpi=_dpi)