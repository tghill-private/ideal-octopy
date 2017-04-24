"""
    ModelFit.py
    
    1 February 2017:
    * updated best_wind function to take same parameters, calculate background,
    etc. the same as Model function. This way any correlation given from the
    best_wind function will be the same as the Model function. Added optional
    parameter to run Model with the parameters after searching for the best
    wind direction
"""

import math

import numpy

import sys
import PST
import PlumeModel
import Geometry
import Units
import ModelFunctions
import XML
import File

def Model(overpass,f_plume=0.10,f_background=0.01,offset=3000.,y_max_positive=50.e3,y_max_negative=50.e3,y_min_negative=0.,y_min_positive=0., direction='y', wind_adjustment=0.,wind_sources=['Average'],smooth=False,surface_stability=True,stability="new", temporal_factors=False, bias_correction='corrected',LocalBackground=PlumeModel.InBackground,LocalInPlume=PlumeModel.InPlume, co2_source='xco2', custom_wind=None, snr_strong_co2_min=None, chi_squared_max=None, albedo_min=None, albedo_max = None, outcome_flags={1,2}, surface_pressure_max=None, surface_pressure_min=None, background_average=None, secondary_sources = False, fixed_secondary_sources=[], x_max=75.e3,scatter_plot=False,force_winds = None, units=Units.output_units, sza_adjustments = True, weighted=False, uncertainty=True):
    """Computes model enhancements for an overpass, and compares them to observed data.
    
    The behaviour is specified by the many default arguments. This function
    does everything needed including calculating model enhancements, but
    delegates the actual comparison to the ModelFunctions module. See
    the keyword list document for an explanation of the optional arguments
    """
    ## First all the default arguments are dealt with, and then move on to actually classifying data and fitting model
    
    # Args to pass to full_file.quality(i,**kwargs) method
    quality_args = {'chi_squared_max':chi_squared_max,
                    'snr_strong_co2_min':snr_strong_co2_min,
                    'albedo_min':albedo_min,
                    'albedo_max':albedo_max,
                    'outcome_flags':outcome_flags,
                    'surface_pressure_min':surface_pressure_min,
                    'surface_pressure_max':surface_pressure_max
                    }
    
    bg_kwargs = {'background_factor':f_background,
                'ymax_positive':y_max_positive,
                'ymax_negative':y_max_negative,
                'ymin_negative':y_min_negative,
                'ymin_positive':y_min_positive,
                'offset':offset,
                'sign':direction
            }
    
    plume_kwargs = {'xmax':x_max,
                    'plume_factor':f_plume
                }
    if secondary_sources == False:
        secondary = []
        secondary_sources = False
    elif secondary_sources == True:
        secondary = overpass.source.secondary
        secondary_sources = True
    elif hasattr(secondary_sources, "__iter__"):
        secondary = secondary_sources
        secondary_sources = True
    else:
        raise TypeError("Invalid argument '{}' for secondary_sources.\
        Must be True, False, or iterable collection of PointSources".format(secondary_sources))
        
    # bias correction:
    if bias_correction not in File.allowed_bias_correction:
        raise ValueError("bias correction must be one of {0}; given {1}".format(', '.join(File.allowed_bias_correction), bias_correction))
    
    if not (co2_source=='xco2' or co2_source=='co2_column'):
        raise ValueError("co2_source must be one of 'xco2' or 'co2_column' not '{0}'".format(co2_source))
    co2 = "{0}_{1}".format(bias_correction,co2_source)
    if smooth:
        co2 = 'smoothed_' + co2

    
    # get emissions for the overpass and make sure they're in g/s
    F = overpass.get_emissions(temporal_factors=temporal_factors)
    F.convert(Units._model_units)
    
    # atmospheric stability parameter
    if surface_stability==True:
        if stability == "new":
            a = overpass.a
        elif stability == "old":
            a = overpass.a_old
    elif surface_stability==False:
        a = overpass.a_elevated
    else:
        a = surface_stability
    
    secondary_emissions = [second.get_emissions(overpass)(Units._model_units) for second in secondary]
    all_emissions = [F(units)] + [em(units) for em in secondary_emissions]
    total_emissions = F(units)
    for second in secondary_emissions:
        total_emissions+=second(units)
    emissions_info = ', '.join([str(emi) for emi in all_emissions])
    sources_info = ', '.join([src for src in [overpass.short]+[s.short for s in secondary]])
    
    print "Using reported emissions:", emissions_info
    print "For sources:", sources_info
    print "Total emissions:", total_emissions
    print "Using atmospheric stability parameter a={0}".format(a)
    
    print "Opening and reading full file"
    full_file = File.full(overpass)
    
    # force_winds is an override for forcing the model to run with a given list of Wind instances.
    # Useful for running the model with many wind adjustments
    if force_winds is None:
        all_winds = PST.AllWinds(overpass)
        try:
            WindSources,wind_labels = all_winds.parse(wind_sources)
            WindSources = [wnd.rotate(wind_adjustment) for wnd in WindSources]
        except Exception as exc:
            WindSources,wind_labels = [], []
            print "Exception raised and ignored:", exc
        
        try:
            custom_winds, custom_labels = all_winds.add_custom(custom_wind)
        except ValueError as ve:
            print "custom_wind value was not valid. See message:", ve
        except Exception as sxc:
            print "Unexpected error occured:", sxc
        else:
            WindSources.extend(custom_winds)
            wind_labels.extend(custom_labels)
    else:
        WindSources = force_winds
        wind_labels = [str(wind) for wind in force_winds]
    
    if sza_adjustments:
        print "Assigning a sign to the sensor zenith angle"
        full_file.sign_zenith_angle(overpass)
    
    # filtered_data has the same fields as full_file but only the points that pass the quality filter
    filtered_data = full_file.filter(**quality_args)
    
    print "Classifying points"
    in_plume_objects = []
    background_objects = []
    model_enhancement_lists = []
    model_alpha_lists = []
    fixed_enhancement_lists = []
    
    for wind in WindSources:
        # set wind.height to the weighted (by emissions) average height
        height_list = [overpass.height]+[source.height for source in secondary]
        mean_height = numpy.average(height_list, weights=all_emissions)
        wind.height = mean_height
        
        plume_data = File.File()
        background_data = File.File()
        model_enhancements = [] # will be column vector [ [V1], [V2], ... ]
        model_alpha = [] # will be matrix A from math docs
        fixed_enhancements = [] # list of enhancements from fixed sources
        
        # we already have a, F determined
        u = wind.speed
        
        # the offset (x,y) in wind basis components from the source to the center plume (highest enhancement)
        x_offset, y_offset = filtered_data.get_offset(overpass,wind)
        
        # same as above offset but for each secondary source
        secondary_offsets = filtered_data.get_secondary_offset(overpass, wind, secondary_sources=secondary)
        
        # emissons of all the fixed secondary sources
        fixed_emissions = [fixed.get_emissions(overpass,temporal_factors=temporal_factors)(Units._model_units) for fixed in fixed_secondary_sources]

        for i in range(len(filtered_data)):
            coordinate = Geometry.CoordGeom(wind)
            x,y = coordinate.coord_to_wind_basis(overpass.lat, overpass.lon, 
                filtered_data.retrieval_latitude[i], filtered_data.retrieval_longitude[i])
            dist = Geometry.CoordGeom.cartesian_distance((x,y),(x_offset, y_offset))
            
            sza = Geometry.SZA(filtered_data,wind)
            
            # check if point is in background or in plume, including secondary sources
            in_background = PlumeModel.InBackground(x,y,dist,u,F,a,**bg_kwargs)
            in_plume = PlumeModel.InPlume(x,y,u,F,a,**plume_kwargs)
            if secondary_sources:
                for ind, secondary_src in enumerate(secondary):
                    SZA_secondary = Geometry.SZA(filtered_data, wind)
                    xs,ys = Geometry.CoordGeom(wind).coord_to_wind_basis(secondary_src.lat,secondary_src.lon,filtered_data.retrieval_latitude[i], filtered_data.retrieval_longitude[i])
                    secondary_dist = Geometry.CoordGeom.cartesian_distance((xs, ys), secondary_offsets[ind])
                    
                    in_secondary_plume = PlumeModel.InPlume(xs,ys,u,1.,a,**plume_kwargs)
                    in_secondary_background = PlumeModel.InBackground(xs,ys,secondary_dist,u,1.,a,**bg_kwargs)
                    
                    # logic for when to consider it in-plume/background with secondary sources
                    in_plume = in_plume or in_secondary_plume
                    in_background = in_background and in_secondary_background
                    
            if in_background:
                background_data.append(filtered_data,i)
                
            if in_plume:
                total_enhancement = 0. #enhancements from all sources
                plume_data.append(filtered_data,i)
                # get enhancement from main source, then add secondary sources
                if sza_adjustments:
                    main_enhancement = sza.V(x,y,u,F,a,i)
                else:
                    main_enhancement = PlumeModel.V(x,y,u,F,a)
                alpha = [main_enhancement/F]
                total_enhancement+=main_enhancement

                for ind,secondary_src in enumerate(secondary):
                    xs,ys = Geometry.CoordGeom(wind).coord_to_wind_basis(secondary_src.lat,secondary_src.lon,filtered_data.retrieval_latitude[i], filtered_data.retrieval_longitude[i])
                    F_secondary = secondary_emissions[ind]
                    
                    if sza_adjustments:
                        secondary_enhancement = sza.V(xs, ys, u, F_secondary, a, i)
                    else:
                        secondary_enhancement = PlumeModel.V(xs, ys, u, F_secondary, a)

                    total_enhancement += secondary_enhancement
                    alpha.append(secondary_enhancement/F_secondary)
                
                model_enhancements.append([total_enhancement])
                model_alpha.append(alpha)
                
                fixed_enhancement = 0.
                for ind, fixed in enumerate(fixed_secondary_sources):
                    xs,ys = Geometry.CoordGeom(wind).coord_to_wind_basis(fixed.lat,fixed.lon,filtered_data.retrieval_latitude[i], filtered_data.retrieval_longitude[i])
                    F_fixed = fixed_emissions[ind]
                    
                    if sza:
                        source_enhancement = sza.V(xs, ys, u, F_fixed, a, i)
                    else:
                        source_enhancement = PlumeModel.V(xs, ys, u, F_fixed, a)
                    fixed_enhancement+=source_enhancement
                    
                fixed_enhancements.append(fixed_enhancement)
        
        in_plume_objects.append(plume_data)
        background_objects.append(background_data)
        model_enhancement_lists.append(numpy.array(model_enhancements))
        model_alpha_lists.append(numpy.array(model_alpha))
        fixed_enhancement_lists.append(numpy.array(fixed_enhancements))
        
        
    all_results = []
    for (k,wind) in enumerate(WindSources):
        print ''
        print wind_labels[k]
        
        defaults = ModelFunctions.results_defaults()
        defaults.co2_attribute = co2
        defaults.co2_name = co2_source
        defaults.output_units = units
        in_plume_objects[k].xco2_uncert = numpy.array(in_plume_objects[k].xco2_uncert)
        
        try:
            results = ModelFunctions.interpret_results(in_plume_objects[k],background_objects[k], model_enhancement_lists[k], model_alpha_lists[k],fixed_enhancement_lists[k], overpass,wind,defaults,float(total_emissions),weights=weighted,background_average=background_average, uncertainty=uncertainty)
            # results is tuple (scale factor, estimated emissions, number of plume points, correlation)
        
        except:
            results = defaults.null_value
            # print "An exception was raised: see message following"
            # print exc
            raise
            
        all_results.append(results)
        
        if secondary_sources:
            print '\nEmissions are ordered as', ', '.join([overpass.short] + map(lambda s: s.short,secondary))
        print ''
    
    # make scatter plot if it's asked for, using last wind source
    if scatter_plot:
        if type(scatter_plot)!=str:
            raise TypeError("Keyword scatter_plot must be a string corresponding to a valid path. Given '{0}'".format(scatter_plot))
        
        try:
            sc_location = ModelFunctions.make_scatter_plot(numpy.array((model_enhancement_lists[k])/numpy.mean(background_objects[k].k)).flatten(), in_plume_objects[k][co2], scatter_plot)
        except:
            raise
        else:
            print "Scatter plot made and saved as {0}".format(scatter_plot)

    return all_results
    

