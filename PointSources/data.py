"""
Module for storing file paths to the data used in the point sources model
"""

import os
from os.path import join

module_path = os.path.dirname(os.path.realpath(__file__))

root = os.path.realpath(os.path.join(module_path, '..'))

modeldata = join(root, 'ModelData')

overpasses = join(root, 'ModelData/overpasses.csv')

units = join(root, 'ModelData/Units.csv')

unitprefixes = join(root, 'ModelData/UnitPrefixes.csv')

sources = join(root, 'ModelData/EmissionsList.csv')

tccon = join(root, 'ModelData/EmissionsList.csv')

secondary = join(root, 'ModelData/EmissionsListSecondary.csv')

defaults = join(root, 'ModelData/defaults.xml')

daily_emissions = '/home/tim/EmissionsDatabase'

hourly_emissions = '/home/tim/EmissionsDatabase/Hourly'

kml_images = join(modeldata, 'KML_Images')