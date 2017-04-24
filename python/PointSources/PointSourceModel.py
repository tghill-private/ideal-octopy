#!/usr/bin/env python
"""
PointSourceModel.py wraps the important module functions and controls
their behaviour through keyword arguments.

The file "/home/tim/PointSources/Docs/Keywords for PointSourceModel.docx"
lists the available keyword arguments for the functions in this script.
"""

module_path = '/home/tim/PointSources/PythonModules'

# Use sys.path.append so this script can always find the modules
import sys
sys.path.append(module_path)

import numpy

import ModelFit
import GridPlot
import VertPlot
import printf
import timing
import PlotOverpasses
import WindHistory
import HourlyEmissionsPlot
import CombinedFigures

# modules to load global Overpass and PointSource variables
from Overpasses import *
from Sources import *

@printf.kwinfo
def Model(overpass, **kwargs):
    """
    Calculates model scale factors, estimated emissions, and
      uncertainties for the specified overpass
    """
    print overpass.info
    return ModelFit.Model(overpass, **kwargs)

def ModelUncertainty(overpass, **kwargs):
    """Calculates the plume and background uncertainty using an ensemble
    combination of parameters.
    """
    return ModelFit.ModelUncertainty(overpass, **kwargs)

@printf.kwinfo
def CreatePlot(overpass,file_name,**kwargs):
    """
    CreatePlot makes "Grid Plots" for the given overpass, and saves the file as file_name
    file_name is the full file path (string); for example, "/home/user/PointSources/GridPlots/overpass_plot.png"
    """
    return GridPlot.main(overpass,file_name,**kwargs)

@printf.kwinfo
def GetBestWind(overpass, **kwargs):
    """GetBestWind(overpass) takes an overpass instance and searches for the best 
    wind adjustments for the overpass, and returns the wind adjustment angle 
    (measured relative to the average of ECMWf and MERRA) and the correlation at this adjustment.
    
    It considers the total range spanned by the ECMWF and MERRA vectors, and searches this entire range, plus
    10 degrees on either side of this range, for the best angle.
    For example, if merra is at 125 degrees and ECMWF is at 160 degrees, it will search from
    115 degrees to 170 degrees.
    """
    print overpass.info
    return ModelFit.best_winds(overpass, **kwargs)

@printf.kwinfo
def VerticalPlot(overpass, file_name, **kwargs):
    """
    Creates a vertical plot for the overpass, saves as file_name
    
    Uses Average of MERRA and ECMWF for wind
    """
    return VertPlot.vertical_plot(overpass,file_name,**kwargs)
    
@printf.kwinfo
def KML(overpass, file_name, **kwargs):
    return PlotOverpasses.Plot(overpass, file_name, **kwargs)

@printf.kwinfo
def PlotWind(overpass, file_name, **kwargs):
    """Plots a time series for wind direction and speed for three
    days before and 1 day after an overpass"""
    return WindHistory.historical(overpass, file_name, **kwargs)
    
def PlotEmissions(overpass, file_name, units='k_t/day'):
    """Creates an hourly emissions plot for the given overpass,
    saving the file as file_name, and measuring emissions with
    units k_t/day by default.
    
    units is a valid units string, for example 'M_t/yr' or 'g/s'
    """
    return HourlyEmissionsPlot.plot(overpass, file_name, units=units)
    
@printf.kwinfo
def CombinedPlot(overpass, file_name, **kwargs):
    """Creates combined grid and vertical plots, saving as file_name"""
    CombinedFigures.main(overpass, file_name, **kwargs)
