"""
GridPlot.py makes combined Grid plots

Code taken from Combined Figures and adapted to only make grid plots
"""

import math
import numpy as np

from matplotlib import pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.collections import PolyCollection
import matplotlib as mpl

import PST
import PlumeModel
import Geometry
import Units
import File
import ModelFit
import Formats
import boundaries
import namespace

# set mathtext font to be the same as regular font
mpl.rcParams['mathtext.default'] = 'regular'

defaults = namespace.Namespace(
# resolution and shape constants
_DPI = 500,
_size = (8,6),
_shape = (6,7),
_obs_height = 4,
_obs_width = 4,
_cbar_height = 5,

_cmap = "Spectral_r",

# constants for specifying gridspec
_obs_grid = {'left':0.15,
             'right':0.8,
             'wspace':0.05,
             'top':0.9,
             'bottom':0.2},

_mod_grid = {'left':0.1,
             'wspace':0.05,
             'hspace':0.05,
             'top':0.9},
_cbar_grid = {  'left':0.15,
                'right':0.8-0.05,
                'bottom':0.2, 'top':0.4},

# final adjustment to leave room for the title
_subplot_adjustment = {'top':0.9},

# specifying font sizes
_labelfont = 12,
_textfont = 10.5,
_titlefont = 14,
_panel_labelfont = 12,
_mod_labelpad = 0.05,
_ticklabelfont = 12,

font = Formats.globalfont,

# positions for panel labels
_panel_labelx = -25,
_panel_labelx_obs = -17.5,
_panel_labely = 0,
_panel_labely_obs = 0,

# resolution constants for the plots
_xres = 1001,
_yres = 1001,

_dx = 1.e2,
_dy = 1.e2,

_h_res = 10, # factor higher res than other arrays
_decay_threshold = 0.005,

_ctick_fmt = '{}',
_txt_dec_fmt = '{:.4f}',

_paneltext_x = 0.02,
_paneltext_y = 0.02,
_paneltext_xspace = 0.15,

# title: formatted by overpass.info and windspeed
_title = "%s, wind %s m/s, %s$^{\circ}$",

_cbarlabel = "Xco$_2$ enhancement relative to background",
_obslabel = "Observed Xco$_2$ enhancement",
_modlabel = "Model Xco$_2$ enhancement",

_xlabel = 'Distance along wind (km)',
_ylabel = 'Distance perpendicular to wind (km)',


clim = (0.99, 1.01),
xlim = (-20, 80),
ylim = (-50, 50),
x_step = None,
y_step = 20,
f_plume = 0.10,
f_background = 0.01,
offset = 3.e3,
y_max_positive = 50.e3,
y_min_positive = 0.,
y_max_negative = 50.e3,
y_min_negative = 0.,
direction = 'y',
wind_adjustment = 0.,
x_max = 75.e3,
wind_source = 'Average',
snr_strong_co2_min=None,
chi_squared_max=None,
albedo_min=None,
albedo_max = None,
surface_pressure_min=None,
surface_pressure_max=None,
smooth=False,
outcome_flags = {1,2},
force_winds = None,
sza_adjustments = True,

temporal_factors = False,
uncertainty = False,

plot_offset = False,

bias_correction ='corrected',

scatter_plot = False,

background_thresholds = [0.01],
plume_thresholds = [0.10, 0.25],
force_wind = None,
weighted = False,
units = Units.output_units,
stability = None,
surface_stability = True,

xco2_min = 395,
xco2_max = 405,

opacity = 0.0,

secondary_sources = [],
fixed_secondary_sources = [],

background_average = None,
)

