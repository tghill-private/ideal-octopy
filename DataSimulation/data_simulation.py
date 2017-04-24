#!/usr/bin/env python
"""
data_simulation.py carries out the data simulation experiment.

This script includes biases based on the input parameters, and makes
the simulated plume figures. You can repeatedly run the sim function
to analyze multiple different parameter sets, or the variance in estimated
emissions with the same parameters.
"""
import os

import numpy as np
from matplotlib import pyplot as plt

from ptsource import Units
from ptsource import PlumeModel

import arrtools

background = 400. # background in ppm

def column_to_xco2(co2_column):
    """Converts co2_column from total column CO2 (g/m^2) to Xco2 in ppm.
    
    Function uses the empirically determined conversion factor
    6000 g/m^2 = 400 ppm from looking at OCO-2 data.
    The true conversion factor would depend on the total O2
    column, so we ignore this complication and use the constant ratio.
    """
    conversion = 6000./400.
    return co2_column/float(conversion)


array_shape = (1200, 1200) # shape of fully-resolved array

# defining the region to simulate
xmin = 0
xmax = 60.e3
ymin = 0
ymax = 60.e3
xlim=(0.,xmax/1000.) # maximum x in km
ylim=(0.,ymax/1000.) # maximum y in km

# axis tick marking locations
axisticks = (0,20,40,60)

full_res = xmax/float(array_shape[0]) # side-length (m) of small box
avg11_res = 2.e3                      # side-length (m) of 2nd column
goal_res = 4.e3                       # side-length (m) of 3rd column
breakthrough_res = 7.e3               # side-length (m) of 4th column
thresh_res = 10.e3                    # side-length (m) of 5th column

# list of resolutions for each plot
resolutions = [full_res, avg11_res, goal_res, breakthrough_res, thresh_res]*3

noise_strength = 1.0        # standard deviation of noise in ppm at 2km x 2 km
terrain_strength = 0.005    # relative terrain strength
footprint_bias = 0.0015     # relative footprint bias strength

# simulated relative sensitivity for (0, 2) albedos
albedo_coeff = [0.999, 1.001]

# defining the simulated emission rates
F_small = Units.SciVal(6., 'M_t/yr')
F_small.convert(Units._model_units)

F_med = Units.SciVal(13., 'M_t/yr')
F_med.convert(Units._model_units)

F_large = Units.SciVal(25., 'M_t/yr')
F_large.convert(Units._model_units)

# interfering secondary source location and emission rates
secondary_location = (5.e3, 15.e3)
F_secondary = Units.SciVal(5., 'M_t/yr')
F_secondary.convert(Units._model_units)

# emissions defines what simulated emissions to use for each panel
emissions = [F_small]*5 + [F_med]*5 + [F_large]*5

# simulation parameters
a_sim = 156.
u_sim = 4.
theta_sim = 45.

# plotting constants
cmin = 0.99
cmax= 1.01
cticks = np.linspace(cmin,cmax,5)
cmap = 'Spectral_r'

# font sizes
label = 8
ticks = 8
title = 8

subplot_adjustments = {'wspace':0.3, 'hspace':0.4, 'right':0.93}

def rotate(x, y, theta):
    """Rotates vector (x,y) through angle theta.
    
    Args:
        * x, y: distance components
        * theta: angle in degrees
    
    Returns (x', y') where (x', y') are the new coordinates
    after rotating through angle (in degrees) theta.
    """
    a = np.radians(theta)
    xp = np.cos(a)*x + np.sin(a)*y
    yp = np.sin(a)*x - np.cos(a)*y
    return (xp, yp)

def make_noise(shape, strength=noise_strength, distribution='normal'):
    """Creates an array simulating instrument noise.
    
    Args:
        * shape: shape of the array to make
        * strength: noise strength to simulate
        * distribution: distribution shape to pull noise
            from. Options are 'normal' (Gaussian) or 'uniform'
    
    Returns:
        * noise np.ndarray of shape 'shape'
    """
    if strength==0:
        return np.zeros(shape)
    else:
        if distribution=='normal':
            noise = np.random.normal(0., noise_strength, shape)
        elif distribution=='uniform':
            noise = np.random.random(shape)
            noise = arrtools.renorm(noise_strength)
            noise = center()
        else:
            raise TypeError("Value '%s' not recognized for 'distribution' argument" % distribution)
        
        return noise

