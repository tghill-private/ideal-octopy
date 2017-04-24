"""
Module arrtools provides tools for manipulating numpy arrays
"""

import numpy as np

def get_strength(arr):
    """Calculates 'srength' of noise of array arr.
    
    Noise strength is the standard deviation of
    the noisy array.
    """
    return np.std(arr)

def renorm(arr, strength):
    """Renormalizes the array arr to strength.
    
    Calculates the noise strength of arr, 
    and multiplies it by a constant such that the
    resulting array has the indicated strength.
    """
    if (arr==0).all():
        return arr
    else:
        return arr*(strength/get_strength(arr))
    
def center(arr):
    """Shifts an array so mean(arr)=0"""
    return arr - np.mean(arr)

def average(array,resolution):
    """Averages an array in resolution sized chunks.
    
    Takes the given array, and averages (resolution, resolution)
    rows and columns together, replacing each value in that
    subarray with the average value.
    
    Assumes the array is compatible dimensions
    """
    rows, cols = array.shape
    avg=np.zeros(array.shape)
    for row in np.arange(rows//resolution):
        rowmin = row*resolution
        rowmax = (row+1)*resolution
        for col in np.arange(cols//resolution):
            colmin = col*resolution
            colmax = (col+1)*resolution
            avg[rowmin:rowmax,colmin:colmax] = np.mean(array[rowmin:rowmax,colmin:colmax])
    return avg

def reduce(arr, factor):
    """Reduces the size of an array by factor times.
    
    Slices the array arr taking factor sized steps. If the
    input array arr has shape (400, 400) and factor=4, the
    returned array will have shape (100, 100)
    """
    return arr[::factor, ::factor]