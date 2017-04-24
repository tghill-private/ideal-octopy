"""
Module ModelFunctions.py

This module calculates quality of fit between model and observed data.

Weighted least squares, scatter plot function, and the function to
compute scale factors, correlation, etc. are here
"""

from matplotlib import pyplot as plt
import numpy
import math

import Units


def lstsq(A, B, W=None):
    """
    Optionally Weighted least squares fit based on numpy.linalg.lstsq
    
    If W is not specified, uses exactly numpy.linalg.lstsq(A,B)
    
    Solves for x where B = Ax and A[i,j] has weight W[i,j]
    
    Weighted least squares uses B' = W*B and A' = W*A, then
    computes the least squares fit as usual
    
    * W can be 1-D or diagonal (numpy.linalg.diag is called on it) or None (default)
    * W is normalized before least squares fit is done
    """
    w = numpy.diag([1. for x in B]) if W is None else numpy.diag(W) # make the diagonal array of weights
    magnitude = numpy.linalg.norm(w) # normalize the diagonal array of weights so it doesn't change residuals
    w/=float(magnitude)
    X = numpy.dot(w,A)
    Y = numpy.dot(w,B)
    return numpy.linalg.lstsq(X,Y)


def make_scatter_plot(model,observed,save_name):
    """Makes a scatter plot between the model and observed data,
    saving the plot as save_name.
    
    Separate function because it has labels and titles specific to
    the model and observed data.
    """
    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    
    labelfont=10
    titlefont=10
    
    ax1.scatter(model,observed,s=10)
    ax1.grid()
    ax1.set_xlabel('Expected Xco$_2$ enhancements (ppm)',fontsize = labelfont)
    ax1.set_ylabel('Observed Xco$_2$ (ppm)',fontsize=labelfont)
    
    fig.suptitle('Observed vs. Expected Xco$_2$ Enhancements',fontsize=titlefont)
    fig.savefig(save_name, dpi=400)

    
    
    
class results_defaults:
    """A structure-like class for passing defaults and data to interpret_results
    """
    def __init__(self,**kwargs):
        for key, value in kwargs.items():
            setattr(self,key,value)
        self.average = 'median'
        self.null_value = (0,0,0,0) # this is actually where this value is stored
        self.co2_name = 'xco2'
        self.co2_attribute = 'corrected_xco2'
        self.output_units = Units.output_units


def interpret_results(plume_values, background_values, model, alpha, fixed, overpass, wind, defaults, reported_emissions, weights=False, print_messages=True, background_average = None, uncertainty=True):
    """
    Function for analyzing the data from observations and the plume model.
    
    This is where the scale factors, correlation, etc. are calculated.
    plume_values and background_values are File.File objects (or any objects
    with the same attributes).
    model and alpha are iterables of model enhancements and alpha values.
    overpass is a PST.Overpass instance
    wind is a PST.Wind instance
    defaults is a results_defaults instance
    weights=False is a Bool controlling whether weighted or un-weighted
        Least Squares is used
    
    This is the function that prints out all the information;
    use print_messages = False to not print anything
    """
    # plume_values.array()
    # background_values.array()

    co2_variable = defaults.co2_attribute
    co2_name = defaults.co2_name
    average = defaults.average
    null = defaults.null_value
    output_units = defaults.output_units
    
    # weights to use for least squares fit
    W = 1./(plume_values.xco2_uncert) if weights is True else None
    
    if wind.speed == 0.:
        raise ValueError("Windspeed is zero; not a valid Wind source")
        
    elif len(background_values)<=2:
        raise IndexError("Not enough points are in the background to carry out fit")
        
    elif len(plume_values)<=2:
        raise IndexError("Not enough points are in the plume to carry out fit")
    
    model_vector = numpy.array(model)
    model_alpha = numpy.array(alpha)
    
    background_average = background_average if background_average else numpy.mean(background_values[co2_variable])
    background_units = 'ppm' if co2_name=='xco2' else 'g/m^2'
    
    if co2_name == 'xco2':
        k_background_mean = numpy.mean(background_values.k)
        model_vector=model_vector/k_background_mean
        model_alpha=model_alpha/k_background_mean
        fixed=fixed/k_background_mean
        
    elif co2_name == 'column_co2':
        pass
    else:
        raise ValueError('co2_variable "{0}" must be one of "xco2" or "column_co2"'.format(co2_variable))
    
    observed_enhancements = numpy.array(plume_values[co2_variable])-background_average-fixed
    
    # calculates F, the emissions for all the sources (will be an array)
    F, F_resid, F_rank, F_singular = lstsq(model_alpha, observed_enhancements,W)
    
    # convert F to the desired output units
    F_mt = [Units.SciVal(f,Units._model_units).convert_cp(output_units) for f in F]
    total_emissions = float(F_mt[0])
    for emi in F_mt[1:]:
        total_emissions += float(emi)
    
    # new definition of scale factor
    s = total_emissions/reported_emissions
    
    # calculate correlation
    cor = numpy.corrcoef(model_vector.flatten(), observed_enhancements)[0,1]
    
    # enhancement the old definition of uncertainties were normalized to
    mean_enhancement = numpy.mean(observed_enhancements)
    
    wind_uncert = abs((overpass.MERRA.speed - overpass.ECMWF.speed)/(overpass.MERRA.speed + overpass.ECMWF.speed))
    
    # calculate relative uncertainty for plume, background
    N_plume = len(plume_values)
    plume_sum_sq_uncert = numpy.sum(numpy.array(plume_values.xco2_uncert)**2)
    plume_abs_uncert = math.sqrt(plume_sum_sq_uncert/N_plume)
    plume_observation_uncert = plume_abs_uncert/mean_enhancement
    
    N_background = len(background_values)
    bg_sum_sq_uncert = numpy.sum(numpy.array(background_values.xco2_uncert)**2)
    bg_abs_uncert = math.sqrt(bg_sum_sq_uncert/N_background)
    background_observation_uncert = bg_abs_uncert/mean_enhancement
    
    # alternate root-mean-square error and normalized root-mean-square-error
    #  comes from the residuals from least squares fit
    alternate_RMSE = math.sqrt(F_resid/len(plume_values))
    alternate_NRMSE = alternate_RMSE/float(mean_enhancement)
    
    ## Print out results
    
    if print_messages is True:
        print "Background Average: {0} {1}, using {2} points".format(background_average, background_units, len(background_values))
        print "Scale Factor: {0} ({1} points)".format(s, len(plume_values))
        print "Estimated Emissions: {0}".format(', '.join(map(str,F_mt)))
        print "Correlation: {0}".format(cor)    
        
        print "Residuals:",F_resid[0]
        
        if uncertainty:
            print "\nUncertainties:"
            print "Wind Uncertainty:", wind_uncert
            print "Plume Observation Uncertainty:", plume_observation_uncert
            print "Background Observation Uncertainty", background_observation_uncert
            print "Observation Uncertainties were normalized to {0} ppm".format(mean_enhancement)
            print "Normalized RMS Error from least squares fit:", alternate_NRMSE
    
    return (s, F_mt, len(plume_values), cor)