def estimate_emissions(obs, alpha):
    """Estimates the emissions required to match model to observed Xco2.
    
    Args:
        * obs: list of 2D array of simulated Xco2 which we want to estimate
            the emissions of
        *alpha: list of 2D array of model alpha values (V/F values)
    
    Returns:
        list of the estimated emissions, in Mt/yr
    """
    estimates = []
    for (obs_array, alph_array) in zip (obs, alpha):
        slice = obs_array>0
        a_vector = np.vstack(alph_array[slice].flatten())
        obs_vector = obs_array[slice].flatten() - background
        F = np.linalg.lstsq(a_vector, obs_vector)[0][0]
        F = Units.SciVal(F, Units._model_units)('M_t/yr')
        estimates.append(F)
    return np.array(estimates).reshape(3,4)

def set_axes():
    """Creates the figure and subplot axes for the plot.
    
    Sets titles and places subplots on the figure,
    but does not set plot limits, tick labels, etc.
    This is done with the arr_colormesh function after
    the pcolormesh plotting commands.
    """
    fig, axes = plt.subplots(nrows=3,ncols=5)
    
    cbar_ax = fig.add_axes([0.95,0.25,0.01,0.5])
        
    for row in axes:
        row[0].set_title('Fully Resolved', fontsize=title)
        row[1].set_title('2x2km$^2$',fontsize=title)
        row[2].set_title('Goal 4x4km$^2$',fontsize=title)
        row[3].set_title('Breakthrough 7x7km$^2$',fontsize=title)
        row[4].set_title('Threshold 10x10km$^2$',fontsize=title)
    
    axes[0][0].set_xlabel('6 Mt CO$_2$/yr', fontsize=label)
    axes[1][0].set_xlabel('13 Mt CO$_2$/yr',fontsize=label)
    axes[1][0].set_ylabel('Distance (km)', fontsize=label)
    axes[2][0].set_xlabel('25 Mt CO$_2$/yr',fontsize=label)
    axes[2][2].set_xlabel('Distance (km)', fontsize=label)
    return (fig, axes, cbar_ax)

def arr_colormesh(x_ax, y_ax, arrs, **kwargs):
    """Creates pcolormesh plots for all arrays in arrs.
    
    calls pcolormesh(x_ax, y_ax, arrs, **kwargs) for arr in arrs,
    and configures the axes (tick labels, xlim, ylim, etc.).
    
    Args:
        * x_ax: x-axis for the data in each array
        * y-ax: y-axis for the data in each array
        * kwargs: Any keyword arguments to pass to the plt.pcolormesh funciton
    
    Returns:
        * fig, a plt.figure instance with all the subplots drawn on
    
    See http://matplotlib.org/api/pyplot_api.html#matplotlib.pyplot.pcolormesh
    for more information on pcolormesh function
    """
    fig, paxes, cax = set_axes()
    shape = (len(y_ax), len(x_ax))
    print shape
    print arrs[0].shape
    arrs_list = arrs.reshape((15,shape[0], shape[1]))
    
    
    for (arr, ax) in zip(arrs_list, paxes.flatten()):
        arr = np.ma.masked_less(arr, 0.9)
        cplot=ax.pcolormesh(x_ax, y_ax, arr, **kwargs)
        ax.grid(True)
        ax.tick_params(labelsize=ticks)
        ax.set_xticks(axisticks)
        ax.set_yticks(axisticks)
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)

    cax.tick_params(labelsize=ticks)
    cbar = fig.colorbar(cplot, cax=cax, ticks=cticks)
    plt.subplots_adjust(**subplot_adjustments)
    return fig
    
def simulate_enhancements(X, Y, emissions):
    """Simulates the enhancements for coordinate arrays X, Y.
    
    Uses each emission rate in the list emissions to simulate
    enhancements using default simulation parameters and positions
    from X, Y.
    
    Args:
        * X, Y: coordinate arrays, from np.meshgrid(xaxis, yaxis)
        * emissions: iterable of emission rates
    
    Effects:
        * Calculates an array giving simulated emissions at each
        point in X, Y. Writes these arrays to a file
    """
    shape = X.shape
    enhancements = {float(F):np.zeros(shape) for F in emissions}
    ncols, nrows = shape
    for col in xrange(ncols):
        for row in xrange(nrows):
            x0, y0 = X[row,col], Y[row,col]
            x_sim, y_sim = rotate(x0, y0, theta_sim)
            for F in emissions:
                F = float(F)
                V = PlumeModel.V(x_sim, y_sim, u_sim, F, a_sim)
                enhancements[F][row,col] = column_to_xco2(V)
    
    np.savetxt('data/sim_output_6mt_tst',
                    enhancements[float(F_small)])
    np.savetxt('data/sim_output_13mt_tst',
                    enhancements[float(F_med)])
    np.savetxt('data/sim_output_25mt_tst',
                    enhancements[float(F_large)])
    