def main(overpass, fname, **kwargs):
    params = defaults
    params.update(**kwargs)
    
    bg_kwargs = {  'background_factor':params.f_background,
                    'ymax_positive':params.y_max_positive,
                    'ymax_negative':params.y_max_negative,
                    'ymin_negative':params.y_min_negative,
                    'ymin_positive':params.y_min_positive,
                    'offset':params.offset,
                    'sign':params.direction
                }
    
    filt_args = {   'chi_squared_max':params.chi_squared_max,
                    'snr_strong_co2_min':params.snr_strong_co2_min,
                    'albedo_min':params.albedo_min,
                    'albedo_max':params.albedo_max,
                    'outcome_flags':params.outcome_flags,
                    'surface_pressure_min':params.surface_pressure_min,
                    'surface_pressure_max':params.surface_pressure_max
                }
    
    plume_args = dict(  plume_factor = params.f_plume,
                        xmax = params.x_max
                    )

    print "Creating subplots"
    # Initialize gridspecs for the different panels
    obs_gs = gridspec.GridSpec(*params._shape)
    obs_gs.update(**params._obs_grid)
    
    mod_gs = gridspec.GridSpec(*params._shape)
    mod_gs.update(**params._mod_grid)
    
    cbar_gs = gridspec.GridSpec(*params._shape)
    cbar_gs.update(**params._cbar_grid)
        
    fig = plt.figure(figsize=params._size)
    
    h, w = params._shape
    half_w = params._obs_width
    
    # add subplots using gridspecs
    obs_ax = fig.add_subplot(obs_gs[:params._obs_height, :half_w])
    
    mod_ax = fig.add_subplot(mod_gs[:int(h//2), half_w:])
    modfull_ax = fig.add_subplot(mod_gs[int(h//2):, half_w:])
    
    cbar_ax = fig.add_subplot(cbar_gs[params._cbar_height, :half_w])
    
    # set tick locations if the step sizes are specified
    if params.x_step:
        dx = params.x_step
        xticks = np.arange(int(dx*math.ceil(params.xlim[0]/dx)),
                                                params.xlim[1]+1., dx)
        obs_ax.set_xticks(xticks)
        mod_ax.set_xticks(xticks)
        modfull_ax.set_xticks(xticks)
        
    if params.y_step:
        dy = params.y_step
        yticks = np.arange(int(dy*math.ceil(params.ylim[0]/dy)),
                                                params.ylim[1], dy)
        yticks_full = np.arange(int(dy*math.ceil(params.ylim[0]/dy)),
                                                    params.ylim[1]+1., dy)
        obs_ax.set_yticks(yticks_full)
        mod_ax.set_yticks(yticks_full)
        modfull_ax.set_yticks(yticks)
    
    # add labels, titles, set fonts
    label_args = dict(  fontsize = params._labelfont,
                        fontname = params.font )
    obs_ax.set_xlabel(params._xlabel, **label_args)
    obs_ax.set_ylabel(params._ylabel, **label_args)
    modfull_ax.set_xlabel(params._xlabel, **label_args)
    
    mod_ax.tick_params('x', bottom='off', labelbottom='off')
    
    title_args = dict(  fontsize = params._titlefont,
                        fontname = params.font )
    obs_ax.set_title(params._obslabel, **title_args)
    mod_ax.set_title(params._modlabel, **title_args)
    
    # now start the real work, axes are set as much as we can right now
    
    a = params.stability if params.stability else overpass.a
    
    try:
        wind = getattr(overpass, params.wind_source)
    except AttributeError:
        raise AttributeError('Overpass has no wind source "%s"' % params.wind_source)
    except Exception:
        raise
    wind = wind.rotate(params.wind_adjustment)
    
    windspeed = Formats.windspeedformat % wind.speed
    wind_direction = Formats.winddirectionformat % wind.bearing
    fig.suptitle(params._title % (overpass.info, windspeed, wind_direction), **title_args)
    
    F = overpass.get_emissions(temporal_factors=params.temporal_factors)
    F.convert(Units._model_units)
    u = wind.speed
    
    free_secondary_emissions = [src.get_emissions(overpass, temporal_factors=params.temporal_factors)
                                            for src in params.secondary_sources]
    
    fixed_secondary_emissions = [src.get_emissions(overpass, temporal_factors=params.temporal_factors)
                                            for src in params.fixed_secondary_sources]
    all_emissions = [F] + free_secondary_emissions + fixed_secondary_emissions
    
    co2_var = "smoothed_{}_xco2" if params.smooth else "{}_xco2"
    co2_var = co2_var.format(params.bias_correction)
    
    print 'Running Model with parameters'
    model_results = ModelFit.Model(
        overpass,
        f_plume = params.f_plume,
        f_background = params.f_background,
        offset = params.offset,
        y_max_positive = params.y_max_positive,
        y_max_negative = params.y_max_negative,
        y_min_negative = params.y_min_negative,
        y_min_positive = params.y_min_positive,
        direction = params.direction,
        wind_adjustment = params.wind_adjustment,
        wind_sources = params.wind_source,
        smooth = params.smooth,
        surface_stability = a,
        stability = params.stability,
        temporal_factors = params.temporal_factors,
        bias_correction = params.bias_correction,
        LocalBackground = PlumeModel.InBackground,
        LocalInPlume = PlumeModel.InPlume,
        co2_source = 'xco2',
        custom_wind = None,
        snr_strong_co2_min = params.snr_strong_co2_min,
        chi_squared_max = params.chi_squared_max,
        albedo_min = params.albedo_min,
        albedo_max = params.albedo_max,
        outcome_flags = params.outcome_flags,
        surface_pressure_max = params.surface_pressure_max,
        surface_pressure_min = params.surface_pressure_min, 
        background_average = params.background_average,
        secondary_sources = params.secondary_sources,
        fixed_secondary_sources = params.fixed_secondary_sources,
        x_max = params.x_max,
        scatter_plot = params.scatter_plot,
        force_winds = params.force_winds,
        units = params.units,
        sza_adjustments = params.sza_adjustments,
        weighted = params.weighted,
        uncertainty = params.uncertainty
)
    _, _, n_plume, cor = model_results[0]
    
    if params.secondary_sources:
        coordinate = Geometry.CoordGeom(wind)
        posns_from_main = [(0,0)]+[coordinate.coord_to_wind_basis(overpass.lat, overpass.lon, second.lat, second.lon) for second in params.secondary_sources]
        x = [pair[0] for pair in posns_from_main]
        y = [pair[1] for pair in posns_from_main]

        if params.plot_offset:
            x_center, y_center = np.average(np.array([x,y]), axis=1, weights=([F]+free_secondary_emissions))
            x_from_center = [x0 - x_center for x0 in x]
            y_from_center = [y0 - y_center for y0 in y]
            
            # indices of top and bottom sources
            neg_offset = y_from_center.index(max(y_from_center))
            pos_offset = y_from_center.index(min(y_from_center))
            
            ## -1*y because the y in wind-basis is left-handed but we want the
            ##  plots to be the regular right-handed system
            # offset of bottom source on plot
            pos_start = (x_from_center[pos_offset],-1*y_from_center[pos_offset])
            # offset of top source on plot
            neg_start = (x_from_center[neg_offset],-1*y_from_center[neg_offset])
            
        else:
            x_center, y_center = 0, 0
            
            pos_start = (0,0)
            neg_start = (0,0)

    else:
        x_center, y_center = (0,0)
        
        pos_start = (0,0)
        neg_start = (0,0)
        
    c_offset = (x_center, y_center)
    
    x_min = params.xlim[0]*1000.
    x_max = params.xlim[1]*1000.
    y_min = params.ylim[0]*1000.
    y_max = params.ylim[1]*1000.
    
    print 'Opening full file for making plots'
    data = File.full(overpass)
    
    def distance(vertices, tlat, tlon, wind, shift=(0,0)):
        """Takes in an array shape (4, 2) of
            [ [lon1 lat1],
              [lon2 lat2],...]
            and returns an equivalenty shaped array of
            [ [x1 y1],
              [x2 y2], ...]
            As measured by in the direction of the wind"""
        distance_array = []
        for i in range(4):
            lon, lat = vertices[i]
            x, y = Geometry.CoordGeom(wind).coord_to_wind_basis(tlat, tlon, lat, lon)
            distance_array.append((x-shift[0],-(y-shift[1])))
        return np.array(Geometry.convex_hull(distance_array))
        
    distances = np.array([distance(data.retrieval_vertex_coordinates[j], overpass.lat, overpass.lon, wind, shift=c_offset) for j in range(len(data.retrieval_vertex_coordinates))])
    
    background = File.File()
    background_k = []
    
    plume = File.File()
    else_data = File.File()
    failed_quality_data = File.File()
    
    x_offset, y_offset = data.get_offset(overpass, wind)
    
    if params.secondary_sources:
        secondary_offsets = data.get_secondary_offset(overpass, wind, secondary_sources=params.secondary_sources)
    
    print 'Classifying points'
    
    verts = []
    observed_xco2 = []
    model_xco2 = []
    
    verts_qf = []
    observed_xco2_qf = []
    model_xco2_qf = []
    all_sources = params.secondary_sources + params.fixed_secondary_sources
    for i in range(len(data)):
        coordinate = Geometry.CoordGeom(wind)
        rlat = data.retrieval_latitude[i]
        rlon = data.retrieval_longitude[i]
        x,y = coordinate.coord_to_wind_basis(overpass.lat,
                                                overpass.lon ,rlat, rlon)
        dist = Geometry.CoordGeom.cartesian_distance((x,y),
                                                     (x_offset, y_offset))
        
        in_background = PlumeModel.InBackground(x,y,dist,u,1.0,a, **bg_kwargs)
        in_plume = PlumeModel.InPlume(x,y,u,F,a,**plume_args)
        for j,second in enumerate(params.secondary_sources):
            xs,ys = coordinate.coord_to_wind_basis(second.lat,second.lon,
                                                            rlat, rlon)
            dx, dy = secondary_offsets[j]
            secondary_dist = Geometry.CoordGeom.cartesian_distance((xs,ys),
                                                                    (dx,dy))
            in_secondary_background = PlumeModel.InBackground(xs,ys,secondary_dist,u,1.,a,**bg_kwargs)
            in_secondary_plume = PlumeModel.InPlume(xs,ys,u,1.,a,**plume_args)
            
            in_background = in_background and in_secondary_background
            in_plume = in_plume or in_secondary_plume
            
        if in_plume:
            if data.quality(i, **filt_args):
                plume.append(data, i)
            else:
                failed_quality_data.append(data, i)
                
        elif in_background:
            if data.quality(i, **filt_args):
                background.append(data, i)
                background_k.append(data.k[i])
            else:
                failed_quality_data.append(data, i)
        
        else:
            if data.quality(i, **filt_args):
                else_data.append(data, i)
            else:
                failed_quality_data.append(data, i)
       
            
        x_shifted = x - c_offset[0]
        y_shifted = y + c_offset[1]
        
        if y_min<=y_shifted<=y_max and x_min<=x_shifted<=x_max:
            lat_row = int((y_max-y_shifted)//1000)
            lon_col=int((x_shifted-x_min)//1000)
            
            if params.sza_adjustments:
                sza = Geometry.SZA(data,wind)
                enhancement = sza.V(x,y,u,F,a,i)
            else:
                enhancement = PlumeModel.V(x,y,u,F,a)

            for ind, child in enumerate(all_sources):
                F_second = all_emissions[ind+1]
                
                x_p, y_p = coordinate.coord_to_wind_basis(overpass.lat, overpass.lon, child.lat, child.lon)
                xs, ys = (x-x_p, y-y_p)
                
                if params.sza_adjustments:
                    second_enhancement = sza.V(xs,ys,u,F_second,a,i)
                else:
                    second_enhancement = PlumeModel.V(xs,ys,u,F_second,a)
                    
                enhancement+=second_enhancement
            if data.quality(i, **filt_args):
                model_xco2.append(enhancement)
                verts.append(distances[i])
                observed_xco2.append(data[co2_var][i])
            else:
                model_xco2_qf.append(enhancement)
                verts_qf.append(distances[i])
                observed_xco2_qf.append(data[co2_var][i])
            
    if params.background_average:
        background_mean = background_average
    else:
        background_mean = np.mean(background[co2_var])
    background_mean_k = np.mean(background_k)
    background_n = len(background)
    
    model_xco2 = np.array(model_xco2)
    model_xco2/=(background_mean*background_mean_k)
    model_xco2+=1.
    
    model_xco2_qf = np.array(model_xco2_qf)
    model_xco2_qf/=(background_mean*background_mean_k)
    model_xco2_qf+=1.
    
    verts = np.array(verts)
    verts_qf = np.array(verts_qf)
    observed_xco2 = np.array(observed_xco2)/float(background_mean)
    observed_xco2_qf = np.array(observed_xco2_qf)/float(background_mean)
    
    print 'Making grid plot'
    observed_coll = PolyCollection(verts/1000., array = observed_xco2,
                                    edgecolors='none', cmap=params._cmap)

    observed_coll_qf = PolyCollection(verts_qf/1000., array = observed_xco2_qf,
                                    edgecolors = 'none', cmap = params._cmap,
                                    alpha = params.opacity)
    
    model_coll = PolyCollection(verts/1000., array = model_xco2,
                                    edgecolors= 'none', cmap = params._cmap)
                                    
    model_coll_qf = PolyCollection(verts/1000., array = model_xco2_qf,
                                    edgecolors='none', cmap = params._cmap,
                                    alpha = params.opacity)
                                    
    collections = [observed_coll, observed_coll_qf,
                    model_coll, model_coll_qf]
    
    for coll in collections:
        coll.set_clim(*params.clim)
    
    obs_ax.add_collection(observed_coll)
    obs_ax.add_collection(observed_coll_qf)
    
    mod_ax.add_collection(model_coll)
    mod_ax.add_collection(model_coll_qf)
    
    cbarticks = np.linspace(params.clim[0], params.clim[1], 5)
    cbar = fig.colorbar(observed_coll, cax=cbar_ax, orientation='horizontal',
                        use_gridspec=True, ticks=cbarticks)
    
    cbar.set_label(params._cbarlabel, **label_args)
    cbar.ax.set_xticklabels([params._ctick_fmt.format(x) for x in cbarticks],
                                            fontname=params.font)
    
    bg_mean = Formats.ppmformat % background_mean
    scor = Formats.ppmformat % cor

    # add model to plot
    print 'Calculating model values for grid plot'
    position_from_main = [(0,0)]
    coordinate = Geometry.CoordGeom(wind)
    all_sources = params.secondary_sources + params.fixed_secondary_sources
    for second in all_sources:
        posn = coordinate.coord_to_wind_basis(overpass.lat, overpass.lon, second.lat, second.lon)
        position_from_main.append(posn)
    
    position_from_center = [(x-c_offset[0], y-c_offset[1]) for (x,y) in position_from_main]
    
    x_ax_absolute = np.arange(x_min, x_max+params._dx, params._dx)
    y_ax_absolute = np.arange(y_min, y_max+params._dy, params._dy)
    y_ax_absolute-=0.5*params._dy
    model_array = np.ones((len(y_ax_absolute), len(x_ax_absolute)))
    
    x_ax_plot = (x_ax_absolute-0.5*params._dx)/1000.
    y_ax_plot = (y_ax_absolute-0.5*params._dx)/1000.
    
    normalize = background_mean*background_mean_k
    for ind in range(len(position_from_main)):
        x_rel, y_rel = position_from_center[ind]
        x_ax = x_ax_absolute - x_rel
        y_ax = y_ax_absolute + y_rel
        F = all_emissions[ind]
        rows, cols = model_array.shape
        for row in range(rows):
            for col in range(cols):
                x,y = x_ax[col], y_ax[row]
                enhancements = PlumeModel.V(x, y, u, F, a)/normalize
                model_array[row, col] += enhancements
    
    mask_value = 1+(params.clim[1]-1)*(params._decay_threshold)
    model_array = np.ma.masked_less_equal(model_array, mask_value)
    
    modfull_ax.pcolormesh(x_ax_plot, y_ax_plot, model_array, cmap=params._cmap, vmin=params.clim[0], vmax=params.clim[1])
    modfull_ax.grid(True)
    
    obs_ax.text(params._paneltext_x, params._paneltext_y,
                    'a = {}\nBackground = {} ppm'.format(a, bg_mean),
                    fontsize=params._textfont, fontname=params.font,
                    transform = obs_ax.transAxes)
    
    obs_ax.text(params._paneltext_xspace, 1-params._paneltext_y,
                    'Number of points in plume: %s\nR = %s'%(n_plume, scor),
                    fontsize = params._textfont, verticalalignment = 'top',
                    fontname = params.font, transform = obs_ax.transAxes)
    
    bounds = boundaries.Boundaries(obs_ax, mod_ax, modfull_ax)
    bounds.plot(a, pos_start, neg_start, params.plume_thresholds,
                    params.background_thresholds, xmax=1000*params.xlim[1],
                    ymax=params.ylim[1], offset=params.offset)    
    
    grid_axes = (obs_ax, mod_ax, modfull_ax)
    axes = (obs_ax, mod_ax, modfull_ax)
    for gax in grid_axes:
        gax.set_xlim(*params.xlim)
        gax.set_ylim(*params.ylim)
        gax.grid(True)
    
    for ax in grid_axes:
        Formats.set_tickfont(ax)
    
    fig.savefig(fname, dpi=params._DPI, bbox_inches='tight')
    print 'Saved figure as', fname
    
if __name__ == '__main__':
    from Overpasses import *
    main(Westar20151204, 'westar_gridonly.png', xlim=(-40,60), ylim=(-20, 20), y_step=5, clim=(0.995, 1.005))