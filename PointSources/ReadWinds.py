"""
Module ReadWinds.py

Reads wind data for all the wind sources we are using.

For each wind data source, there is a function named
get_[description of source](time, **kwargs) that will
return a PST.Wind object, and for ECMWF optionally
surface winds and stability
"""


import os
import datetime as dt
import math

import numpy
from pygeode.formats import fstd,netcdf
import pygrib
import h5py
import PST


_ecmwf_fmt = '/wrk8/eltonc/ECMWF/data/EI/%Y/EI%y%m%d%H'
_merra_fmt = '/wrk8/MERRA/goldsmr5.gesdisc.eosdis.nasa.gov/%Y/%m/MERRA2_400.tavg3_3d_asm_Nv.%Y%m%d.nc4'
_gem_fmt = '/wrk8/GEM/operation.analyses.glbeta2/%Y/%m/%Y%m%d%H_000'
_ecmwfh_fmt = '/wrk8/eltonc/ECMWF/data/MH/%Y/MH%y%m%d%H'
_gemh_fmt = '/wrk8/GEM/operation.forecasts.glbhyb/%Y/%m/%Y%m%d%p_0%H'
_new_ecmwf_fmt = "/wrk8/ECMWF/%Y/EI%Y%m%d%H"

_merra_step = 3
_ecmwf_step = 3
_gem_step = 6
_new_ecmwf_step = 6

def get_gem_highres(time):
    """Reads 1h Gem Forecast data"""
    print "\nGathering GEM data..."
    
    t_lon = 360.+time.lon if time.lon < 0. else time.lon
    t_lat = time.lat
    
    year = time.year
    month = time.month
    day = time.day
    hour = time.hour
    minute = time.minute
    decimal_hour = time.decimaltime
    
    hour_minus = time.hour
    hour_plus = time.hour + 1
    
    time_minus = PST.Time(dt.datetime(year,month,day,hour_minus,0),time.source)
    time_plus = PST.Time(time_minus.datetimeobj+dt.timedelta(hours=1),time.source)

    hour_string_minus = '00' if time_minus.hour<12 else '12'
    hour_string_plus = '00' if time_plus.hour<12 else '12'
    
    file_minus = time_minus.strftime(_gemh_fmt).replace("AM","00").replace("PM","12")
    file_plus = time_plus.strftime(_gemh_fmt).replace("AM","00").replace("PM","12")
    
    if (not os.path.isfile(file_minus)) and (not os.path.isfile(file_plus)):
        err =  IOError("Neither file on either side of the sounding time exists. Unable to read wind data")
        raise err

    elif (not os.path.isfile(file_minus)) and os.path.isfile(file_plus):
        print("File before in time does not exist, but file after in time does; using only time after sounding")
        files = [file_plus,file_plus]
        
    elif (not os.path.isfile(file_plus)) and os.path.isfile(file_minus):
        print("File after in time does not exist, but file before in time does; using only time before sounding")
        files = [file_minus,file_minus]
        
    else:
        files = [file_minus,file_plus]
    
    u_interp=[]
    v_interp=[]
    for fname in files:
        try:
            rpn = fstd.open(fname)
        except IOError as e:
            print "Unable to open file {0}".format(fname)
            raise e

        try:
            U = rpn.UU
            V = rpn.VV
            GZ= rpn.GZ
        except AttributeError as error:
            print("Unable to read all fields -- see exception raised")
            print error

        # <Var 'GZ'> has 160 levels, but U, V only have 80. In tests opening files,
        # <LogHybrid> from GZ has extra levels compared to it from U and V; test to make sure of this

        if not numpy.array_equal(U.axes[2][:],GZ.axes[2][1::2]):
            raise ValueError("<LogHybrid> from GZ and UU, VV variables don't match up. Look closer at this file")
            return PST.Wind((0,0),0)

        lats = U.lat[:]
        lons=U.lon[:]
        lat_row=0
        lon_col=0
        while lats[lat_row]<t_lat:
            lat_row+=1
        while lons[lon_col]<t_lon:
            lon_col+=1

        lat_row-=1
        lon_col-=1
        used_lat = lats[lat_row]
        used_lon = lons[lon_col]

        lat_error = abs(t_lat - used_lat)
        lon_error = abs(t_lon - used_lon)

        if lat_error>abs(lats[1]-lats[0]) or lon_error>abs(lons[1] - lons[0]):
            print "Source position :",(t_lat,t_lon)
            print "Calculated position:",(used_lat, used_lon)
            raise ValueError("Rounding error: latitude or longitude was off by more than their resolution")
            
        U=U[0,0,:,lat_row,lon_col]
        V=V[0,0,:,lat_row,lon_col]
        GZ=GZ[0,0,1::2,lat_row,lon_col]
        i = 0
        while i<len(GZ):
            if GZ[i] < time.height:
                h1 = GZ[i]
                h2 = GZ[i-1]
                break
            i+=1
        else:
            h1=h2 = time.height
        u1=U[i]/3.6
        u2=U[i-1]/3.6
        v1=V[i]/3.6
        v2=V[i-1]/3.6
        u = numpy.interp(time.height,[h1,h2],[u1,u2])
        v = numpy.interp(time.height,[h1,h2],[v1,v2])
        u_interp.append(u)
        v_interp.append(v)
    u,v=map(lambda x: numpy.interp(decimal_hour,[hour_minus,hour_plus],x),[u_interp,v_interp])
    return PST.Wind((u,v),time.height)