def simulate_secondary_enhancements(X, Y, F):
    """Simulates enhancements for a secondary source with emissions rate F.
    
    Uses X, Y in same way as simulate_enhancements, but for one
    source with emission rate F.
    
    Args:
        * X, Y: coordinate arrays, from np.meshgrid(xaxis, yaxis)
        * F: emission rate
    
    Effects:
        * Calculates an array giving simulated emissions at each
        point in X, Y. Writes the array to a file
    """
    shape = X.shape
    enhancements = np.zeros(shape)
    ncols, nrows = shape
    for col in xrange(ncols):
        for row in xrange(nrows):
            x0, y0 = X[row,col], Y[row,col]
            x_sim, y_sim = rotate(x0, y0, theta_sim)
            F = float(F)
            V = PlumeModel.V(x_sim, y_sim, u_sim, F, a_sim)
            enhancements[row,col] = column_to_xco2(V)
    np.savetxt('data/sim_output_secondary', enhancements)

def model_enhancements(X, Y, u, theta, a):
    """Calculates the model enhancements based on positions in X, Y.
    
    Args:
        * X, Y: coordinate arrays, from np.meshgrid(xaxis, yaxis)
        * u: model wind speed
        theta: model wind direction
        a: model atmospheric stability parameter
    
    Returns:
        * numpy.ndarray giving the model "alpha" values for each point
            in X, Y.
    """
    shape = X.shape
    ncols, nrows = shape
    alpha = np.zeros(shape)
    for col in xrange(ncols):
        for row in xrange(nrows):
            x0, y0 = X[row,col], Y[row,col]
            xm, ym = rotate(x0, y0, theta)
            alpha[row,col] = column_to_xco2(PlumeModel.V(xm, ym, u, 1.0, a))
    return alpha

