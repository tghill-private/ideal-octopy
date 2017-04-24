"""
Reads the weekly factors from the file "factors"
"""

import os

import numpy as np

module_dir = os.path.realpath(os.path.dirname(__file__))

factor_file = os.path.join(module_dir, 'factors')

def initialize():
    with open(factor_file, 'r') as data:
        factors = np.array([float(x.strip()) for x in data.readlines()])
    return factors

factors = initialize()

def get_week(date):
    numday = int(date.strftime('%j'))
    numweek = int(numday//7)
    return numweek