def get_ecmwf_highres(time,surface=True):
    """Reads 0.3 degree ECMWF data"""
    print "Gathering ECMWF data..."
    source = time.source
    
    step = 1
    year = time.year
    month = time.month
    day = time.day
    hour = time.hour
    minute = time.minute

    hour_minus = hour
    hour_plus = hour+1
    time_minus = PST.Time(dt.datetime(year,month,day,hour_minus,0),source)
    time_plus = PST.Time(time_minus.datetimeobj+dt.timedelta(hours=1),source)

    file_minus = time_minus.strftime(_ecmwfh_fmt)
    file_plus = time_plus.strftime(_ecmwfh_fmt)
    
    u_time_interpolate = []
    v_time_interpolate = []
    u_surface_interp = []
    v_surface_interp = []
    cloud_fractions = []
    
    lat_resolution, lon_resolution = (0.3,0.3)
    
    for file_name in [file_minus,file_plus]:
        if not os.path.isfile(file_name):
            raise IOError('File {0} does not exist'.format(file_name))
            
        try:
            ecmwf = pygrib.open(file_name)
        except IOError:
            print("IOError: Could not open file {0}".format(file_name))
            raise
        except Excption as exc:
            print "Unexpected error occured"
            raise exc
        
        try:
            UU = ecmwf.select(name = 'U component of wind')
            VV = ecmwf.select(name = 'V component of wind')
            P_surface = ecmwf.select(name = 'Surface pressure')[0]
            P_surface.expand_grid(0)
            P_surface = numpy.reshape(P_surface.values[:55800],(150,372))
            cloud_fraction = ecmwf.select(name = "Total cloud cover")[0].values
            U_surface = ecmwf.select(name = "10 metre U wind component")[0].values[:-1]
            V_surface = ecmwf.select(name = "10 metre V wind component")[0].values[:-1]
        except AttributeError:
            raise AttributeError("File {0} is missing some expected attributes".format(file_name))
        
        # This data is missing part of the last row ( 33.3 to 33.0 degrees latitude for -109.8 to -64.8 degrees longitude)
        # so ignore the last row of the data (last 151 values)
        U=[]
        V=[]
        levels = len(UU)
        half_levels = levels+1
        try:
            for level in range(len(UU)):
                UU[level].expand_grid(0)
                U.append(numpy.reshape((UU[level].values)[:55800],(150,372)))
                
                VV[level].expand_grid(0)
                V.append(numpy.reshape((VV[level].values)[:55800],(150,372)))
            
            latitudes = numpy.reshape(UU[0].latitudes[:55800],(150,372))[:,0]
            longitudes = numpy.reshape(UU[0].longitudes[:55800],(150,372))[0]-360.
        except:
            raise IndexError("Problem reshaping U, V, lat, lon arrays in file {0}".format(file_name))

        U = numpy.array(U)
        V = numpy.array(V)
        
        A = UU[0].pv[:half_levels]
        A/=100.
        B = VV[0].pv[half_levels:]
        
        lat_row = int((latitudes[0] - time.lat)//lat_resolution)
        lon_col = int((time.lon - longitudes[0])//lon_resolution)
        
        lat_check = abs(latitudes[lat_row]-time.lat)<0.3
        lon_check = abs(longitudes[lon_col] - time.lon)<0.3
        
        coord = (latitudes[lat_row],longitudes[lon_col])
        
        if not lat_check or not lon_check:
            raise ValueError("Latitude and longitude points are further than the resolution away from the source. Source position ({0},{1}); calculated as ({2},{3})".format(time.lat,time.lon,latitudes[lat_row],longitudes[lon_col]))
        
        p0 = P_surface[lat_row,lon_col]
        H = 7000.
        z_prev = 0.
        k=0
        while k < (levels-1):
            A0 = A[k]
            A1 = A[k+1]
            A0 = A[k]
            A1 = A[k+1]
            B0 = B[k]
            B1 = B[k+1]
            Pk0 = A0 + B0*p0
            Pk1 = A1 + B1*p0
            Pk = 0.5*(Pk0 + Pk1)
            z = H*math.log(p0/Pk)
            if z < time.height:
                h1 = z
                h2 = z_prev
                break
            k+=1
            z_prev = z
        else:
            h1=h2=time.height
        u1 = U[k][lat_row,lon_col]
        u2 = U[k-1][lat_row,lon_col]
        v1 = V[k][lat_row,lon_col]
        v2 = V[k-1][lat_row,lon_col]
        u_surface = U_surface[lat_row, lon_col]
        v_surface = V_surface[lat_row, lon_col]
        
        u_interpolated = numpy.interp(time.height, [h1, h2], [u1, u2])
        v_interpolated = numpy.interp(time.height, [h1, h2], [v1, v2])
        
        u_time_interpolate.append(u_interpolated)
        v_time_interpolate.append(v_interpolated)
        u_surface_interp.append(u_surface)
        v_surface_interp.append(v_surface)
        
        cloud_fractions.append(cloud_fraction[lat_row,lon_col])
    
    u = numpy.interp(time.decimaltime,[hour_minus,hour_plus],u_time_interpolate)
    v = numpy.interp(time.decimaltime,[hour_minus,hour_plus],v_time_interpolate)
    
    # print u,v
    u_surface = numpy.interp(time.decimaltime, [hour_minus, hour_plus], u_surface_interp)
    v_surface = numpy.interp(time.decimaltime, [hour_minus, hour_plus], v_surface_interp)
    
    surface_wind = PST.Wind((u_surface, v_surface),10.) if surface else PST.Wind((u,v),time.height)
    wind = PST.Wind((u,v),time.height)
    
    if surface:
        stability = PST.Stability(surface_wind.speed,min(cloud_fractions))
    else:
        stability = PST.Stability(wind.speed,min(cloud_fractions))
    return (wind,stability)


def get_gem(time, interp=True, print_time=False):
    """Reads 6h GEM data"""
    print "\nGathering GEM data..."
    
    t_lon = time.lon%360
    t_lat = time.lat
    year = time.year
    month = time.month
    day = time.day
    hour = time.hour
    minute = time.minute
    step = _gem_step
    time_step = 3600*step
    
    decimal_hour = hour + minute/60.
    
    hour_minus = int(6*(time.decimaltime//6))
    delta_minus = dt.timedelta(hours=hour_minus-hour,minutes=-minute)
    hour_plus = hour_minus+6
    delta_plus = dt.timedelta(hours=hour_plus-hour,minutes=-minute)
   
    time_minus = time+delta_minus
    time_plus = time+delta_plus
    
    file_minus = time_minus.strftime(_gem_fmt)
    file_plus = time_plus.strftime(_gem_fmt)
    
    time_closest = time.round(time_step)
    file_closest = time_closest.strftime(_gem_fmt)
    
    if interp:
        files = [file_minus, file_plus]
        hours = [hour_minus, hour_plus]
    else:
        files = [file_closest]
        hours = [decimal_hour]
        
    u_interp=[]
    v_interp=[]
    
    if print_time:
        print "Time {0}; using files {1}".format(time.datetimeobj, files)

    for fname in files:
        if not os.path.exists(fname):
            raise IOError("File does not exists {0}".format(fname))
            
        try:
            rpn = fstd.open(fname)
        except IOError:
            raise IOError("Could not open {0} for GEM data\n".format(fname))
        
        try:
            U = rpn.UU
            V = rpn.VV
            Heights = rpn.GZ
            lats = U.lat[:]
            lons=U.lon[:]
        except AttributeError:
            raise AttributeError("Could not read U, V, GZ, lat, and lon from file {0}".format(fname))
        lat_row=0
        lon_col=0
        while lats[lat_row]<t_lat:
              lat_row+=1
        while lons[lon_col]<t_lon:
              lon_col+=1
        lat_row-=1
        lon_col-=1
        used_lat = lats[lat_row]
        used_lon = lons[lon_col]
        lat_error = t_lat - used_lat
        lon_error = t_lon - used_lon
        if lat_error>1. or lon_error>1.:
            raise ValueError("Position error: ({0},{1})".format(lat_error,lon_error))
            
        U=U[0,0,:,lat_row,lon_col]
        V=V[0,0,:,lat_row,lon_col]
        Heights=Heights[0,0,:,lat_row,lon_col]
        stack=time.height
        H_list = list(Heights)
        i = 0
        while i<len(H_list) and H_list[i]>stack:
              i+=1
        i=min(i,len(H_list)-1)
        h1 = H_list[i]
        h2 = H_list[i-1]
        u1=U[i]/3.6
        u2=U[i-1]/3.6
        v1=V[i]/3.6
        v2=V[i-1]/3.6
        u = numpy.interp(stack,[h1,h2],[u1,u2])
        v = numpy.interp(stack,[h1,h2],[v1,v2])
        u_interp.append(u)
        v_interp.append(v)
    u = numpy.interp(decimal_hour, hours, u_interp)
    v = numpy.interp(decimal_hour, hours, v_interp)
    return PST.Wind((u,v),stack)

def get_ecmwf(time, surface=True, interp=True, print_time=False, return_stability=True):
    """Reads 1 degree 3h interpolated ECMWF data"""
    source = time.source
    print "\nGathering ECMWF data..."
    step = _ecmwf_step
    time_step = 3600*step
    year = time.year
    month = time.month
    day = time.day
    hour = time.hour
    minute = time.minute
    decimal_hour = hour + float(minute)/60.
    
    time_closest = time.round(time_step)
    file_closest = time_closest.strftime(_ecmwf_fmt)

    hour_minus = int(step*(time.decimaltime//step))
    delta_minus = dt.timedelta(hours = (hour_minus-hour), minutes=-minute)
    
    hour_plus = hour_minus + step
    delta_plus = dt.timedelta(hours=hour_plus-hour,minutes=-minute)

    time_minus = time + delta_minus
    time_plus = time + delta_plus

    file_minus = time_minus.strftime(_ecmwf_fmt)
    file_plus = time_plus.strftime(_ecmwf_fmt)
    
    
    if interp:
        files = [file_minus, file_plus]
        hours = [hour_minus, hour_plus]
    else:
        files = [file_closest]
        hours = [decimal_hour]

    u_interp = []
    v_interp = []
    uSurface_interp = []
    vSurface_interp = []
    if print_time:
        print "Time {0}; using files {1}".format(time.datetimeobj, files)
    
    for file_name in files:    
        try:
            grib = pygrib.open(file_name)
        except IOError:
            raise IOError("Could not open file {0}".format(file_name))
        except:
            print "Unexpected Error follows:"
            raise
               
        u_list = grib.select(name = 'U component of wind')
        v_list = grib.select(name = 'V component of wind')
        Psurface = grib.select(name= 'Surface pressure')[0].values
        cloud = grib[304].values

        A = u_list[0].pv[:61]/100.
        B = u_list[1].pv[61:]
        lat_ax = u_list[0].latlons()[0][:,0]
        lon_ax = u_list[0].latlons()[1][0,:]
        lat0=lat_ax[0]
        lat1=lat_ax[1]
        lon0 = lon_ax[0]
        lon1=lon_ax[1]
        dlat = lat1-lat0
        dlon = lon1-lon0
        lat_row = int((source.lat-lat0)//dlat)
        lon_col = int((source.lon-lon0)//dlon)  
        lat_used = lat_ax[lat_row]
        lon_used = lon_ax[lon_col]
        lat_error = lat_used - source.lat
        lon_error = lon_used - source.lon
        if lat_error>1. or lon_error>1.:
            raise ValueError("Lat/lon disagree by more than the resolution: Errors are ({0}, {1})".format(lat_error,lon_error))
            
        stack = source.height
        H = 7000.
        p0 = Psurface[lat_row,lon_col]/100.
        H_list=[]
        i = 0
        prev = 0
        while i<60:
              A0 = A[i]
              A1 = A[i+1]
              B0 = B[i]
              B1 = B[i+1]
              Pk0 = A0 + B0*p0
              Pk1 = A1 + B1*p0
              Pk = 0.5*(Pk0 + Pk1)
              z = H*math.log(p0/Pk)
              if z<stack:
                 h1 = z
                 h2= prev
                 break
              i+=1
              prev = z
        i = min(59,i)
        if i==59:
           h1=stack
           h2=stack
        u1=u_list[i].values[lat_row,lon_col]
        u2=u_list[i-1].values[lat_row,lon_col]
        v1=v_list[i].values[lat_row,lon_col]
        v2=v_list[i-1].values[lat_row,lon_col]
#        print("Interpolating between heights {0} and {1} for a stack height of {2}".format(h1,h2,stack))
        u = numpy.interp(stack,[h1,h2],[u1,u2])
        v = numpy.interp(stack,[h1,h2],[v1,v2])
        uSurface = grib.select(name = "10 metre U wind component")[0].values[lat_row,lon_col]
        vSurface = grib.select(name = "10 metre V wind component")[0].values[lat_row,lon_col]
        u_interp.append(u)
        v_interp.append(v)
        uSurface_interp.append(uSurface)
        vSurface_interp.append(vSurface)
    cloudFraction = cloud[lat_row,lon_col]
    u_final = numpy.interp(decimal_hour,hours,u_interp)
    v_final = numpy.interp(decimal_hour,hours,v_interp)
    uSurface_final = numpy.interp(decimal_hour,hours,uSurface_interp)
    vSurface_final = numpy.interp(decimal_hour,hours,vSurface_interp)
    if surface:
        stability = PST.Stability(PST.Wind((uSurface_final,vSurface_final),stack).speed,cloudFraction)
    else:
        stability = PST.Stability(PST.Wind((u_final,v_final),stack).speed,cloudFraction)
        
    if return_stability:
        return [PST.Wind((u_final,v_final),stack),stability]
    else:
        return PST.Wind((u_final, v_final), stack)


def get_merra(time, print_time=False, action='middle'):
    """Reads 3h average MERRA data"""
    Source = time.source
    print "\nGathering MERRA data..."
    
    file_times = ["01:30", "04:30", "07:30", "10:30", "13:30", "16:30", "19:30", "22:30"]

    filename = time.strftime(_merra_fmt)

    t_lon=Source.lon
    t_lat = Source.lat
    
    if action=='middle':
        time_indices = [int((time.decimaltime)//_merra_step)]
        hours = [time.decimaltime]
    
    elif action=='beginning':
        time_indices = [int((time.decimaltime-1.5)//_merra_step)]
        hours = [time.decimaltime]
    
    elif action=='interpolate':
        tfloor = int((time.decimaltime-1.5)//_merra_step)
        time_indices = [tfloor, tfloor+1]
        hours = [(_merra_step*h + 1.5) for h in time_indices]
    
    else:
        raise ValueError('Invalid option "%s" for "action"' % action)
    
    if print_time:
        ftimes = [file_times[i] for i in time_indices]
        print "Time {0}; using file for time {1}".format(time.datetimeobj, ', '.join(ftimes))

    if not os.path.exists(filename):
        raise IOError("File {0} does not exist".format(filename))
    u_interp = []
    v_interp = []
    for time_index in time_indices:
        try:
            merra = netcdf.open(filename)
        except IOError:
            raise
        except:
            print "Unexpected Error Encountered:"
            raise
        
        U = merra.U
        V = merra.V
        lat0 = U.lat[0]
        lon0 = U.lon[0]
        lat1 = U.lat[1]
        lon1 = U.lon[1]
        dlat = lat1-lat0
        dlon = lon1-lon0
        lat_row = int((t_lat-lat0)//dlat)
        lon_col = int((t_lon-lon0)//dlon)
        lat_used = U.lat[lat_row]
        lon_used = U.lon[lon_col]
        lat_error = lat_used - t_lat
        lon_error = lon_used - t_lon
        
        if lat_error>dlat or lon_error>dlon:
            raise ValueError("Lat/lon disagree by more than the resolution: Errors are ({0}, {1})".format(lat_error,lon_error))
            
        U = U[time_index,:,lat_row,lon_col]
        V = V[time_index,:,lat_row,lon_col]
        Heights = merra.H[time_index,:,lat_row,lon_col]
        stack = Source.height
        H_list = list(Heights)
        i = 0
        while i<len(H_list) and H_list[i]>stack:
            i+=1
        if i==len(H_list):
            i=-1
            u=U[i]
            v=V[i]
    #       print("Using height {0}".format(H_list[i]))
        else:
            h1 = H_list[i]
            h2 = H_list[i-1]
            u1=U[i]
            u2=U[i-1]
            v1=V[i]
            v2=V[i-1]
    #         print("Interpolating between heights {0} and {1} for a stack height of {2}".format(h1,h2,stack))
            u = numpy.interp(stack,[h1,h2],[u1,u2])
            v = numpy.interp(stack,[h1,h2],[v1,v2])
        u_interp.append(u)
        v_interp.append(v)
    if len(u_interp)==1:
        u_final = u_interp[0]
        v_final = v_interp[0]
    else:
        u_final = numpy.interp(time.decimaltime, hours, u_interp)
        v_final = numpy.interp(time.decimaltime, hours, v_interp)
    return PST.Wind((u_final,v_final),stack)
    
def get_surface(time, interp=True):
    """Reads just surface wind from 0.75 degree 6h ECMWF data"""
    source = time.source
    print "\nGathering ECMWF data..."
    grib_file = _new_ecmwf_fmt
    step = _new_ecmwf_step
    year = time.year
    month = time.month
    day = time.day
    hour = time.hour
    minute = time.minute
    tlon = source.lon%360
    tlat = source.lat
    
    hour_minus = int(step*(time.decimaltime//step))
    delta_minus = dt.timedelta(hours = (hour_minus-hour), minutes=-minute)
    hour_plus = hour_minus + step
    delta_plus = dt.timedelta(hours=hour_plus-hour,minutes=-minute)

    time_minus = time+delta_minus
    time_plus = time+delta_plus

    decimal_hour = hour+minute/60.

    file_minus = time_minus.strftime(grib_file)
    file_plus = time_plus.strftime(grib_file)
    
    time_closest = time.round(step*3600)
    file_closest = time_closest.strftime(grib_file)
    
    if interp:
        files = [file_minus, file_plus]
        hours = [hour_minus, hour_plus]
    else:
        files = [file_closest]
        hours = [decimal_hour]

    usurf_interp = []
    vsurf_interp = []
    
    for file_name in files:
        try:
            grib = pygrib.open(file_name)
        except IOError:
            raise IOError("Could not open file {0}".format(file_name))
        except:
            print "Unexpected Error follows:"
            raise
        
        u_surf_dataset = grib.select(name="10 metre U wind component")[0]
        u_surf_list = u_surf_dataset.values
        v_surf_list = grib.select(name = "10 metre V wind component")[0].values
        
        lat_ax = u_surf_dataset.latlons()[0][:,0]
        lon_ax = u_surf_dataset.latlons()[1][0,:]
        lat0=lat_ax[0]
        lat1=lat_ax[1]
        lon0 = lon_ax[0]
        lon1=lon_ax[1]
        dlat = lat1-lat0
        dlon = lon1-lon0
        lat_row = int((tlat-lat0)//dlat)
        lon_col = int((tlon-lon0)//dlon)  
        lat_used = lat_ax[lat_row]
        lon_used = lon_ax[lon_col]
        lat_error = lat_used - tlat
        lon_error = lon_used - tlon
        if lat_error>1. or lon_error>1.:
            raise ValueError("Lat/lon disagree by more than the resolution: Errors are ({0}, {1})".format(lat_error,lon_error))
        
        u_surf = u_surf_list[lat_row, lon_col]
        v_surf = v_surf_list[lat_row, lon_col]
        usurf_interp.append(u_surf)
        vsurf_interp.append(v_surf)
    u = numpy.interp(decimal_hour, hours, usurf_interp)
    v = numpy.interp(decimal_hour, hours, vsurf_interp)
    
    return PST.Wind((u,v),0.)
    
    
def get_new_ecmwf(time, interp=True, return_stability=True, return_surface=False):
    """Reads 0.75 degree 6h ECMWF data"""
    source = time.source
    print "\nGathering ECMWF data..."
    grib_file = _new_ecmwf_fmt
    step = _new_ecmwf_step
    year = time.year
    month = time.month
    day = time.day
    hour = time.hour
    minute = time.minute
    tlon = source.lon%360
    tlat = source.lat
    
    hour_minus = int(step*(time.decimaltime//step))
    delta_minus = dt.timedelta(hours = (hour_minus-hour), minutes=-minute)
    hour_plus = hour_minus + step
    delta_plus = dt.timedelta(hours=hour_plus-hour,minutes=-minute)

    time_minus = PST.Time(time.datetimeobj+delta_minus,source)
    time_plus = PST.Time(time.datetimeobj+delta_plus,source)

    decimal_hour = hour+minute/60.

    file_minus = time_minus.strftime(grib_file)
    file_plus = time_plus.strftime(grib_file)
    
    time_closest = time.round(step*3600)
    file_closest = time_closest.strftime(grib_file)
    
    if interp:
        files = [file_minus, file_plus]
        hours = [hour_minus, hour_plus]
    else:
        files = [file_closest]
        hours = [decimal_hour]
    
    u_interp = []
    v_interp = []
    usurf_interp = []
    vsurf_interp = []
    cloud_interp = []
    
    for file_name in files:
        try:
            grib = pygrib.open(file_name)
        except IOError:
            raise IOError("Could not open file {0}".format(file_name))
        except:
            print "Unexpected Error follows:"
            raise
            
        u_list = grib.select(name = 'U component of wind')
        v_list = grib.select(name = 'V component of wind')
        Psurface = grib.select(name = 'Surface pressure')[0].values
        cloud = grib.select(name = "Total cloud cover")[0].values
        u_surf_list = grib.select(name = "10 metre U wind component")[0].values
        v_surf_list = grib.select(name = "10 metre V wind component")[0].values
        
        A = u_list[0].pv[:61]/100.
        B = u_list[1].pv[61:]
        lat_ax = u_list[0].latlons()[0][:,0]
        lon_ax = u_list[0].latlons()[1][0,:]
        lat0=lat_ax[0]
        lat1=lat_ax[1]
        lon0 = lon_ax[0]
        lon1=lon_ax[1]
        dlat = lat1-lat0
        dlon = lon1-lon0
        lat_row = int((tlat-lat0)//dlat)
        lon_col = int((tlon-lon0)//dlon)  
        lat_used = lat_ax[lat_row]
        lon_used = lon_ax[lon_col]
        lat_error = lat_used - tlat
        lon_error = lon_used - tlon
        
        # check if lat, lon are too far from the expected lat, lon
        if lat_error>1. or lon_error>1.:
            raise ValueError("Lat/lon disagree by more than the resolution: Errors are ({0}, {1})".format(lat_error,lon_error))
        # print "Using value at ({0}, {1})".format(lat_row,lon_col)
        stack = source.height
        H = 7000.
        p0 = Psurface[lat_row,lon_col]/100.
        H_list=[]
        i = 0
        prev = 0
        while i<60:
              A0 = A[i]
              A1 = A[i+1]
              B0 = B[i]
              B1 = B[i+1]
              Pk0 = A0 + B0*p0
              Pk1 = A1 + B1*p0
              Pk = 0.5*(Pk0 + Pk1)
              z = H*math.log(p0/Pk)
              if z<stack:
                 h1 = z
                 h2= prev
                 break
              i+=1
              prev = z
        else:
            h1=z
            h2=stack
            i-=1
            
        u1=u_list[i].values[lat_row,lon_col]
        u2=u_list[i-1].values[lat_row,lon_col]
        v1=v_list[i].values[lat_row,lon_col]
        v2=v_list[i-1].values[lat_row,lon_col]
        
        u = numpy.interp(stack,[h1,h2],[u1,u2])
        u_interp.append(u)
        v = numpy.interp(stack,[h1,h2],[v1,v2])
        v_interp.append(v)

        cloud_fraction = cloud[lat_row, lon_col]    
        cloud_interp.append(cloud_fraction)
        
        u_surf = u_surf_list[lat_row, lon_col]
        usurf_interp.append(u_surf)
        v_surf = v_surf_list[lat_row, lon_col]
        vsurf_interp.append(v_surf)
        
    u_final = numpy.interp(decimal_hour,hours,u_interp)
    v_final = numpy.interp(decimal_hour,hours,v_interp)
    
    usurf_final = numpy.interp(decimal_hour, hours, usurf_interp)
    vsurf_final = numpy.interp(decimal_hour, hours, vsurf_interp)
    
    cloud_final = numpy.interp(decimal_hour, hours, cloud_interp)
    surface_wind = PST.Wind((usurf_final,vsurf_final),0.)
    stability = PST.Stability(surface_wind.speed,cloud_final)
    return_values = [PST.Wind((u_final,v_final),stack)]
    if return_stability:
        return_values.append(stability)
    if return_surface:
        return_values.append(surface_wind)
        
    return return_values
