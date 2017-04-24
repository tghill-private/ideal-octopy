"""
Module Overpasses.py

This module contains all the Overpass instances needed to run the model.

class OverpassContainer makes Overpass instances for every line in 
the csv file it is given, then makes the module level variables.
Importing this module with * will then import all the instances
into whatever module's namespace they are imported into, while
import the module using import Overpasses will let you access
the instances using dot notation
"""

import os
import datetime

import PST
import Sources
import data

class OverpassContainer:
    """Creates Overpass instances for each line in the csv file it is given.
    
    Defines __iter__ and __len__, so you can just use this container
    class like a list of overpasses
    """
    
    def __init__(self, location=data.overpasses):
        self.all = []
        self.source_file = location
        self.all_overpasses = self._Initialize(location)
    
    def _Initialize(self, csv_name):
        """Creates Overpass objects for each overpass, labelled as {PointSource short name}{YYYYMMDD}
        for example, Gavin20160207"""
        
        if not os.path.exists(csv_name):
            raise IOError("File %s does not exist" % csv_name)
        try:
            csv=open(csv_name,'r')
        except:
            print "Could not open %s: See message" % csv_name
            raise
        header=csv.readline()
        line=csv.readline()
        list = line.split(',')
        overpass_list = []
        while line !="":
            try:
                key = list[0]
                source = Sources.Sources[key]
            except AttributeError:
                raise AttributeError("Attribute {0} does not exist in module Sources.\nCurrent line of csv: {1}; in csv {2}".format(key, line, self.source_file))
                
            if len(list)==18:
                try:
                    date = map(int,list[1].split('-'))
                    year,month,day,hour,minute = date
                    dt = datetime.datetime(year,month,day,hour,minute)
                    time = PST.Time(dt,source)
                    merra_vector = map(float,list[2:4])
                    ecmwf_old_vector = map(float,list[4:6])
                    ecmwf_vector = (0,0)
                    gem_vector = map(float,list[6:8])
                    avg_vector = map(float,list[8:10])
                    surf_vector = map(float,list[10:12])
                    stability_class = list[12]
                    a = float(list[13].strip('\n'))
                    stability_corrected = list[14]
                    a_corrected = float(list[15])
                    lite = list[16]
                    full = list[17].strip('\n').strip('\r')
                except IndexError:
                    raise
                except Exception as exc:
                    print "An unecpexted exception was raised: see exception"
                    raise
            
            else:
                try:
                    date = map(int,list[1].split('-'))
                    year,month,day,hour,minute = date
                    dt = datetime.datetime(year,month,day,hour,minute)
                    time = PST.Time(dt,source)
                    merra_beginning = map(float,list[2:4])
                    merra_middle = map(float, list[4:6]) 
                    merra_interp = map(float, list[6:8])
                    ecmwf_old_vector = map(float,list[8:10])
                    ecmwf_vector = map(float,list[10:12])
                    gem_vector = map(float,list[12:14])
                    avg_vector = map(float,list[14:16])
                    surf_vector = map(float,list[16:18])
                    stability_class = list[18]
                    a = float(list[19].strip('\n'))
                    stability_corrected = list[20]
                    a_corrected = float(list[21])
                    lite = list[22]
                    full = list[23].strip('\n').strip('\r')
                except IndexError:
                    raise
                except Exception as exc:
                    print "An unecpexted exception was raised: see exception"
                    raise
            
            try:
                overpass = PST.Overpass(time)
                overpass.height = source.height
                overpass.MERRA_beginning = PST.Wind(merra_beginning,source.height)
                overpass.MERRA = PST.Wind(merra_middle, source.height)
                overpass.MERRA_interp = PST.Wind(merra_interp, source.height)
                overpass.ECMWF = PST.Wind(ecmwf_vector,source.height)
                overpass.ECMWF_old = PST.Wind(ecmwf_old_vector, source.height)
                overpass.GEM = PST.Wind(gem_vector,source.height)
                overpass.Average_beginning = 0.5*(overpass.MERRA_beginning + overpass.ECMWF)
                overpass.Average = 0.5*(overpass.MERRA + overpass.ECMWF)
                overpass.Average_interp = 0.5*(overpass.MERRA_interp + overpass.ECMWF)
                overpass.Average_old = 0.5*(overpass.MERRA + overpass.ECMWF_old)
                overpass.Average_hybrid = PST.Wind.construct(overpass.Average.speed, overpass.Average_beginning.bearing, overpass.height)
                overpass.surface = PST.Wind(surf_vector,source.height)
                overpass.a_elevated = PST.Stability(overpass.Average.speed,0.).a
                overpass.a_old = a
                overpass.a = a_corrected
                overpass.stability_old = stability_class
                overpass.stability = stability_corrected
                overpass.source = source
                overpass.FullFile = full
                overpass.LiteFile = lite
                try:
                    obs_mode = full.split('/')[-1].split('_')[1][-2:]
                except:
                    obs_mode = ''
                overpass.observation_mode = obs_mode
                overpass_name = source.short + time.strf8
                
                setattr(self, overpass_name, overpass)
                self.all.append(overpass)
                Sources.Sources[key].Overpasses.append(overpass)
                overpass_list.append(overpass)
                line=csv.readline()
                list=line.split(',')
                
                overpass.secondary = source.secondary
            except:
                raise
        csv.close()
        return overpass_list
    
    def __repr__(self):
        return 'Overpasses("{0}")'.format(self.source_file)
    
    def __len__(self):
        return len(self.all_overpasses)
    
    def __iter__(self):
        for x in self.all_overpasses:
            yield x
    
    def __getitem__(self,value):
        if hasattr(self,value):
            return getattr(self,value)
        else:   
            raise AttributeError("Overpasses object has no attribute {0}".format(value))
    
    def include(self):
        for overpass in self.all_overpasses:
            globals()[overpass.short_name] = overpass


Overpasses = OverpassContainer(data.overpasses)
Overpasses.include()
all_overpasses = Overpasses.all_overpasses

