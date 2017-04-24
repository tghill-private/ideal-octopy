"""
Module VertPlot.py

VertPlot creates so-called vertical plots for OCO-2 data near a Point Source.
function vertical_plot makes these plots
"""

from matplotlib import pyplot as plt
import numpy

import PST
import PlumeModel
import Geometry
import File
import Formats

labelfont = 18.
titlefont = 18.
ticklabelfont = 18.
_fig_size = (4, 10) # figure size in inches
_subplot_adjustments = {'top':0.95}
leftlabelpad = 35
rightlabelpad = 35
_dpi = 400

_plume_colour = 'r'
_bg_colour = 'b'
_other_colour = 'k'
_source_colour = 'y'
_bg_mean_colour = 'g'

_source_markersize = 10
_size = 5

_plume_lbl = 'In-Plume Points'
_bg_lbl = 'Assumed Background Points'
_other_lbl = 'Other Points'
_qual_lbl = 'Failed Quality Points'

def vertical_plot(overpass,file_name,bias_correction="corrected",x_max=75.e3,y_max_negative = 50.e3, y_max_positive=50.e3, f_plume=0.10, f_background=0.01,wind_adjustment=0.,wind_source="Average",y_min_positive=0., y_min_negative = 0., offset=3.e3, direction='y', xco2_min=395,xco2_max=405, plot_max=125, plot_min=125, snr_strong_co2_min=None, chi_squared_max=None, albedo_min=None, albedo_max = None, surface_pressure_min=None, surface_pressure_max=None, smooth=False, units='g/s', outcome_flags = {1,2}, secondary_sources = False,stability="new", force_wind=None, surface_stability=None, failed_quality_color='grey', show_latitude=False):
    """vertical_plot makes so-called vertical plots.
    
    Args:
      * overpass: a PST.Overpass instance
      * file_name: str, valid file path to save the image as
      
    Keyword Args:
      * see keyword arguments document
    """
    quality_args = {'chi_squared_max':chi_squared_max,
                    'snr_strong_co2_min':snr_strong_co2_min,
                    'albedo_min':albedo_min,
                    'albedo_max':albedo_max,
                    'outcome_flags':outcome_flags,
                    'surface_pressure_min':surface_pressure_min,
                    'surface_pressure_max':surface_pressure_max
                    }
    
    bg_kwargs = {'ymax_negative':y_max_negative,
                'ymax_positive':y_max_positive,
                'background_factor':f_background,
                'ymin_negative':y_min_negative,
                'ymin_positive':y_min_positive,
                'offset':offset,
                'sign':direction
            }
            
    if bias_correction not in File.allowed_bias_correction:
        raise ValueError("bias_correction must be one of {0}; given {1}".format(', '.join(File.allowed_bias_correction), bias_correction))
    
    co2 = "{0}_xco2".format(bias_correction)
    if smooth:
        co2 = 'smoothed_' + co2
    
    try:
        wind = getattr(overpass, wind_source).rotate(wind_adjustment)
    except AttributeError:
        raise TypeError('wind_sources must be one of {0}; given {1}'.format(", ".join(PST.AllWinds.valid_keys), wind_source))
    
    if force_wind:
        wind = force_wind
    
    u = wind.speed
    if surface_stability:
        a = surface_stability
    else:
        a = overpass.a if stability=="new" else overpass.a_old
    F = overpass.get_emissions(units)
    
    print "Using stability parameter a={0}".format(a)
    print("Opening and reading Full File")
    full_file = File.full(overpass)
    
    (x0, y0, index_min) = full_file.get_offset(overpass, wind, return_index=True)
    
    if secondary_sources:
        if hasattr(secondary_sources, "__iter__"):
            overpass.source.secondary = secondary_sources
            secondary_sources = True
        secondary_offsets = full_file.get_secondary_offset(overpass, wind)
        print "Using secondary sources {0}".format(overpass.source.secondary)
    
    if secondary_sources:
        all_source_latitudes = [overpass.lat] + [second.lat for second in overpass.source.secondary]
    else:
        all_source_latitudes = [overpass.lat]
    
    weighted_avg_lat = numpy.average(all_source_latitudes, weights=all_source_latitudes)
    lat_offset = overpass.lat - weighted_avg_lat
    
    lat0 = full_file.retrieval_latitude[index_min]
    lon0 = full_file.retrieval_longitude[index_min]
    
    lat_length = 0.001*Geometry.CoordGeom(wind).distance(overpass.lat,overpass.lon,overpass.lat+1,overpass.lon)

    plume_data = File.File()
    else_data = File.File()
    background_data = File.File()
    failed_quality_data = File.File()
    
    delta_lat = 3.
    lat_max = weighted_avg_lat + plot_max/lat_length
    lat_min = weighted_avg_lat - plot_min/lat_length
    
    i=0
    print("Classifying data")
    for i in range(len(full_file)):
        if full_file.quality(i, **quality_args):
            coordinate = Geometry.CoordGeom(wind)
            x,y = coordinate.coord_to_wind_basis(overpass.lat,overpass.lon,full_file.retrieval_latitude[i], full_file.retrieval_longitude[i])
            dist = Geometry.CoordGeom.cartesian_distance((x,y),(x0, y0))
            
            # Don't have a separate if secondary_sources... loop for background since it's far enough away that it shouldn't make a difference
            # As long as it isn't in the secondary plume, add the point to the background
            in_background = PlumeModel.InBackground(x,y,dist,u,F,a,**bg_kwargs)
            
            in_plume = PlumeModel.InPlume(x,y,u,F,a,plume_factor=f_plume,xmax=x_max)
            if secondary_sources:
                for ind, secondary in enumerate(overpass.source.secondary):
                    xs,ys = Geometry.CoordGeom(wind).coord_to_wind_basis(secondary.lat,secondary.lon,full_file.retrieval_latitude[i], full_file.retrieval_longitude[i])
                    secondary_offset = secondary_offsets[ind]
                    secondary_dist = Geometry.CoordGeom.cartesian_distance((xs, ys),(secondary_offset[0], secondary_offset[1]))
                    in_secondary_plume = PlumeModel.InPlume(xs,ys,u,1.,a,plume_factor = f_plume,xmax=x_max)
                    in_plume = in_plume or in_secondary_plume
                    
                    in_secondary_background = PlumeModel.InBackground(xs,ys,secondary_dist,u,1.,a,**bg_kwargs)
                    in_background = in_background and in_secondary_background
                    
            if in_plume:
                plume_data.append(full_file,i)
            elif in_background:
                background_data.append(full_file,i)
            else:
                else_data.append(full_file,i)
        else:
            failed_quality_data.append(full_file, i)
            
    max_dist = Geometry.CoordGeom(wind).distance(lat0, lon0, lat0+delta_lat, lon0)
    min_dist = -Geometry.CoordGeom(wind).distance(lat0, lon0, lat0-delta_lat, lon0)
    background_mean = numpy.mean(background_data[co2])
    
    print "Background mean:",background_mean
    
    ticks_plus = numpy.append(numpy.arange(0,plot_max,50),[plot_max])
    ticks_minus = sorted(-1*numpy.append(numpy.arange(50,plot_min,50),[plot_min]))
    
    dist_ticks = numpy.append(ticks_minus,ticks_plus)
    
    fig = plt.figure(figsize = _fig_size)
    ax1=fig.add_subplot(111)
    ax1.scatter(plume_data[co2], plume_data.retrieval_latitude, color=_plume_colour, s=_size, label=_plume_lbl)
    ax1.scatter(background_data[co2], background_data.retrieval_latitude, color=_bg_colour, s=_size, label=_bg_lbl)
    ax1.scatter(else_data[co2], else_data.retrieval_latitude, color=_other_colour, s=_size, label=_other_lbl)
    ax1.scatter(failed_quality_data[co2], failed_quality_data.retrieval_latitude, color=failed_quality_color, s=_size, label=_qual_lbl)
    ax1.plot([background_mean,background_mean], [-plot_min,plot_max], color=_bg_mean_colour)
    ax1.set_ylim(lat_min, lat_max)
    ax1.set_xlim(xco2_min, xco2_max)
    ax1.set_ylabel('Distance from source (km)',fontsize=labelfont, labelpad=leftlabelpad, fontname=Formats.globalfont)
    ax1.set_xlabel('Xco$_2$ (ppm)',fontsize=labelfont, fontname=Formats.globalfont)
    ax1.set_xticks(numpy.linspace(xco2_min,xco2_max,5))
    ax1.plot(background_mean,weighted_avg_lat,marker='.',color=_source_colour,markersize=_source_markersize, lw=5)
    ax1.set_title('Background: %s ppm' % (Formats.ppmformat % background_mean), fontsize=titlefont, fontname=Formats.globalfont)

    ax2 = ax1.twinx()
    ax1.tick_params(labelsize=ticklabelfont)
    ax2.tick_params(labelsize=ticklabelfont)
    ax2.set_ylim(-plot_min,plot_max)
    if show_latitude:
        ax2.set_ylabel('Latitude ($^{\circ}$N)',fontsize=labelfont, labelpad=rightlabelpad, fontname=Formats.globalfont)
    ax2.set_yticks(dist_ticks)
    ax2.set_ylim(-plot_min,plot_max)
    ax2.tick_params('y', left=True, labelleft=True, right=False, labelright=False)
    
    if show_latitude:
        ax1.tick_params('y',left=False, right=True, labelleft=False, labelright=True)
    else:
        ax1.tick_params('y',left=False, right=False, labelleft=False, labelright=False)
        ax1.set_yticks([])
    Formats.set_tickfont(ax1)
    Formats.set_tickfont(ax2)
    plt.subplots_adjust(**_subplot_adjustments)
    plt.savefig(file_name, dpi=_dpi, bbox_inches='tight')
    plt.close()