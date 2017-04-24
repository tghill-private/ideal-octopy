"""
Module Sources.py

This module exists to contain global variables for each source (PointSource instance)
to contain the variables to one module.

Import this module to access the sources using dot notation.

Sources are initialized from the csv files
    'ModelData/EmissionsList.csv'
    'ModelData/EmissionsListSecondary.csv'
"""

import os

import PST
import Units
import data


class PointSourceContainer(object):
    """A class for holding all PointSource objects, as intialized
    from the list as pointed to be data.sources
    """ 
    units = PST.PointSource._emitter_list_units
    def __init__(self, file_name=data.sources, secondary_file_name=data.secondary):
        """Initializes PointSource instances from the given file_name
        
        Makes each source in the list a class attribute. Calling include()
        method after will make each source a module-level global variable.
        
        Attributes:
        * file_name: str, the file name the sources come from
        * secondary_file_name, the file the secondary sources come from
        * all_sources: list of all PointSource instances that were created
        * secondary_sources: list of the secondary sources created
        """
        self.file_name = file_name
        self.secondary_file_name = secondary_file_name
        self.all_sources = self._initialize_sources()
        self.secondary_sources = self._initialize_secondary()
        
    def _initialize_sources(self):
        """Helper method to initialize sources from the main csv file"""
        units = PointSourceContainer.units
        source_list = []
        if not os.path.exists(self.file_name):
            raise IOError("The file %s does not exists" % self.file_name)
        
        try:
            source_file = open(self.file_name)
        except:
            print "Exception Raised: see message"
            raise
        file_heading = source_file.readline()
        next_line = source_file.readline()
        while next_line != "":
            temp = next_line.split(',')
            name = temp[0]
            loc = temp[1]
            lon = float(temp[2])
            lat = float(temp[3])
            emissions_2014 = float(temp[4])
            emissions_2015 = float(temp[5])
            emissions_2016 = float(temp[6])
            average_emissions = (emissions_2014 + emissions_2015 + emissions_2016)*(1./3.)
            yearly_emissions = {2014: Units.SciVal(emissions_2014, units),
                                2015: Units.SciVal(emissions_2015, units),
                                2016: Units.SciVal(emissions_2016, units)
                                }
            var_name = temp[7]
            height = float(temp[8])
            monthly_factors = map(lambda x: float(x),temp[9:21])
            full_name = '{0}, {1}'.format(name,loc)
            source = PST.PointSource(var_name,lat,lon,full_name,average_emissions,yearly_emissions,height)
            source.monthly_factors = monthly_factors
            setattr(self,var_name,source)
            source_list.append(source)
            next_line = source_file.readline()
        
        source_file.close()
        return source_list
    
    def _initialize_secondary(self):
        """Helper method to initializes sources from secondary source file"""
        units = PointSourceContainer.units
        try:
            secondary_sources = open(self.secondary_file_name)
        except IOError as error:
            err_string = "Unable to open file {0}".format(self.secondary_file_name)
            raise IOError(err_string)
            
        secondary_list = []
        
        headers = secondary_sources.readline()
        line = secondary_sources.readline()
        while line!="":
            line_list = line.split(',')
            name=line_list[0]
            parent = line_list[1]
            parentSource = getattr(self,parent)
            lat=float(line_list[2])
            lon=float(line_list[3])
            emissions = float(line_list[4])
            yearly_emissions = {2014: Units.SciVal(emissions, units),
                                2015: Units.SciVal(emissions, units),
                                2016: Units.SciVal(emissions, units)
                                }
            height = float(line_list[5])
            source = PST.PointSource(name,lat,lon,name,emissions,yearly_emissions,height)
            setattr(self,name,source)
            secondary_list.append(source)
            parentSource.secondary.append(source)
            line=secondary_sources.readline()
        secondary_sources.close()
        return secondary_list

    
    def __repr__(self):
        return "PointSourceContainer('%s')" % self.file_name
    
    def __len__(self):
        return len(self.all_sources)
    
    def __iter__(self):
        for x in self.all_sources:
            yield x
    
    def __getitem__(self,value):
        if hasattr(self,value):
            return getattr(self,value)
        else:
            raise AttributeError("PointSourceContainer object has no attribute '{0}'".format(value))
    
    def include(self):
        for source in self.all_sources:
            key = source.short
            globals()[key] = source
        for secondary_source in self.secondary_sources:
            key = secondary_source.short
            globals()[key] = secondary_source


Sources = PointSourceContainer()
Sources.include()