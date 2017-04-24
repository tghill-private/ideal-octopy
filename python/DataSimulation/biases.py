"""
Dictionaries giving bias parameters to use in data simulation
"""

topography_bias = { 'footprint_bias':0 }

footprint_bias = {'terrain_bias':0}

cloud_mask = {  'footprint_bias':0,
                'terrain_bias':0,
                'cloud_mask':True
}

smplmsk_lft = { 'footprint_bias':0,
                'terrain_bias':0,
                'sample_mask':'swath_mask_left'
}

smplmsk_mid = { 'footprint_bias':0,
                'terrain_bias':0,
                'sample_mask':'swath_mask_middle'
}

smplmsk_rght = {'footprint_bias':0,
                'terrain_bias':0,
                'sample_mask':'swath_mask_right'
}

smplmsk_diag = {'footprint_bias':0, 
                'terrain_bias':0,
                'sample_mask':'swath_mask_diag'
}

interference_bias = {   'footprint_bias':0,
                        'terrain_bias':0,
                        'interference_bias':True
}

wind_bias = {   'footprint_bias':0,
                'terrain_bias':0,
                'wind_bias':35, 
                'calculate_model':True
}

stab_bias = {   'footprint_bias':0,
                'terrain_bias':0,
                'stability_bias':104.0,
                'calculate_model':True
}

combined = {    'footprint_bias':0.001,
                'terrain_bias':0.003,
                'stability_bias':130.0,
                'albedo_bias':True,
                'calculate_model':False
}

windspeed_bias_3 = {    'footprint_bias':0, 
                        'terrain_bias':0,
                        'u':3.
}

windspeed_bias_5 = {    'footprint_bias':0,
                        'terrain_bias':0,
                        'u':5.
}

windspeed_bias_2 = {    'footprint_bias':0,
                        'terrain_bias':0,
                        'u':2.
}

noisestrength_05 = {    'footprint_bias':0,
                        'terrain_bias':0,
                        'noise_strength':0.5
}

noisestrength_15 = {    'footprint_bias':0,
                        'terrain_bias':0,
                        'noise_strength':1.5
}

albedo_bias = { 'footprint_bias':0,
                'terrain_bias':0,
                'albedo_bias':True
}

no_bias = { 'footprint_bias':0, 
            'terrain_bias':0
}

no_bias_renorm = {  'footprint_bias':0,
                    'terrain_bias':0,
                    'renorm':'sqrt'
}

no_bias_constant = {    'footprint_bias':0,
                        'terrain_bias':0,
                        'renorm':'constant',
                        'plot_factor':20
}

biases = [  topography_bias,
            footprint_bias,
            cloud_mask,
            smplmsk_lft,
            smplmsk_mid,
            smplmsk_rght,
            smplmsk_diag,
            interference_bias,
            windspeed_bias_3,
            windspeed_bias_5,
            windspeed_bias_2,
            noisestrength_05,
            noisestrength_15,
            albedo_bias,
            no_bias,
            no_bias_renorm
]
            
bias_names = [  'topography.csv',
                'footprint.csv',
                'cloudmask.csv',
                'samplemask_left.csv',
                'samplemask_mid.csv',
                'samplemask_right.csv',
                'samplemask_diag.csv',
                'interference.csv',
                'windspeed_3.csv',
                'windspeed_5.csv',
                'windspeed_2.csv',
                'noisestrength_0.5.csv',
                'noisestrength_1.5.csv',
                'albedo.csv',
                'defaults.csv',
                'renorm.csv'
]