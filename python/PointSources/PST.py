"""
Module PST.py

This is an important module giving structure to the basic classes of
point source work: PointSource, Time, Wind, and Overpass classes.

Also contains the massive File class for now, which reads OCO-2 full
and lite files, as well as mimics their file structure while containing
points filtered by certain quality criteria.
"""

## Standard python modules
import math
import datetime as dt
import os
import warnings
from collections import namedtuple


## Other necessary modules
import numpy
import h5py # opening Netcdf and HDF lite and full files

## Modules from /home/tim/PointSources/Python/Modules
import ReadWinds
import TIMES
import Geometry
import Emissions
import Units
import timing
import PlumeModel
import warnings

class PointSource(object):
    """Stores data about the point sources we are interested in.
    
    Requires a name to give the variable, latitude, longitude, display name
    (for printing more detailed information), annual average co2 emissions,
    and weighted mean stack height.
    
    Mainly used to subclass to get access to latitude and longitude, but
    also has method to get the emissions for a given time.
    """
    _emitter_list_units = 'M_t/yr'
    
    def __init__(self, name, lat, lon, display_name, annual_average, yearly_emissions, height):
        self.lon = lon
        self.lat = lat
        self.short = name
        self.name = display_name
        self.height = height
        self.yearly_emissions = yearly_emissions
        
        self.emissions = Units.SciVal(annual_average, PointSource._emitter_list_units)
        self.emissions.convert(Units.output_units)
        self.co2_annual_average = self.emissions
        
        self.monthlyFactors = [1 for i in range(12)]
        self.secondary = []
        self.Overpasses = []

    def __eq__(self,other):
        return isinstance(other, PointSource) and self.lon==other.lon and self.lat==other.lat and self.name==other.name and self.emissions==other.emissions and self.short==other.short and self.secondary==other.secondary and self.height==other.height
        
    def set_secondary(self,sources):
        self.secondary = sources
                 
    def __repr__(self):
        return self.name
    
    def get_emissions(self, date, temporal_factors=False, units=Units._model_units, **kwargs):
        """Gets the daily emissions from Emissions module.
        
        date is any instance (or instance of a subclass) of datetime.datetime.
        That means Overpass or Time objects are also acceptable

        Uses Emissions.get_emissions(self, date, **kwargs) function to get value

        Returns a SciVal instance
        """
        try:
            return Emissions.get_daily_emissions(Time(date,self), 
                                temporal_factors=temporal_factors,
                                units=units, **kwargs)
        except IOError:
            emissions = self.yearly_emissions[date.year]
        except KeyError:
            # There is not a file for the requested time
            print "KeyError: Using annual emissions average"
            emissions = self.yearly_emissions[date.year]
        except Exception as exc:
            # Unexpected exception occured:
            # print "An Unexpected exception occured: see message\n", exc
            # return self.emissions*factor
            raise
        
        if temporal_factors:
            daily,weekly = TIMES.Factors(date)
            factor = daily*weekly
        else:
            factor=1.
        return emissions(units)*factor
    
    def get_hourly_emissions(self, date, temporal_factors=False, units=Units._model_units, **kwargs):
        """Gets the hourly emissions from Emissions module.
        date is any instance (or instance of a subclass) of datetime.datetime.
        That means Overpass or Time objects are also acceptable
        
        Uses Emissions.Emissions.get_emissions(self, date, **kwargs)
        function to get value
        
        Returns a SciVal instance
        """
        try:
            return Emissions.get_hourly_emissions(Time(date,self), 
                                temporal_factors=temporal_factors,
                                units=units, **kwargs)
        except IOError:
            emissions = self.emissions
        except KeyError:
            # There is not a file for the requested time
            print "KeyError: Using annual emissions average"
            emissions = self.emissions
        except Exception as exc:
            # Unexpected exception occured:
            # print "An Unexpected exception occured: see message\n", exc
            # return self.emissions*factor
            raise
        
        if temporal_factors:
            daily,weekly = TIMES.Factors(date)
            factor = daily*weekly
        else:
            factor=1.
        return emissions(units)*factor
    
    def with_emissions(self, F, units):
        F = Units.SciVal(F, units)
        new = PointSource(self.short, self.lat, self.lon, self.name, self.emissions, self.yearly_emissions, self.height)
        new.emissions = F
        for key in new.yearly_emissions.keys():
            new.yearly_emissions[key] = F
        return new