def best_winds(overpass, adjust_min=-10, adjust_max=10, tolerance=2.5,f_plume=0.10,f_background=0.01,offset=3000.,y_max_positive=50.e3,y_max_negative=50.e3,y_min_negative=0.,y_min_positive=0.,direction='y',wind_adjustment=0.,smooth=False,surface_stability=True,stability="new",temporal_factors=False,bias_correction='corrected',LocalBackground=PlumeModel.InBackground,LocalInPlume=PlumeModel.InPlume,co2_source='xco2', snr_strong_co2_min=None, chi_squared_max=None, albedo_min=None, albedo_max = None,outcome_flags={1,2}, surface_pressure_min=None, surface_pressure_max=None, background_average=None,secondary_sources = False, fixed_secondary_sources=[], x_max=75.e3,scatter_plot=False,force_winds = None, units=Units.output_units, sza_adjustments = True, output_file=False, weighted=False,run_model=True):
    """Searches for the wind adjustment that gives the highest correlation.
    
    Searches between increasingly narrow wind adjustments for the wind
    direction that gives the highest correlation. It prints out
    the adjustment, and then runs the full model function with this
    best adjustment value (if run_model==True).
    
    Searches for 10 degrees by default outside the limits set
    by ECMWF and MERRA. This can be adjsuted with the adjust_min and
    adjust_max arguments. tolerance is the difference between the
    outside limits of adjusting the wind at which to consider
    the search accurate enough and return the value.
    """
    merra = overpass.MERRA
    ecmwf = overpass.ECMWF
    average_wind= overpass.Average

    direction_min = min(merra.bearing, ecmwf.bearing) + adjust_min
    direction_max = max(merra.bearing, ecmwf.bearing) + adjust_max
    
    starting_wind_speed = average_wind.speed
    
    adjust_min = direction_min - average_wind.bearing
    adjust_max = direction_max - average_wind.bearing
    
    first_adjustments = numpy.linspace(adjust_min,adjust_max,9)

    ## First all the default arguments are dealt with, and then move on to actually classifying data and fitting model
    
    # Args to pass to full_file.quality(i,**kwargs) method
    quality_args = {'chi_squared_max':chi_squared_max,
                    'snr_strong_co2_min':snr_strong_co2_min,
                    'albedo_min':albedo_min,
                    'albedo_max':albedo_max,
                    'outcome_flags':outcome_flags,
                    'surface_pressure_min':surface_pressure_min,
                    'surface_pressure_max':surface_pressure_max
                    }
    
    bg_kwargs = {'background_factor':f_background,
                'ymax_positive':y_max_positive,
                'ymax_negative':y_max_negative,
                'ymin_negative':y_min_negative,
                'ymin_positive':y_min_positive,
                'offset':offset,
                'sign':direction
            }
    
    plume_kwargs = {'xmax':x_max,
                    'plume_factor':f_plume
                }
    
    # if secondary_sources is passed a collection of sources, it uses those as the secondary sources
    if hasattr(secondary_sources, "__iter__"):
        secondary = secondary_sources
    
    elif secondary_sources==True:
        secondary = overpass.source.secondary
    
    else:
        secondary = []
    
    # get emissions for the overpass and make sure they're in g/s
    F = overpass.get_emissions(temporal_factors=temporal_factors)
    F.convert(Units._model_units)
    secondary_emissions = [src.get_emissions(overpass, temporal_factors=temporal_factors)(Units._model_units) for src in secondary]
    all_emissions = [F] + secondary_emissions
    
    # atmospheric stability parameter
    if surface_stability==True:
        if stability == "new":
            a = overpass.a
        else:
            a = overpass.a_old
    elif surface_stability==False:
        a = overpass.a_elevated
    else:
        a = surface_stability
    print "Using reported emissions: {0}".format(F.convert_cp(units))
    print "Using atmospheric stability paramter a={0}".format(a)
    print("Opening and reading full file")
    full_file = File.full(overpass)

    # bias correction:
    if bias_correction not in File.allowed_bias_correction:
        raise ValueError("bias correction must be one of {0}; given {1}".format(', '.join(File.allowed_bias_correction), bias_correction))
    
    if not (co2_source=='xco2' or co2_source=='co2_column'):
        raise ValueError("co2_source must be one of 'xco2' or 'co2_column' not '{0}'".format(co2_source))
    co2 = "{0}_{1}".format(bias_correction,co2_source)
    if smooth:
        co2 = 'smoothed_' + co2
        
    if sza_adjustments:
        print "Assigning a sign to the sensor zenith angle"
        full_file.sign_zenith_angle(overpass)
    
    # filtered_data has the same fields as ModelData but only the points that pass the quality filter
    filtered_data = full_file.filter(**quality_args)

    print "Adjusting the winds"
    delta = adjust_max-adjust_min
    while delta>tolerance:
        correlations = []
        adjustments = numpy.linspace(adjust_min,adjust_max,9)
        WindSources = [average_wind.rotate(x) for x in adjustments]
        print "Adjustments"
        print adjustments
        
        in_plume_objects = []
        background_objects = []
        model_enhancement_lists = []
        model_alpha_lists = []
        fixed_enhancement_lists = []

        for wind in WindSources:
            height_list = [overpass.height]+[source.height for source in secondary]
            mean_height = numpy.average(height_list, weights=all_emissions)
            wind.height = mean_height
            
            plume_data = File.File()
            background_data = File.File()
            model_enhancements = []
            model_alpha = []
            fixed_enhancements = []
            
            # we already have a, F determined
            u = wind.speed
            
            # the offset (x,y) in wind basis components from the source to the center plume (highest enhancement)
            x_offset, y_offset = filtered_data.get_offset(overpass,wind)
            
            secondary_offsets = filtered_data.get_secondary_offset(overpass, wind, secondary_sources=secondary)
            fixed_emissions = [fixed.get_emissions(overpass,temporal_factors=temporal_factors)(Units._model_units) for fixed in fixed_secondary_sources]

            for i in range(len(filtered_data)):
                coordinate = Geometry.CoordGeom(wind)
                x,y = coordinate.coord_to_wind_basis(overpass.lat,overpass.lon,filtered_data.retrieval_latitude[i], filtered_data.retrieval_longitude[i])
                dist = Geometry.CoordGeom.cartesian_distance((x,y),(x_offset, y_offset))
                sza = Geometry.SZA(filtered_data,wind)
                
                in_background = PlumeModel.InBackground(x,y,dist,u,F,a,**bg_kwargs)
                in_plume = PlumeModel.InPlume(x,y,u,F,a,**plume_kwargs)
                if secondary_sources:
                    for ind, secondary_src in enumerate(secondary):
                        SZA_secondary = Geometry.SZA(filtered_data, wind)
                        xs,ys = Geometry.CoordGeom(wind).coord_to_wind_basis(secondary_src.lat,secondary_src.lon,filtered_data.retrieval_latitude[i], filtered_data.retrieval_longitude[i])
                        secondary_offset = secondary_offsets[ind]
                        secondary_dist = Geometry.CoordGeom.cartesian_distance((xs, ys),secondary_offset)
                        in_secondary_plume = PlumeModel.InPlume(xs,ys,u,1.,a,**plume_kwargs)
                        in_plume = in_plume or in_secondary_plume
                        
                        in_secondary_background = PlumeModel.InBackground(xs,ys,secondary_dist,u,1.,a,**bg_kwargs)
                        in_background = in_background and in_secondary_background
                        
                if in_background:
                    background_data.append(filtered_data,i)
                    
                if in_plume:
                    total_enhancement = 0. #enhancements from all sources
                    plume_data.append(filtered_data,i)
                    # get enhancement from main source, then add secondary sources
                    if sza_adjustments:
                        main_enhancement = sza.V(x,y,u,F,a,i)
                    else:
                        main_enhancement = PlumeModel.V(x,y,u,F,a)
                    alpha = [main_enhancement/F]
                    total_enhancement+=main_enhancement

                    for ind,secondary_src in enumerate(secondary):
                        xs,ys = Geometry.CoordGeom(wind).coord_to_wind_basis(secondary_src.lat,secondary_src.lon,filtered_data.retrieval_latitude[i], filtered_data.retrieval_longitude[i])
                        F_secondary = secondary_emissions[ind]
                        
                        if sza_adjustments:
                            secondary_enhancement = sza.V(xs, ys, u, F_secondary, a, i)
                        else:
                            secondary_enhancement = PlumeModel.V(xs, ys, u, F_secondary, a)

                        total_enhancement += secondary_enhancement
                        alpha.append(secondary_enhancement/F_secondary)
                    
                    model_enhancements.append([total_enhancement])
                    model_alpha.append(alpha)
                        
                    fixed_enhancement = 0.
                    for ind, fixed in enumerate(fixed_secondary_sources):
                        xs,ys = Geometry.CoordGeom(wind).coord_to_wind_basis(fixed.lat,fixed.lon,filtered_data.retrieval_latitude[i], filtered_data.retrieval_longitude[i])
                        F_fixed = fixed_emissions[ind]
                        if sza:
                            source_enhancement = sza.V(xs, ys, u, F_fixed, a, i)
                        else:
                            source_enhancement = PlumeModel.V(xs, ys, u, F_fixed, a)
                        fixed_enhancement+=source_enhancement
                        
                    fixed_enhancements.append(fixed_enhancement)
            
            in_plume_objects.append(plume_data)
            background_objects.append(background_data)
            model_enhancement_lists.append(numpy.array(model_enhancements))
            model_alpha_lists.append(numpy.array(model_alpha))
            fixed_enhancement_lists.append(numpy.array(fixed_enhancements))
        
        for (k,wind) in enumerate(WindSources):
            if len(in_plume_objects[k])<=2:
                correlations.append(0)
            else:
                try:
                    fixed_enhance = fixed_enhancement_lists[k]/numpy.mean(background_objects[k].k)
                    cor = numpy.corrcoef(in_plume_objects[k][co2]-fixed_enhance,model_enhancement_lists[k].flatten())[0,1]
                except:
                    raise
                correlations.append(cor)
        
        max_cor = max(correlations)
        max_index = correlations.index(max_cor)
        
        adjust_max = adjustments[min(8,max_index+3)]
        adjust_min = adjustments[max(0,max_index-3)]
        delta = abs(adjust_max - adjust_min)

    print "Maximum Correlation: {0}; with wind adjustment {1} relative to the average\n\n".format(max_cor, adjustments[max_index])
    
    if run_model:
        print "Running the model with the best wind..."
        
        return Model(overpass,f_plume=f_plume,f_background=f_background,offset=offset,y_max_positive=y_max_positive,y_max_negative=y_max_negative,y_min_negative=y_min_negative,y_min_positive=y_min_positive,direction=direction,wind_adjustment=wind_adjustment,wind_sources=None,smooth=smooth,surface_stability=surface_stability,stability=stability,temporal_factors=temporal_factors,bias_correction=bias_correction,LocalBackground=LocalBackground,LocalInPlume=LocalInPlume,co2_source=co2_source, snr_strong_co2_min=snr_strong_co2_min, chi_squared_max=chi_squared_max, albedo_min=albedo_min, albedo_max=albedo_max, outcome_flags=outcome_flags, background_average=background_average,secondary_sources=secondary,x_max=x_max,scatter_plot=scatter_plot,force_winds=[WindSources[max_index]], units=units, sza_adjustments=sza_adjustments, weighted=weighted, fixed_secondary_sources=fixed_secondary_sources)

        
