"""
Module Uncertainty.py

Module has a decorator to calculate model uncertainty.

I don't think this is actually useful to be in the production
code, since the decorator definition is really the same
length as the full uncertainty function, and it will just create
confusion including it in the interface module.

It's an interesting curiosity making a decorator
take arguments though.
"""

import numpy

import XML

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
    
def model_key(r):
    all_emissions = r[0][1]
    main_emissions = all_emissions[0]
    total_emissions = float(main_emissions)
    for e in all_emissions[1:]:
        total_emissions+=float(e)
    return total_emissions
    
class uncert(object):
    def __init__(self, key=lambda x:x):
        self.key = key
    
    def __call__(self, func):
        
        def uncertainty_wrapper(*args, **kwargs):
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
            results_key=self.key
            kw_val_err = "Keyword not found or dictionary values are not consistent length"
            len_error = "Value for keyword %s not matching length"
            print args[0].info
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
                    result = results_key(func(*args, **complete_kwargs))
                    bg_results.append(result)
                
            for set in plume_sets:
                if set!={}:
                    complete_kwargs = main_kwargs.copy()
                    complete_kwargs.update(set)
                    complete_kwargs.update(bg_sets[0])
                    print "\nUpdating Plume Values:"
                    for (key,val) in set.iteritems():
                        print key, val
                    print "\nModel Output:"
                    result = results_key(func(*args, **complete_kwargs))
                    plume_results.append(result)
                    
            print "\nCalculating Uncertainties:"
            bg_std = numpy.std(bg_results)
            plume_std = numpy.std(plume_results)
            print "Estimated Emissions for background parameters:", bg_results
            print "Background Standard Deviation:", bg_std
            print "Estimated Emissions for different bias correction:", plume_results
            print "Plume Standard Deviation:", plume_std
        
        return uncertainty_wrapper