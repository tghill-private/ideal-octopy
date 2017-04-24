"""
Module Units.py

Introduces class SciVal to explicitly associate units
with a numeric value.
Uses class Units to performt the unit conversions.

Reads unit conversion factors from:
    ModelData/Units.csv
    ModelData/UnitPrefixes.csv

And converts from one set of units to another

Required syntax for units is:
    prefix_unit or prefix1_unit1/prefix2_unit2

For example,
'M_t/yr', 'st' are valid (megatonnes per year and short tons)
"""

import data

##  Module global constants; this is where all default units are stored
## ==========================================================================

output_units = "k_t/day" # preferred units for expressing emissions
_model_units = "g/s" # units required for input into the plume model

## ==========================================================================

class Units:
    """class Units introduces a required syntax for specifying units, and
    converts between different units.
    
    Conversion values come from the file data.units
    Prefix values come from the file data.unitprefixes
    
    Required syntax is prefix_unit/prefix_unit.
    
    Examples of valid units:
    k_t/day
    M_t/yr
    
    class is not meant to be used directly; is meant to be accessed by SciVal
    """
    def __init__(self):
        # Read the units csv and make a dictionary of conversions to SI, keys are unit names
        input_units = open(data.units)
        headers = input_units.readline()
        values = input_units.readlines()
        input_units.close()
        unit_db = {}
        for conversion in values:
            conversion = conversion.strip('\n').strip('\r').split(',')
            from_units = conversion[0]
            try:
                factor = float(conversion[2])
            except:
                print conversion
                raise
            unit_db[from_units] = factor
        
        # Read prefixes and make a dictionary of prefix factors
        # ie, k <--> 1000.0
        #     M <--> 1 000 000.0
        prefixes = open(data.unitprefixes)
        headers = prefixes.readline()
        pre_vals = prefixes.readlines()
        prefixes.close()
        prefix_db = {}
        for conv in pre_vals:
            conv = conv.strip('\n').strip('\r').split(',')
            prefix = conv[0]
            multiplier = float(conv[1])
            prefix_db[prefix]=multiplier
        
        self.valid_units = unit_db.keys()
        self.valid_prefixes = prefix_db.keys()
        
        self.prefix_db = prefix_db
        self.unit_db = unit_db
    
    
    def __getitem__(self,units):
        """Allows dictionary-style access to unit conversions.
        self[units] returns the conversion factor associated with units"""
        if '/' in units:
            top_units, bottom_units = units.split('/')
            return self[top_units]/self[bottom_units]
        if '_' in units:
            prefix, unit = units.split('_')
            if prefix not in self.valid_prefixes:
                raise ValueError('Prefix {0} is not recognized'.format(prefix))
            
            if unit not in self.valid_units:
                raise ValueError("Units {0} are not recognized".format(unit))
                
            return float(self.prefix_db[prefix]*self.unit_db[unit])
        else:
            if units not in self.valid_units:
                raise ValueError("Units {0} are not recognized".format(units))
            return float(self.unit_db[units])
    
    def convert(self,value,from_units, to_units):
        """Converts number value from units from_units to to_units"""
        # Check possible mismatches in this units; if one is per something, the other must also be per something
        if len(from_units.split('/'))!=len(to_units.split('/')):
            raise ValueError("Units must match; from units {0} do not match to units {1}".format(from_units, to_units))
        SI_value = value*self[from_units]
        output_value = SI_value/(self[to_units])
        return output_value
    
