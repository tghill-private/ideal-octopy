"""
Module for storing file paths to the data used in the point sources model
"""

import os
from os.path import join


root = '/home/tim/PointSources'

modeldata = join(root, 'ModelData')

overpasses = join(root, 'ModelData/overpasses_updated_merra.csv')

units = join(root, 'ModelData/Units.csv')

unitprefixes = join(root, 'ModelData/UnitPrefixes.csv')

sources = join(root, 'ModelData/EmissionsList.csv')

tccon = join(root, 'ModelData/EmissionsList.csv')

secondary = join(root, 'ModelData/EmissionsListSecondary.csv')

defaults = join(root, 'ModelData/defaults.xml')

daily_emissions = '/home/tim/EmissionsDatabase'

hourly_emissions = '/home/tim/EmissionsDatabase/Hourly'