def sim(figname, noise_strength=noise_strength, terrain_bias=terrain_strength, cloud_mask=False, footprint_bias=footprint_bias, interference_bias=False, sample_mask=False, stability_bias=False, wind_bias=False, simulate=False, calculate_model=False, albedo_bias=False, u=u_sim, renorm=False, plot_factor=1):
    """Simulates Xco2 with included biases and estimates the emission rate.
    
    Loads the simualted emissions from disk, calculates or loads model
    values depending on the biases included, and calculates the
    least-squares solution for the emisisons that would result
    in the "observed" enhancements.
    
    Args:
        - figname: name to save simulated figure as (file extension
            correctly controls the file format; .eps works).
        - noise_strength: float specifying relative noise strength to use
            default 1.0
        - terrain_bias: float specifying terrain bias strength
            default 0.005
        - cloud_mask: Bool indicating whether to include cloud mask
        - footprint_bias: float specifying strength of footprint bias
            default 0.0015
        - interference_bias: Bool controlling inclusion of secondary source
        - sample_mask: False or string specifying which sample_mask file to use
        - stability_bias: False or float giving a_model value
        - wind_bias: False or float specifying model wind direction
        - calculate_model: Bool controlling whether we need to re-calculate
            model enhancements or it is okay to use the model enhancements
            saved to disk
        - albedo_bias: Bool controlling whether to include albedo bias
        - u: float specifying total wind speed for model and simulation
        - renorm: False, "sqrt", or "constant". False to let the noise
            decrease by natural averaging, "sqrt" to keep weak dependence
            on the side length, or "constant" to keep a constant noise strnegth
        - plot_factor: Integer factor giving the relative reduction in
            resolution to plot compared to the resolution the arrays are
            calculated at. To save the figures as eps files, need to
            set plot_factor ~ 10 to 20 or the files are too large to render.
    
    Returns:
        
    """
    x_ax = np.linspace(xmin, xmax, array_shape[1])
    y_ax = np.linspace(ymin, ymax, array_shape[0])
    X, Y = np.meshgrid(x_ax, y_ax)
    
    if simulate:
        print 'Simulating Enhnancements'
        simulate_enhancements(X, Y, [F_small, F_med, F_large])
        if interference_bias:
            X_second = X - secondary_location[0]
            Y_second = Y - secondary_location[1]
            simulate_secondary_enhancements(X_second, Y_second, F_secondary)
    
    secondary_enhancements = 0
    if interference_bias:
        secondary_enhancements = np.loadtxt('data/sim_output_secondary')
    
    if calculate_model:
        print 'Calculating model enhnacements'
        a_inv = stability_bias if stability_bias else a_sim
        theta_inv = wind_bias if wind_bias else theta_sim
        alpha = model_enhancements(X, Y, u_sim, theta_inv, a_inv)
        np.savetxt('data/model_output_modified', alpha)
    else:
        alpha = np.loadtxt('data/model_output')
    
    print 'Loading simulated enhnacements'
    enhancements6 = np.loadtxt('data/sim_output_6mt') + secondary_enhancements
    enhancements13 = np.loadtxt('data/sim_output_13mt') + secondary_enhancements
    enhancements25 = np.loadtxt('data/sim_output_25mt') + secondary_enhancements
    
    wind_adjust_factor = float(u_sim)/float(u)
    
    enhancements6*=wind_adjust_factor
    enhancements13*=wind_adjust_factor
    enhancements25*=wind_adjust_factor
    alpha*=wind_adjust_factor
    
    print 'Simulating Noise'
    noise = make_noise(array_shape, noise_strength)
    noise = arrtools.average(noise, int(avg11_res//full_res))
    noise = arrtools.center(noise)
    noise = arrtools.renorm(noise, noise_strength)
    
    sim_enhancements = []
    for e_array in [enhancements6, enhancements13, enhancements25]:
        sim_enhancements.extend([e_array for x in range(5)])
    
    print 'Generating biases'
    biases = []

    footprint = 1+(np.loadtxt('data/column_bias')*footprint_bias)
    biases.append(footprint)
    
    terrain = 1 + terrain_bias*np.loadtxt('data/simulated_terrain')
    biases.append(terrain)
    
    if albedo_bias:
        albedo = np.loadtxt('data/albedo_map')
        albedo[albedo==0]=albedo_coeff[0]
        albedo[albedo==1]=1
        albedo[albedo==2]=albedo_coeff[1]
        biases.append(albedo)
    
    masks = []
    if cloud_mask:
        cm = np.loadtxt('data/cloud_mask')
        masks.append(cm)
    
    if sample_mask:
        mask_array = os.path.join('data',sample_mask)
        if not os.path.exists(mask_array):
            raise IOError("Sample Mask '%s' does not exist" % mask_array)
        sm = np.loadtxt(mask_array)
        masks.append(sm)
    
    print 'Averaging and re-gridding arrays'
    finalized_plot_arrays = []
    fit_sim_arrays = []
    fit_inv_arrays = []
    for i,simulated in enumerate(sim_enhancements):
        # if i%5==0 we are plotting the "model" array and don't include biases
        if i%5==0:
            all_biases = 1
            
            mask = 1
            for msk in masks:
                mask*=msk
            simulated = np.array(simulated+background)*all_biases/background
            model_plot = arrtools.average(mask*simulated, plot_factor)
            model_plot = arrtools.reduce(model_plot, plot_factor)
            finalized_plot_arrays.append(model_plot)
            
        else:
            rfactor = int(resolutions[i]//full_res)
            all_biases = np.ones(array_shape)
            
            for bias in biases:
                rb = arrtools.average(bias, rfactor)
                all_biases*=rb
            
            total_mask = 1
            for msk in masks:
                mask = arrtools.average(msk, rfactor)
                mask[mask<0.5]=0
                mask[mask>0.5]=1
                total_mask*=mask
            
            alpha_array = arrtools.average(alpha, rfactor)
            fit_inv_arrays.append(arrtools.reduce(alpha_array, rfactor))
            
            if renorm==False:
                renorm_factor = 1.
            elif renorm=='sqrt':
                renorm_factor = np.sqrt(int(resolutions[i]//resolutions[1]))
            elif renorm=='constant':
                renorm_factor = int(resolutions[i]//resolutions[1])
            else:
                raise TypeError('"renorm" must be one of False, "sqrt", or "constant"')
                
            avg_noise = arrtools.average(noise, rfactor)*renorm_factor
            
            simulated = arrtools.average((simulated+background)*all_biases, rfactor) + avg_noise
            simulated*=total_mask
            simulated_r = arrtools.reduce(simulated, rfactor)
            
            plot_arr = arrtools.average(simulated, plot_factor)
            plot_arr = arrtools.reduce(plot_arr, plot_factor)
            finalized_plot_arrays.append(plot_arr/background)
            fit_sim_arrays.append(simulated_r)
            
    print "Estimating emissions..."
    estimates = estimate_emissions(fit_sim_arrays, fit_inv_arrays)
    print "Emissions Estimates:"
    print estimates
    if figname!="":
        print "Creating mesh plots"
        kwargs = {  'vmin':cmin,
                    'vmax':cmax,
                    'cmap':cmap
                }
        x_axis = (x_ax/1000.)[::plot_factor]
        y_axis = (y_ax/1000.)[::plot_factor]
        fig = arr_colormesh(x_axis, y_axis, np.array(finalized_plot_arrays), **kwargs)
        fig.savefig(figname, dpi=400, bbox_inches='tight', pad_inches=0.05)
        plt.clf()
        print 'Figure saved as', os.path.realpath(figname)
    
    return estimates