class SciVal(object):
    """Class to associate units with a numeric value.
    Uses class Units for conversions and storing units.
    
    Addition and subtraction defined between SciVal instances. Raises
    ValueError if they don't share the same units
    
    Multiplication and Division defined between SciVal instances and floats (right and left).
    All return SciVal instances except right division (float/SciVal) returns a float.
    
    Conversion done with SciVal.convert method to mutate in place, or SciVal.convert_cp to make
    a new instance with the new units.
    
    You can also convert by making a new SciVal instance of an existing one,
    with specifying different units.
    
    Or, by calling a SciVal isntance with new units.
    
    Equality
        __eq__ compares if two values are within float tolerance, and units are the same
        SciVal.equal() calls compares values after converting to the same units."""
    
    Conversions = Units()
    _float_tolerance = 1.e-8
    
    def __init__(self,value,units):
        if isinstance(value, SciVal):
            # value is already a SciVal instance, so be careful with its units
            
            if value.units != units:
                # The value should be converted to the units specified
                converted_val = value.convert_cp(units)
            
                self.value = float(converted_val.value)
                self.units = units
            
            else:
                self.value = float(value)
                self.units = units
            
        else:
            self.value = float(value)
            self.units = units
            # try to get factor to see if units are good
            self.SI = value*SciVal.Conversions[units]
    
    def convert(self,output_units):
        """Converts self to have output_units. Mutates in place, be careful. returns None"""
        new_value = SciVal.Conversions.convert(self.value, self.units, output_units)
        self.value = float(new_value)
        self.units = output_units
    
    def convert_cp(self,output_units):
        """Converts self to output units, returning the result and not mutating"""
        new_value = SciVal.Conversions.convert(self.value, self.units, output_units)
        return SciVal(new_value, output_units)
    
    def __repr__(self):
        return "SciVal({0},{1})".format(self.value, self.units)
    
    def __str__(self):
        """Prints as
            value units
        For example,
        
        print SciVal(3.14, 'M_t')
        >>> 3.14 M_t
        """
        return str(self.value) + ' ' + self.units
    
    # Operator overrides:
    def __add__(self,other):
        if not isinstance(other,SciVal):
            raise TypeError("Can not add type {0} and Units.SciVal instance".format(type(other).__name__))
        if self.units!=other.units:
            raise ValueError("Units of arguments to __add__ don't match. Units given are {0}, {1}".format(self.units, other.units))
        else:
            val = self.value + other.value
            return SciVal(val,self.units)
    
    def __sub__(self,other):
        if not isinstance(other,SciVal):
            raise TypeError("Can not add type {0} and Units.SciVal instance".format(type(other).__name__)) 
        if self.units!=other.units:
            raise ValueError("Units of arguments to __sub__ don't match. Units given are {0}, {1}".format(self.units, other.units))
        else:
            val = self.value - other.value
            return SciVal(val,self.units)
        
    def __mul__(self, multiplier):
        try:
            m = float(multiplier)
        except:
            m = False
        if type(multiplier)==int or type(multiplier)==float or type(m)==float:
            return SciVal(self.value*multiplier, self.units)
        else:
            return TypeError("SciVal objects can only be multiplied by floats or ints not {0}".format(type(multiplier).__name__))
    
    def __rmul__(self, multiplier):
        return self.__mul__(multiplier)
    
    def __div__(self,divisor):
        return self.__mul__(1./divisor)
    
    def __rdiv__(self, divisor):
        return divisor/self.value
    
    def __eq__(self,other):
        return isinstance(other, SciVal) and abs(self.value-other.value)<SciVal._float_tolerance and self.units==other.units
    
    def __float__(self):
        """Calling float(SciValInstance) separates the units from the value"""
        return self.value
    
    def round(self, n):
        """Return a SciVal instance with self.value rounded to n decimal places"""
        val = round(self.value, n)
        return SciVal(val, self.units)
    
    def __call__(self,new_units):
        return SciVal(self, new_units)
    
    def equal(self,other):
        return isinstance(other, SciVal) and abs(self.value-(other.convert_cp(self.units).value))<SciVal._float_tolerance
    
    def __ge__(self, other):
        return float(self) >= float(other)
    
    def __le__(self, other):
        return float(self) <= float(other)
    
    def __gt__(self, other):
        return float(self) > float(other)
    
    def __lt__(self, other):
        return float(self) < float(other)