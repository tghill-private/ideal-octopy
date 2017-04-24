'''
===================================================================================================

  TIMES.py
  
  Purpose:
      (1) To retrieve the scale factors for a given latitude, longitude, date and time, and mode
          See function TemporalFactor for this
      
      (2) To plot the TIMES scale factors globally, for either diurnal or weekly factors
          See function PlotFactors
  
  Output of TemporalFactor is used to scale ODIAC and Vulcan data by the scale factors to ensure
    an accurate instantaneous emission rate -> enhancement
    
===================================================================================================
'''

import numpy
import os

import pygeode
from matplotlib import pyplot,cm


# Different TIMES Products:
Diurnal_Factors = '/wrk1/nassar/TIMES/netcdf/diurnal_scale_factors.nc'
Weekly_Factors = '/wrk1/nassar/TIMES/netcdf/weekly_factors_constant_China.nc'

def DailyFactor(time):
    """Reads the daily TIMES scale factor for a Time instance.
    
    Uses lat/lon and solar time stored in time to get the TIMES
    daily factor for the right lat/lon position and right
    time.
    
    Args:
        A PST.Time instance
    
    Returns:
        The TIMES daily scale factor
    """
    lat = time.lat
    lon = time.lon
    hour = time.solar.hour
    Daily = pygeode.open(Diurnal_Factors).diurnal_scale_factors[:]
    lat_row = (lat+90)//0.25
    lon_col = (lon+180)//0.25
    diurnal = Daily[lat_row,lon_col,hour]
    return diurnal

def WeeklyFactor(time):
    """Reads the TIMES weekly factor for a Time instance.
    
    Args: PST.Time instance
    Returns: TIMES weekly scale factor
    """
    lat = time.lat
    lon = time.lon
    day = time.solar.weekday()
    Weekly = pygeode.open(Weekly_Factors).weekly_scale_factors[:]
    lat_row = (lat+90)//0.25
    lon_col = (lon+180)/0.25
    weekly = Weekly[lat_row,lon_col,day]
    return weekly
	
def Factors(time):
    """Reads both daily and weekly factor for a Time.
    
    Args: PST.Time instance
    Returns: tuple (daily, weekly) scale factors
    """
    daily = DailyFactor(time)
    weekly = WeeklyFactor(time)
    return (daily,weekly)


def PlotFactors(mode):
    Daily = pygeode.open(Diurnal_Factors).diurnal_scale_factors
    Weekly = pygeode.open(Weekly_Factors).weekly_scale_factors
    if mode == 'diurnal':
       Data = Daily[:]
       smin = 0.8
       smax = 1.2
       TitleTime = DateTime
       tUnit = 'h UTC'
    elif mode == 'weekly':
         Data = Weekly[:]
         smin = 0.95
         smax = 1.05
         Data = Weekly_Array[:,:,DateTime]
         tUnit = ''
         TitleTime = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][DateTime]
    else:
         print 'Invalid mode. Use "diurnal" or "weekly"'
         return
    x_axis = numpy.arange(-180.,180.,0.25)
    y_axis = numpy.arange(-90.,90.,0.25)
    fig,ax = pyplot.subplots()
    cax=ax.pcolormesh(x_axis,y_axis,Data,cmap=cm.coolwarm,vmin=smin,vmax=smax)
    ax.set_title('TIMES {0} Scale Factors for {1}{2}'.format(mode,TitleTime,tUnit))
    ax.set_xlim(-180,180)
    ax.set_ylim(-90,90)
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    cbar = fig.colorbar(cax,orientation='horizontal')
    pyplot.savefig('Times{0}.png'.format(mode))