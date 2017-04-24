"""
Module PlumeModel.py

Calculates epected enhancements and classifies points.

Enhancements are calculated using a vertically integrated Gaussian Plume
Model. Points are classified according to the ratio of the expected
enhancement to the on-axis enhancement, and the absolute
distance from the point source.
"""

import numpy as np

# default values
_plume_default = 0.10
_bg_default = 0.01
_xmax_default = 75.e3
y_max_pos_default = 50.e3
y_max_neg_default = 50.e3
y_min_pos_default = 0.
y_min_neg_default = 0.
_offset_default = 3.e3

def V(x, y, u, F, a, y0=0.):
    """Calculates expected enhancement in g/m^2 according to 2D plume model.
    
    Uses 2D Gaussian Plume model for position (x,y) (m), windspeed u (m/s),
    emissions F (g/s), and atmospheric stabiltiy parameter a.
    
    Args:
        x: along-wind distance in meters
        y: across-wind distance in meters
        u: wind-speed at plume-height (m/s)
        F: Source emissions (g/s)
        a: Atmospheric Stability Parameter (depends on atmos. conditions)
        y0 [default 0.]: cross section of source
    
    Returns:
        Expected enhancements in g/m^2, ignoring any additional
        zenith/azimuth angle corrections
    
    Exception Handling:
        Returns 0 for ZeroDivisionError. No other exceptions expected.
    """
    if x<=0:
        return 0
    else:
        x0 = (y0/float(a))**(1./0.894)*1000.
        x_effective = x + x0
        sigma_y = a*((x_effective/1000.)**(0.894))
        denom = np.sqrt(2*np.pi)*sigma_y*u
        exponent = -0.5*((y/sigma_y)**2)
    try:
        enhancement = (float(F)/denom)*np.exp(exponent)
    except ZeroDivisionError:
        enhancement = 0.
    return enhancement
    


def InPlume(x,y,u,F,a,plume_factor=_plume_default,xmax=_xmax_default):
    """True if point (x, y) is in the plume, False otherwise

    Criteria for in the plume:
    * V(x, y) >= plume_factor*V(x, 0)
    * x <= xmax
    
    Args:
        x: along-wind distance in meters
        y: across-wind distance in meters
        u: wind-speed at plume-height (m/s)
        F: Source emissions (g/s)
        a: Atmospheric Stability Parameter (depends on atmos. conditions)
        plume_factor: plume decay threshold
        xmax: Maximum along-wind distance to consider in the plume.
    
    Returns:
        True for in plume, False otherwise
    """
    if x<=0:
        return False
    else:
        Vmax = V(x,0,u,F,a)
        Vcurrent = V(x,y,u,F,a) 
        return Vcurrent >= plume_factor*Vmax and x<=xmax
        
        
def Background(x, y, u, F, a, background_factor=0.01, ymax=50.e3, offset=3000.):
    """Simplified background definition used for threshold lines on grid plots.
    
    We use a simpler definition for the grid plots because we don't want
    the plotted boundary lines to have any sudden jumps which would be
    caused by ymin_positive etc.
    
    Args:
        x: along-wind distance in meters
        y: across-wind distance in meters
        r: along-track distance from the source
        u: wind-speed at plume-height (m/s)
        F: Source emissions (g/s)
        a: Atmospheric Stability Parameter (depends on atmos. conditions)
        offset: extra displacement required in y-direction from center
        background_factor: background decay threshold
        ymax: Maximum distance from center to consider points
    
    Returns:
        True/False for in background or not
    """
    if x>0:
        Vmax=V(x,0,u,F,a)
        Vcurrent = V(x,max(0,abs(y)-offset),u,F,a)
        return Vcurrent <= background_factor * Vmax and abs(y) <= ymax
    else:
        return y<=ymax

def InBackground(x, y, r, u, F, a, background_factor=_bg_default,
                ymax_positive=y_max_pos_default, ymax_negative=y_max_neg_default,
                ymin_negative=y_min_neg_default, ymin_positive=y_min_pos_default,
                offset=_offset_default, sign='y'):
    """True if point (x, y) is in the background, False otherwise

    Criteria for Background:
    * (y-offset) is between ymin_negative and ymax_negative or between
      ymmin_positive and ymax_positive
    * V(x, y) <= background_factor*V(x, 0)
    
    Args:
        x: along-wind distance in meters
        y: across-wind distance in meters
        r: along-track distance from the source
        u: wind-speed at plume-height (m/s)
        F: Source emissions (g/s)
        a: Atmospheric Stability Parameter (depends on atmos. conditions)
        offset: extra displacement required in y-direction from center
        background_factor: background decay threshold
        ymax_positive, ymin_positive: allowed min/max distance in pos direction
        ymax_negative, ymin_negative: allowed min/max distance in neg direction
    """
    if sign=='y':
        sign_indicator = y
    elif sign=='x':
        sign_indicator = x
    else:
        raise TypeError('"sign" must be "x" or "y"; given %s' % sign)
    r = r*np.sign(sign_indicator)
    if x>0:
        Vmax=V(x,0,u,F,a)
        Vcurrent = V(x,max(0,abs(y)-offset),u,F,a)
        
        threshold_test = Vcurrent<=background_factor*Vmax
        distance_neg = -ymax_negative<=r<=-ymin_negative
        distance_pos = ymin_positive <= r <= ymax_positive
        return threshold_test and (distance_neg or distance_pos)
    else:
        distance_neg = -ymax_negative<=r<=-ymin_negative
        distance_pos = ymin_positive <= r <= ymax_positive
        return distance_neg or distance_pos