class Wind:
    """Stores wind vector (u,v) and height the wind is measured at.
    
    Allows easy access to wind speed and wind direction
    Defines operations __add__, __mul__, __rmul__, __sub__
    If v, w are both winds, the following are all valid, and work component-wise:
    v + w
    v - w
    v*2.5
    2.5*w
    w/3.1
    Heights are averaged when two vectors are added or subtracted
    This means the average wind vector is now just 0.5*(w + v)
    
    Attributes:
    * speed: float (>=0) giving the scalar wind speed
    * direction: float (-180-180) giving the wind bearing (North-clockwise)
    * height: height the wind is measured at
    * u, v: floats giving the u (North) and v(East) wind components
    """
    def __init__(self,wind,height):
        """Constructs a wind from the vector (u,v) and altitude height"""
        u = wind[0]
        v = wind[1]
        self.u = u
        self.v = v
        self.speed = (u*u + v*v)**(1./2.)
        angle = math.atan2(float(u),float(v))
        bearing = angle*180./math.pi
        self.bearing = bearing
        try:
            self.direction = (float(u)/self.speed,float(v)/self.speed)
        except ZeroDivisionError:
            self.direction=0
        self.height = height
    
    def __add__(self, y):
        """Allows adding Winds component-wise.
        
        Definition of wind addition:
        Let W = Wind((uw, vw), hw), V = Wind(uv, vv), hv)
        Then,
        V+W = Wind((uv+uw, vv+vw), 0.5*(hw+hv))"""
        if isinstance(y, Wind):
            new_u = self.u + y.u
            new_v = self.v + y.v
            new_height = 0.5*(self.height + y.height)
            return Wind((new_u, new_v), new_height)
        else:
            raise TypeError('Can not add Wind object and {0}'.format(type(y)))
    
    def __div__(self, divisor):
        """Scalar division of a wind by a scalar.
        Let W = Wind((u, v), h), d be a scalar.
        Then,
        W/d = Wind((u/d, v/d), h)
        """
        divisor = float(divisor)
        u, v = self.u, self.v
        try:
            return Wind((u/divisor, v/divisor), self.height)
        except:
            raise
    
    def __mul__(self, multiplier):
        """Dot product between two Winds, or scalar multiplication.
        
        Let W = Wind((uw, vw), hw), V = Wind(uv, vv), hv)
        Then,
        V*W = (uv*uw) + (vv*vw)
        
        Let W = Wind((u, v), h) and m be a scalar
        Then,
        V*W = Wind((m*u, m*v), h)"""
        if isinstance(multiplier, Wind):
            return (self.u*other.u)+(self.v*other.v)
            
        elif type(multiplier)==int or type(multiplier)==float:
            try:
                multiplier = float(multiplier)
            except:
                raise
            u, v = self.u, self.v
            try:
                return Wind((u*multiplier, v*multiplier), self.height)
            except:
                raise
                
        else:
            raise TypeError("multiplier in Wind.__mul__(self, multiplier) must be either and int or a float, not {0}".format(type(multiplier)))
        
    def __rmul__(self, multiplier):
        """Allows multiplication on the right, ie
        3*wind and wind*3 are both allowed"""
        return self * multiplier
        
        
    def __sub__(self, y):
        """Subtraction between wind objects.
        This is equal to adding a negative"""
        if isinstance(y, Wind):
            new_u = self.u - y.u
            new_v = self.v - y.v
            new_height = 0.5*(self.height + y.height)
            return Wind((new_u, new_v), new_height)
        else:
            raise TypeError('Can not ssubtract (method Wind.__sub__(self, u)) Wind object and {0}'.format(type(y)))
    
    def __str__(self):
        S = "{0}m/s, {1} degrees".format(self.speed,self.bearing)
        return S
    
    def __repr__(self):
        return "Wind(({0}, {1}), {2})".format(self.u, self.v, self.height)
        
    def rotate(self,angle,units='degrees'):
        """Rotates the wind vector. Optionally can be degrees (default) or radians"""
        if units=='degrees':
            rad = angle*math.pi/180.
        else:
            rad = angle
        u=self.u
        v=self.v
        s=self.speed
        angle=math.atan2(v,u)
        tot_angle = -rad+angle
        u_new = s*math.cos(tot_angle)
        v_new = s*math.sin(tot_angle)
        return Wind((u_new,v_new),self.height)
    
    @staticmethod
    def construct(mag,dir,height):
        """Makes a wind object given a speed, direction, and height"""
        u = mag*math.sin(dir*math.pi/180.)
        v = mag*math.cos(dir*math.pi/180.)
        return Wind((u,v),height)
    
    def __eq__(self, other):
        """Defines equality component wise for u, v, and height.
        Does not raise Exception if other is not a Wind instance, instead returns False
        """
        return isinstance(other,Wind) and self.u==other.u and self.v==other.v and self.height==other.height