kw_val_err = "Keyword not found or dictionary values are not consistent length"
len_error = "Value for keyword %s not matching length"
def iterable(obj):
    return hasattr(obj, "__iter__")
    
def dict_split(d):
    if len(d.values())==0:
        num_params = 1
        return [d]
    else:
        num_params = len(d.values()[0])
        split_dictionaries = [{} for p in range(num_params)]
        for (kw,val) in d.iteritems():
            if len(val)!=num_params:
                raise ValueError(len_error % kw)
            for (index, value) in enumerate(val):
                split_dictionaries[index][kw]=value
    
        return split_dictionaries
    
def ModelUncertainty(overpass, **kwargs):
    """Calculates the uncertainty in the model results.
    
    Uses an ensemble of different parameters, and defines the
    uncertainty as the standard deviation of the total enhancements
    estimated across the different parameters.
    
    It considers the plume uncertainty by varying the bias correction,
    and the background uncertainty by varying any of the background
    parameters.
    
    This function splits the given keyword arguments into different
    sets of arguments for the plume/background, and runs the model
    for each set of values. It is selective in the results it prints
    compared to the full Model function.
    """

    print overpass.info
    constant_bg_values = {}
    varying_bg_values = {}
    constant_plume_values = {}
    varying_plume_values = {}
    current_other_kw = {}
    
    defaults = XML.get_model_defaults()
    
    for (keyword, value) in kwargs.iteritems():
        if keyword in defaults.background:
            if iterable(value):
                varying_bg_values[keyword] = value
            else:
                constant_bg_values[keyword] = value
        elif keyword in defaults.plume:
            if iterable(value):
                varying_plume_values[keyword] = value
            else:
                constant_plume_values[keyword] = value
        elif keyword in defaults.other:
            current_other_kw[keyword] = value
        else:
            raise KeyError('Unexpected keyword "%s" encountered' % keyword)
    
    if len(varying_bg_values.values())>0:
        num_bg_sets = len(varying_bg_values.values()[0])
    else:
        num_bg_sets = 1
        
    if len(varying_plume_values.values())>0:
        num_plume_sets = len(varying_plume_values.values()[0])
    else:
        num_plume_sets = 1
    
    print "Using %d background parameter sets" % num_bg_sets
    print "Using %d plume parameter sets" % num_plume_sets
    print ""
    
    bg_sets = dict_split(varying_bg_values)
    plume_sets = dict_split(varying_plume_values)
    
    main_kwargs = current_other_kw.copy()
    main_kwargs.update(constant_plume_values)
    main_kwargs.update(constant_bg_values)
    main_kwargs.update(bg_sets[0])
    main_kwargs.update(plume_sets[0])
    
    print "Main Optional Parameters Specified:"
    for (key,val) in main_kwargs.iteritems():
        print key, val
    
    bg_results = []
    plume_results = []
    
    for set in bg_sets:
        if set!={}:
            complete_kwargs = main_kwargs.copy()
            complete_kwargs.update(set)
            complete_kwargs.update(plume_sets[0])
            print "\nUpdating Background Values:"
            for (key,val) in set.iteritems():
                print key, val
            print "\nModel Output:"
            all_emissions = Model(overpass, uncertainty=False, **complete_kwargs)[0][1]
            total_emissions = float(all_emissions[0])
            for emi in all_emissions[1:]:
                total_emissions += float(emi)
            bg_results.append(total_emissions)
        
    for set in plume_sets:
        if set!={}:
            complete_kwargs = main_kwargs.copy()
            complete_kwargs.update(set)
            complete_kwargs.update(bg_sets[0])
            print "\nUpdating Plume Values:"
            for (key,val) in set.iteritems():
                print key, val
            print "\nModel Output:"
            all_emissions = Model(overpass, uncertainty=False, **complete_kwargs)[0][1]
            total_emissions = float(all_emissions[0])
            for emi in all_emissions[1:]:
                total_emissions += float(emi)
            plume_results.append(total_emissions)
        
    
    print "\nCalculating Uncertainties:"
    wind_uncert = abs((overpass.MERRA.speed - overpass.ECMWF.speed)/(overpass.MERRA.speed + overpass.ECMWF.speed))
    
    bg_std = numpy.std(bg_results)
    plume_std = numpy.std(plume_results)
    
    print "Estimated Emissions for background parameters:", bg_results
    print "Background Standard Deviation:", bg_std
    print "Estimated Emissions for different bias correction:", plume_results
    print "Plume Standard Deviation:", plume_std
    print "Wind Uncerainty: %s%%" % wind_uncert
    print "Absolute Wind Uncertainty:", wind_uncert*bg_results[0]
