"""
PlotOverpasses.py

This module makes maps of OCO-2 data in Google Earth KML format.

Function Plot(overpass, filename, **kwargs) makes a KML file,
saved as filename
"""

import sys

import PST
import KML
import os
import PlumeModel
import Colours
import Overpasses
import Sources
import numpy
import Geometry
import Units
import File

valid_winds = ["Average", "ECMWF", "ECMWF_old", "MERRA", "GEM"]

def Plot(overpass, filename, min_xco2=KML.default_cmin, max_xco2=KML.default_cmax, secondary_sources=[], arrow_scale=0.02, stability="new", wind_source="Average", wind_adjustment=0., f_plume=0.10, f_background=0.01, offset=3.e3, y_max_positive=50.e3, y_max_negative=50.e3, y_min_positive=0., y_min_negative=0., direction='y', x_max=75.e3, snr_strong_co2_min=None, chi_squared_max=None, albedo_min=None, albedo_max=None, outcome_flags={1,2}, surface_pressure_min=None, surface_pressure_max=None, lon_thresh=0.5, lat_thresh=0.5, bias_correction='corrected', npoints=500, width=0.5, height=None, labelsize=Colours.default_fontsize, x=0.05, wind_arrow_sources=['MERRA', 'ECMWF', 'GEM', 'Average']):
    """Creates a KML file for an overpass with parameters as specified.
    
    If xco2 limits are default values, no new colour bar is made.
    Otherwise, will make a new colour bar and save it alongside the
    kml on the server.
    
    Parameters for defining the plume and background are included because
    the extended data for each polygon contains a flag for whether each
    point is in the plume, in the background, or in neither.
    
    Polygons are plotted for 'npoints' points on either side
    of the box defined by the lat and lon thresholds.
    """
    print "Making KML for",overpass.info
    if overpass.FullFile=="":
        raise ValueError("Corrupt overpass file")

    # Bundle together arguments that need to be passed to plume model functions
    # For determining background:
    bg_kwargs = {'background_factor':f_background,
                'ymax_positive':y_max_positive,
                'ymax_negative':y_max_negative,
                'ymin_negative':y_min_negative,
                'ymin_positive':y_min_positive,
                'offset':offset,
                'sign':direction
            }
    # For determining in plume points:
    plume_kwargs = {'plume_factor':f_plume,
                    'xmax':x_max
                }
    
    # Args to pass to full_file.quality(i,**kwargs) method
    quality_args = {'chi_squared_max':chi_squared_max,
                    'snr_strong_co2_min':snr_strong_co2_min,
                    'albedo_min':albedo_min,
                    'albedo_max':albedo_max,
                    'outcome_flags':outcome_flags,
                    'surface_pressure_min':surface_pressure_min,
                    'surface_pressure_max':surface_pressure_max
                    }
    
    # parse bias_correction argument
    if bias_correction not in File.allowed_bias_correction:
        type_err = "'bias_correction' argument must be one of %s"
        raise TypeError(type_err % ', '.join(File.allowed_bias_correction))
        
    # The co2 variable to read; ex, 'corrected_xco2', 'S31_xco2'
    co2 = bias_correction + "_xco2"
    try:
        wind = getattr(overpass,wind_source)
    except AttributeError:
        raise AttributeError("'wind_source' must be one of %s" % ', '.join(valid_winds))
    
    # make arrow_lat, arrow_lon the average lat, lon weighted by emissions
    if secondary_sources:
        secondary_lats = [second.lat for second in secondary_sources]
        secondary_lons = [second.lon for second in secondary_sources]
        all_lats = [overpass.lat] + secondary_lats
        all_lons = [overpass.lon] + secondary_lons
        all_emissions = [overpass.get_emissions()(Units._model_units)] + \
            [second.get_emissions(overpass)(Units._model_units) for second in secondary_sources]
        arrow_lat = numpy.average(all_lats, weights=all_emissions)
        arrow_lon = numpy.average(all_lons, weights=all_emissions)
        print "Using coordinate ({0}, {1}) for wind arrows".format(arrow_lat, arrow_lon)
    else:
        arrow_lat, arrow_lon = overpass.lat, overpass.lon
 
    # Use KML module to make the KML
    kml_description = overpass.strftime(KML.modis_description_fmt)
    Map = KML.KML(description=kml_description)
    oco2_name = "OCO-2 Data"
    oco2_description = "Data from OCO-2 v7 Full Files with '%s' "\
    "bias correction" % bias_correction
    
    OCO2_folder = KML.Folder(oco2_name, oco2_description)
    Map.add_folder(OCO2_folder)
    warn_level_folders = {} # dictionary to be able to update the folders
    for wl in range(21):
        folder_name = "Warn Level %d" % wl
        folder_description = "Lite File Warn Level %d" % wl
        folder = KML.Folder(folder_name, folder_description)
        OCO2_folder.add_object(folder)
        warn_level_folders[wl]=folder
        
    wind_arrows = KML.Overlay.wind_arrow(overpass,lat=arrow_lat,
                                         lon=arrow_lon,size=arrow_scale,
                                         sources=wind_arrow_sources)
    height = height if height else (1.1/5.)*width
    cbar = Colours.colour_bar('', cmin=min_xco2, cmax=max_xco2, fontsize=labelsize)
    colour_scale = KML.Overlay.colour_scale(cbar, width=width, height=height, x=x)
    Map.add_object(wind_arrows)
    Map.add_object(colour_scale)
    
    print('Opening Full File; Performing Bias Correction')
    full_file = File.full(overpass)
    lite_file = File.lite(overpass)
    
    # warn_dict maps a sounding id to a warn level
    warn_dict = {lite_file.sounding_id[n]:lite_file.warn_level[n]
                                    for n in range(len(lite_file))}
    
    lon = overpass.lon
    lat = overpass.lat
    
    close_indices = []
    for i in range(len(full_file)):
        lon_i = full_file.retrieval_longitude[i]
        lat_i = full_file.retrieval_latitude[i]
        dlon = abs(lon_i - overpass.lon)%360
        dlat = abs(lat_i - overpass.lat)%360
        if dlon<=lon_thresh and dlat<=lat_thresh:
          close_indices.append(i)
        i+=1
    
    # (k_min, k_max) are limits on what points to plot
    k_min = max(0,close_indices[0]-npoints)
    k_max = min(len(full_file),close_indices[-1]+npoints)
    
    # plume-model parameters
    u = wind.speed
    F = 1.0 # actual emissions are not important for background
    a = overpass.a if stability=="new" else overpass.a_old
    
    x_offset, y_offset = full_file.get_offset(overpass, wind)
    secondary_offsets = full_file.get_secondary_offset(overpass, wind,
                                    secondary_sources=secondary_sources)
    
    print('Adding polygons to KML File')
    count_plume_points = 0
    count_bg_points = 0
    for k in range(k_min,k_max):
        lats = full_file.retrieval_vertex_latitude[k,0,:]
        lons = full_file.retrieval_vertex_longitude[k,0,:]
        sounding_xco2 = full_file.corrected_xco2[k]
        sounding_id = full_file.id[k]
        sounding_lat = full_file.retrieval_latitude[k]
        sounding_lon = full_file.retrieval_longitude[k]
        
        sounding_colour = Colours.Colour(sounding_xco2, vmin=min_xco2,
                                                        vmax=max_xco2)
        
        if sounding_id in warn_dict:
            warn_level = warn_dict[sounding_id]
        else:
            warn_level=20
        
        point = Geometry.CoordGeom(wind)
        sounding_x, sounding_y = point.coord_to_wind_basis(lat, lon, 
                                                    sounding_lat, sounding_lon)
        
        data = KML.Data()
        data.get_data(k, full_file)
        wl_data = data.add_new_data('Warn Level',warn_level)
        posn_data = data.add_new_data('Wind Basis Coord',(sounding_x,sounding_y))
        
        data.add_new_data('Full File', os.path.split(overpass.FullFile)[1])
        data.add_new_data('Lite File', os.path.split(overpass.LiteFile)[1])
        data.add_new_data('Observation Mode', overpass.observation_mode)
        data.add_new_data('Latitude', sounding_lat)
        data.add_new_data('Longitude', sounding_lon)
        
        dist = ((sounding_x-x_offset)*(sounding_x-x_offset) + 
                (sounding_y-y_offset)*(sounding_y-y_offset))**0.5
        
        in_plume = PlumeModel.InPlume(sounding_x, sounding_y, u, F, a,
                                      **plume_kwargs)
        in_background = PlumeModel.InBackground(sounding_x, sounding_y, dist,
                                                u, F, a, **bg_kwargs)
        for (ind, second) in enumerate(secondary_sources):
            x0,y0 = secondary_offsets[ind]
            xs,ys = point.coord_to_wind_basis(second.lat, second.lon, sounding_lat, sounding_lon)
            second_dist = point.cartesian_distance((xs,ys),(x0,y0))
            in_secondary_plume = PlumeModel.InPlume(xs, ys, u, 1.0, a, **plume_kwargs)
            in_secondary_bg = PlumeModel.InBackground(xs, ys, second_dist, u, 1.0, a, **bg_kwargs)
            in_plume = in_plume or in_secondary_plume
            in_background = in_background and in_secondary_bg
        
        if in_plume:
            model_status = KML.DataPoint('Notes','In Plume Point')
            if full_file.quality(k, **quality_args):
                count_plume_points+=1
        elif in_background:
            model_status = KML.DataPoint('Notes','Background Point')
            if full_file.quality(k, **quality_args):
                count_bg_points+=1
        else:
            model_status = KML.DataPoint('Notes','None')
        data.add_data_field(model_status)
        
        quality = full_file.quality(k, **quality_args)
        data.add_new_data("Quality Check", str(quality))
        poly_col = sounding_colour.cformat(Colours.Colour.GE)
        sounding_polygon = KML.Polygon(lats, lons, sounding_id, poly_col)
        sounding_polygon.add_data(data)
        warn_level_folders[warn_level].add_object(sounding_polygon)

    Map.write(filename)
    print "KML saved as", filename
    print "Done Overpass"
    
if __name__ == "__main__":
    from Overpasses import *
    Plot(Gavin20150730, "Gavin_new_kml_test.kmz")