class Time(PointSource,dt.datetime):
    """Adds location to built in dt.datetime class
    
    Subclasses PointSource and dt.datetime. This associates
    a location with a time, which is a very useful package
    of information for getting wind data, etc.
    """
    def __new__(cls,dtime,source,time_string=None):
        """Overriding defulat __new__ to subclass datetime.datetime"""
        if time_string!=None:
            t = time_string[1:-1].split()
            yr = int(t[0])
            mo = int(t[1])
            dy = int(t[2])
            hr = int(t[3])
            mi = int(t[4])
            sec = int(t[5])
            dtime = dt.datetime(yr, mo, dy, hr, mi, sec)
        return super(Time,cls).__new__(cls,dtime.year, dtime.month, dtime.day, dtime.hour, dtime.minute,dtime.second)
    
    def __init__(self,dtime,source,time_string=None):
        """Inherits from PointSource and dt.datetime.
        
        Adds local solar time representation of time.
        """
        if time_string != None:
            t = time_string[1:-1].split()
            yr = int(t[0])
            mo = int(t[1])
            dy = int(t[2])
            hr = int(t[3])
            mi = int(t[4])
            sec = int(t[5])
            dtime = dt.datetime(yr, mo, dy, hr, mi, sec)
        super(Time,self).__init__(source.short, source.lat, source.lon,
                source.short, source.co2_annual_average,
                source.yearly_emissions, source.height)
        
        self.strf8 = self.strftime('%Y%m%d')
        self.strf6 = self.strftime('%y%m%d')
        self.numday = self.strftime('%j')
        self.decimaltime = self.hour + (self.minute/60.)
        
        self.datetimeobj = dtime
        self.source = source
        
        solar_hour = int(source.lon//15)
        solar_minute = int((source.lon%15) * 4)
        delt = dt.timedelta(0,0,hours=solar_hour,minutes=solar_minute)
        solar_date = dtime + delt
        self.solar = solar_date
        
        hyphen = self.strftime('%Y-%m-%d-%H-%M')
        self.hyphen=hyphen
        lite_file = '/wrk7/SATDATA/OCO-2/Lite/v07b/{0}/oco2_LtCO2_{1}_B7000rb_COoffline.nc4'.format(self.year,self.strf8)
        self.Lite = lite_file
    
    def __repr__(self):
        return "Time({0}, {1})".format(self.short, self.datetimeobj.__repr__())
    
    def __str__(self):
        return "{0} {1}".format(self.short, self.datetimeobj.__str__())
    
    def round(self, roundTo=3600):
        """Round a datetime object to any time laps in seconds
        dt : datetime.datetime object, default now.
        roundTo : Closest number of seconds to round to, default 1 minute.
        Author: Thierry Husson 2012 - Use it as you want but don't blame me.
        """
        seconds = (self.replace(tzinfo=None) - self.min).seconds
        rounding = (seconds+roundTo/2) // roundTo * roundTo
        new_time = self.datetimeobj + dt.timedelta(0,rounding-seconds,-self.microsecond)
        return Time(new_time,self.source)
    
    def __add__(self, other):
        """Add a dt.timedelta instance to Time instance.
        
        Returns the new instance
        Time(datetime + other, source) where other is a dt.timedelta
        instance, so datetime + other is a new dt.datetime instance
        """
        try:
            self_time = self.datetimeobj
            new_time = Time(self_time+other, self.source)
        except:
            raise
        return new_time

class Stability:
    """Determines stability class from surface wind and cloud fraction.

    Stores the string class representation and the numeric value of a,
    calculated according to the Pasquil-Gifford stability classes.
    We have added classes 'AB' and 'BC' with 'a' values halfway
    between the existing class values"""
    def __init__(self,surfaceWind,cloudFraction):
        """Methods:
        stability.stability  stability class (str A, AB, B, BC, C, CD, D)
        stability.a          stability parameter (float)
        """
        classes = {'A':213., 'AB': 184.5, 'B': 156., 'BC':130.,
        'C': 104., 'CD': 86., 'D':68.}
        self.surfaceWind = surfaceWind
        self.cloudFraction = cloudFraction
        high_mod=0.33333
        mod_low=0.66667
        if cloudFraction<high_mod:
            if surfaceWind<2:
                stability = 'A'
            elif surfaceWind<3:
                stability = 'AB'
            elif surfaceWind<5:
                stability = 'B'
            elif surfaceWind<6:
                stability = 'BC'
            else:
                stability = 'C'
        elif cloudFraction<mod_low:
            if surfaceWind<2:
                stability = 'AB'
            elif surfaceWind<3:
                stability = 'B'
            elif surfaceWind<5:
                stability = 'BC'
            elif surfaceWind<6:
                stability = 'CD'
            else:
                stability = 'D'
        else:
            if surfaceWind<2:
                stability = 'B'
            elif surfaceWind<3:
                stability = 'C'
            elif surfaceWind<5:
                stability = 'C'
            elif surfaceWind<6:
                stability = 'D'
            else:
                stability = 'D'
        self.stability = stability
        a=classes[stability]
        self.a=a
        
    def __str__(self):
        info = 'Class {0}, {1}; {2}m/s; Total Cloud Cover = {3}'.format(self.stability,self.a,self.surfaceWind,self.cloudFraction)
        return info
       
    def __repr__(self):
        return "Stability({0}, {1})".format(self.surfaceWind,self.cloudFraction)


class AllWinds(Time):
    """Class for storing and retrieving wind data for a Time self.
    
    Use self.get_winds() to retrieve the basic three wind directions, and
    to calculate the average (of MERRA and ECMWF).
    Use self.get_GEM_high_resolution() and self.get_ECMWF_high_resolution()
    to get the high resolution GEM and ECMWF data
    """
    
    valid_keys = [  'MERRA', 'MERRA_beginning', 'MERRA_interp',
                    'ECMWF','ECMWF_old', 'ECMWF_highres',
                    'Average', 'Average_old',
                    'Average_beginning', 'Average_interp','Average_hybrid',
                    'GEM', 'GEM_highres',
                    'all', 'highres'
                ]
    
    def __new__(cls, Time, surface=True):
        """Overriding the default __new__ method to pass Time right arguments to subclass dt.datetime"""
        return super(AllWinds,cls).__new__(cls,Time.datetimeobj,Time.source)
    
    def __init__(self, Time, surface=True):
        """Overriding default constructor to subclass Time"""
        self.surface = surface
        self.time = Time
        self.height = Time.height
        super(AllWinds,self).__init__(Time.datetimeobj,Time.source)
        
    def get_winds(self):
        """Reads MERRA, ECMWF, and GEM winds from module ReadWinds.
        Prints Exceptions but does not raise, and sets the attribute to zero-wind 
        (except for parse method which raises).
        
        parse(str) method deals with parsing a str corresponding to winds
        into lists of the Wind objects and wind labels
        """
        fill_value = Wind((0,0),0)
        try:
            merra = ReadWinds.get_merra(self.time)
        except IOError:
            print("Could not open MERRA file for {0}".format(self.time))
            merra = fill_value
        except ValueError:
            print("Error reading winds; reading from wrong grid box")
            merra = fill_value
        except Exception as err:
            print("Unexpected exception encountered:")
            print err
            merra = fill_value
        finally:
            self.MERRA = merra
        
        try:
            merra_beginning = ReadWinds.get_merra(self.time, action='beginning')
        except IOError:
            print("Could not open MERRA file for {0}".format(self.time))
            merra_beginning = fill_value
        except ValueError:
            print("Error reading winds; reading from wrong grid box")
            merra_beginning = fill_value
        except Exception as err:
            print("Unexpected exception encountered:")
            print err
            merra_beginning = fill_value
        finally:
            self.MERRA_beginning = merra_beginning
        try:
            merra_interp = ReadWinds.get_merra(self.time, action='interpolate')
        except IOError:
            print("Could not open MERRA file for {0}".format(self.time))
            merra_interp = fill_value
        except ValueError:
            print("Error reading winds; reading from wrong grid box")
            merra_interp = fill_value
        except Exception as err:
            print("Unexpected exception encountered:")
            print err
            merra_interp = fill_value
        finally:
            self.MERRA_interp = merra_interp
        
        try:
            gem = ReadWinds.get_gem(self.time)
        except IOError:
            print("Could not open GEM file for {0}".format(self.time))
            gem = fill_value
        except ValueError:
            print("Error reading winds; reading from wrong grid box")
            gem = fill_value
        except Exception as err:
            print("Unexpected exception encountered:")
            print err
            gem = fill_value
        finally:
            self.GEM = gem
        
        try:
            ecmwf,stability_class = ReadWinds.get_ecmwf(self.time, self.surface)
        except IOError:
            print("Could not open ECMWF file for {0}".format(self.time))
            ecmwf = fill_value
            stability_class = Stability(0,1)
        except ValueError:
            print("Error reading winds; reading from wrong grid box")
            ecmwf = fill_value
            stability_class = Stability(0,1)
        except Exception as err:
            print("Unexpected exception encountered:")
            print err
            ecmwf = fill_value
            stability_class = Stability(0,1)
        finally:
            self.ECMWF_old = ecmwf
            self.cloud = stability_class.cloudFraction
            self.stability_old = stability_class.stability
        
        try:
            ecmwf_new, stability, surface_wind = ReadWinds.get_new_ecmwf(self.time, return_surface=True)
        except IOError:
            print("Could not open ECMWF file for {0}".format(self.time))
            ecmwf_new = fill_value
            stability = Stability(0,1)
            surface_wind = fill_value
        except ValueError:
            print("Error reading winds; reading from wrong grid box")
            ecmwf_new = fill_value
            stability = Stability(0,1)
            surface_wind = fill_value
        except Exception as err:
            print("Unexpected exception encountered:")
            print err
            ecmwf_new = fill_value
            stability = Stability(0,1)
            surface_wind = fill_value
        finally:
            self.ECMWF = ecmwf_new
            self.stability = stability.stability
            self.cloud = stability.cloudFraction
            self.surface_wind = surface_wind
            
    
        self.a = stability.a
        self.a_elevated = Stability(ecmwf.speed,stability_class.cloudFraction).a
        
        self.a_old = stability_class.a
        
        average = 0.5*(merra + ecmwf_new)
        self.Average = average
        
        average_old = 0.5*(merra + ecmwf)
        self.Average_old = average_old
        
        # Attributes to provide the disagreement between MERRA and ECMWF
        delta_angle = (merra.bearing - ecmwf.bearing)%360
        delta_speed = merra.speed - ecmwf.speed
        
        self.delta_bearing = delta_angle
        self.delta_speed = delta_speed
    
    def get_ECMWF_highres(self):    
        try:
            wind,stability = ReadWinds.get_ecmwf_highres(self.time,self.surface)
        except Exception as excp:
            wind = Wind((0,0),0)
            stability = Stability(0,0)
            print excp
        
        self.ECMWF_highres = wind
        self.a_highres = stability.a
        self.cloud_highres = stability.cloudFraction
        return wind
    
    def get_GEM_highres(self):
        try:
            self.GEM_highres = ReadWinds.get_gem_highres(self.time)
        except Exception as excp:
            self.GEM_highres = Wind((0,0),0)
            print excp
        return self.GEM_highres

    def __repr__(self):
        return "AllWinds({0})".format(self.time)
    
    def construct_wind(self,mag,dir):
        """Makes a wind object given a speed, direction, and height"""
        u = mag*math.sin(dir*math.pi/180.)
        v = mag*math.cos(dir*math.pi/180.)
        return Wind((u,v),self.height)
    
    
    def __getitem__(self,key):
        if hasattr(self,key):
            return getattr(self,key)
        else:
            raise AttributeError("'AllWinds' object does not have attribute {0}".format(key))
    
    def add_custom(self,values):
        """Values is either a single pair (speed, bearing), or is a list of such pairs.
        Otherwise it should raise a TypeError exception"""
        if values==None:
            return ([],[])
        shape = numpy.shape(values)
        if len(shape)==1:
            try:
                speed, bearing = values
            
            except ValueError:
                raise TypeError("values = {0} is not of the form (speed, bearing). It must be either (speed, bearing) or a list of (speed, bearing)".format(values))
            except:
                raise
            else:
                wind = self.construct_wind(speed,bearing)
                return ([wind],[str(wind)])
        else:
            winds = []
            labels = []
            for value in values:
                try:
                    speed, bearing = value
                
                except ValueError:
                    raise TypeError("values = {0} is not of the form listof(speed, bearing). It must be either (speed, bearing) or a list of (speed, bearing)".format(values))
                except:
                    raise
                else:
                    wind = self.construct_wind(speed,bearing)
                    winds.append(wind)
                    labels.append(str(wind))
            
            return (winds,labels)
    
    def parse(self, wind_str):
        """Parses a string to a list of matching Wind instances.
        
        wind_str can be a string or list of strings, and the function
        will return a list of all matching winds.
        
        Args:
         * wind_str: string or list of strings. Possible values are
         ["MERRA", "GEM", "ECMWF", "Average", "ECMWF_old",
                            "GEM_highres", "ECMWF_highres"]
          "all" maps to "MERRA", "ECMWF", "Average", and
          "highres" maps to "MERRA", "ECMWF", "ECMWF_highres", "Average"
        
        Returns:
            A list of Wind instances
        """
         
        wind_map = {'all':['MERRA','ECMWF','Average'],
                    'highres':['MERRA','ECMWF','ECMWF_highres','Average']}
        
        try:
            self.MERRA = self.time.MERRA
            self.MERRA_beginning = self.time.MERRA_beginning
            self.MERRA_interp = self.time.MERRA_interp
            
            self.GEM = self.time.GEM
            
            self.ECMWF = self.time.ECMWF
            self.ECMWF_old = self.time.ECMWF_old
            
            self.Average = self.time.Average
            self.Average_old = self.time.Average_old
            self.Average_beginning = self.time.Average_beginning
            self.Average_interp = self.time.Average_interp
            self.Average_hybrid = self.time.Average_hybrid
        except AttributeError:
            self.get_winds()
        except:
            raise
        # self.get_GEM_highres()
        # self.get_ECMWF_highres()
        if wind_str == 'all':
            wind_attrs = wind_map['all']
        
        elif wind_str== 'highres':
            self.get_GEM_highres()
            self.get_ECMWF_highres()
            wind_attrs = wind_map['highres']
        
        elif hasattr(wind_str,"__iter__"):
            wind_attrs = wind_str
        
        elif type(wind_str)==str:
            if wind_str=='ECMWF_highres':
                self.get_ECMWF_highres()
            elif wind_str=='GEM_highres':
                self.get_GEM_highres()  
            wind_attrs = [wind_str]
        
        elif wind_str==None:
            wind_attrs = []
        else:
            raise TypeError("Value or type of winds not recognized. Given {0}; expected one of or list of {1}".format(wind_str,', '.join(AllWinds.valid_keys)))
            return
        
        wind_instances = []
        wind_labels = []
        for wind in wind_attrs:
            # change case to match a key if necessary
            if wind in AllWinds.valid_keys:
                wind_key = wind
            elif wind.upper() in AllWinds.valid_keys:
                wind_key = wind.upper()
            elif wind.lower() in AllWinds.valid_keys:
                wind_key = wind.lower()
            else:
                raise AttributeError("AllWinds instance does not have attribute '{0}'. Valid strings are {1}".format(wind, ', '.join(AllWinds.valid_keys)))
            
            try:
                w = self[wind_key]
            except AttributeError:
                raise AttributeError("AllWinds instance does not have attribute '{0}'. Valid strings are {1}".format(wind, ', '.join(AllWinds.valid_keys)))
            except:
                raise
                
            else:
                wind_instances.append(w)
                wind_labels.append(wind)
        
        return (wind_instances,wind_labels)
        
    def __getitem__(self, key):
        return getattr(self, key)


class Overpass(Time):
    """Represents and stores data for an OCO-2 overpass

    Subclasses Time, so inherits from both dt.datetime and PointSource;
    this is natural since an overpass has a specific location
    and time. This class is never created by itself, but is
    created in the Overpasses module.
    
    Allows easy access of emissions data.
    
    Function new makes an Overpass instance and gets wind data
    if you know te source, time, and lite and full files
    """
    
    header = "Source,Time,MERRA Beginning U,MERRA Beginning V,\
MERRA Middle U,MERRA Middle V,MERRA interp U,MERRA interp V,ECMWF U,ECMWF V,\
New ECMWF U,New ECMWF V,GEM U,GEM V,Average U,AverageV,Surface U,SurfaceV,\
Old Stability,Old a,Stability,a,Lite File,Full File\n"
    
    def __new__(cls,time):
        return super(Overpass,cls).__new__(cls,time.datetimeobj,time.source) #override __new__ for subclassing datetime.datetime
    
    def __init__(self,time):
        super(Overpass,self).__init__(time.datetimeobj, time.source) # subclass time

        self.time = time
        self.source = time.source
        self.datetime = time.datetimeobj
        self.info = "{0} {1}".format(self.short, self.strftime('%Y-%m-%d'))
        self.short_name = self.short+self.strftime('%Y%m%d')
        
    
    def get_ECMWF_HighRes(self):
        """Tries to get the ECMWF 0.3 degree wind for an overpass.
        
        This method calls the AllWinds.get_ECMWF_high_resolution
        method, so if any Exceptions are raised it returns
        Wind((0,0),0)
        """
        self.all_winds.get_ECMWF_high_resolution()
        self.ECMWF_high_resolution = all_winds.ECMWF_mh
        return all_winds.ECMWF_mh
    
    def get_GEM_HighRes(self):
        """Tries to get the GEM forecast 1h wind data for an overpass.
        
        This method calls the AllWinds.get_GEM_high_resolution
        method, so if any Exceptions are raised it returns
        Wind((0,0),0)
        """
        self.all_winds.get_GEM_high_resolution()
        self.GEM_high_resolution = all_winds.gem_high_resolution
        return self.GEM_high_resolution

    def __repr__(self):
        return "Overpass({0})".format(self.time.__repr__())
    
    def __str__(self):
        return self.time.__str__()
    
    def get_emissions(self,units=Units._model_units,**kwargs):
        """Gets the daily emissions for the time of the overpass.
        
        Emissions are returned with units 'units', which
        defaults to 'g/s'.
        
        Optional keyword arguments are passed to Emissions module
        functions (temporal factors).
        """
        return self.source.get_emissions(self,units=units,  **kwargs)
    
    def get_hourly_emissions(self, units=Units._model_units, **kwargs):
        """Gets the hourly emissions for the time of the overpass.
        
        This will always use time.hour as the time to get. For
        example, 21:45 --> emissions for hour 21:00.
        
        Emissions are returned with units 'units', which
        defaults to 'g/s'.
        
        Optional keyword arguments are passed to Emissions module
        functions (temporal factors).
        """
        return self.source.get_hourly_emissions(self, units=units, **kwargs)
    
    def surrounding_winds(self, source="MERRA", **kwargs):
        """Gets the winds before and after the overpass time.
        
        Uses the source indicated by 'source' parameter,
        and reads the file before and after the overpass time.
        
        kwargs are any arguments that can be passed to the
        reading winds functions
        """
        if source == "MERRA":
            time_step = 3600*ReadWinds._merra_step
            time_minus = self.time.round(time_step) + dt.timedelta(hours=-1.5)
            time_plus = time_minus + dt.timedelta(hours=ReadWinds._merra_step)
            w_minus = ReadWinds.get_merra(time_minus, **kwargs)
            w_plus = ReadWinds.get_merra(time_plus, **kwargs)
        
        elif source == "ECMWF":
            time_step = 3600*ReadWinds._ecmwf_step
            time_minus = self.time.round(time_step)
            time_plus = time_minus + dt.timedelta(hours=ReadWinds._ecmwf_step)
            w_minus = ReadWinds.get_ecmwf(time_minus, interp=False, **kwargs)[0]
            w_plus = ReadWinds.get_ecmwf(time_plus, interp=False, **kwargs)[0]
        
        elif source == "GEM":
            time_step = 3600*ReadWinds._gem_step
            time_minus = self.time.round(time_step)
            time_plus = time_minus + dt.timedelta(hours=ReadWinds._gem_step)
            w_minus = ReadWinds.get_gem(time_minus, interp=False, **kwargs)
            w_plus = ReadWinds.get_gem(time_plus, interp=False, **kwargs)
        
        else:
            raise TypeError("source must be one of 'ECMWF', 'MERRA', or 'GEM'")
        
        print "Wind for {0}: {1}".format(time_minus, w_minus)
        print "Wind for {0}: {1}".format(time_plus, w_plus)
        return (w_minus, w_plus)
    
    def surface_wind(self, interp=True):
        """Gets the surface winds for an overpass.
        
        interp [True] controls whether to interpolate
        between the nearest files, or just take
        the absolute closest file
        """
        try:
            surf = ReadWinds.get_surface(self, interp=interp)
        except IOError: # file doesn't exist
            surf = Wind((0,0),0)
        except Exception as e:
            print "Unexpected Exeption:", e
            surf = Wind((0,0),0)
        return surf
    
    def write(self):
        """Writes overpass information to a csv-formatted string """
        try:
            vals_list = [self.short, self.time.hyphen,
                        self.MERRA_beginning.u, self.MERRA_beginning.v,
                        self.MERRA.u, self.MERRA.v,
                        self.MERRA_interp.u, self.MERRA_interp.v,
                        self.ECMWF_old.u, self.ECMWF_old.v,
                        self.ECMWF.u, self.ECMWF.v,
                        self.GEM.u, self.GEM.v,
                        self.Average.u, self.Average.v,
                        self.surface.u, self.surface.v,
                        self.stability_old, self.a_old,
                        self.stability, self.a,
                        self.LiteFile, self.FullFile]
        except AttributeError:
            raise
        
        return ','.join(map(str, vals_list)) + '\n'
    
    @staticmethod
    def new(source, time, full_file, lite_file):
        """Creates a new overpass and gets wind data.
        
        Takes all necessary data from the source and time, and
        reads the wind data after constructing a Time instance.
        
        If used in combination with write() method, this is
        very useful for getting new overpasses
        
        Args:
            source: PointSource
            time: Time
            full_file: absolute file path to OCO-2 full file
            lite_file: absolute file path to OCO-2 lite file
        
        Returns:
            Overpass instance
        """
        overpass_name = source.short + time.strftime("%Y%m%d")
        time_inst = Time(time, source)
        self = Overpass(time_inst)
        winds = AllWinds(time_inst)
        winds.get_winds()
        self.ECMWF = winds.ECMWF
        self.MERRA = winds.MERRA
        self.MERRA_interp = winds.MERRA_interp
        self.MERRA_beginning = winds.MERRA_beginning
        self.GEM = winds.GEM
        self.ECMWF_old = winds.ECMWF_old
        self.Average = winds.Average
        self.Average_old = winds.Average_old
        self.surface = winds.surface_wind
        self.stability = winds.stability
        self.stability_old = winds.stability_old
        self.a = winds.a
        self.a_old = winds.a_old
        self.FullFile = full_file
        self.LiteFile = lite_file
        return self