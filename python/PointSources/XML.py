"""
module XML.py reads the model default parameters from xml into a python dict.

Model default parameters are stored in the defaults.xml file. The
parameters are read into one overall dictionary, XML.defaults.
Parameters are also categorized into [background, plume, other]
for calculating ensemble uncertainties. These individual dicts
are XML.background, XML.plume, XML.other

Function get_model_defaults() returns an XML object for the
tree parsed from the default parameter file.
"""

from xml.etree import cElementTree as ElementTree

import Units
import data

default_parameter_file = data.defaults


class XMLDefaults(object):
    """Turns an ElementTree Tree into a dictionary.
    
    Reads the defaults xml file into an overall defaults
    dictionary, and dictionaries for background, plume,
    and other keyword-default value pairs.
    
    Attributes:
        defaults: a dictionary mapping keywords to default values
                for all accepted keywords
        
        background: a dictionary mapping keywords to default values
                for all background keywords
                
        plume: a dictionary mapping keywords to default values
                for all plume keywords
                
        other: a dictionary mapping keywords to default values
                for all other keywords
    """
    keyerr = 'Unexpected keyword argument "%s" encountered'
    new_keyerr = 'Keyword "%s" already has value %s'
    def __init__(self, tree):
        """Reads the ElementTree into a dictionary"""
        bool_dict = {'True':True, 'False': False}
        actions = { 'float':float,
                    'str':str,
                    'Bool':lambda b: bool_dict[b],
                    'set-int':lambda c: {int(i) for i in c[1:-1].split(',')},
                    'set-float':lambda c: {float(i) for i in c[1:-1].split(',')},
                    'None':lambda x: None,
                    'Units': lambda u: getattr(Units,u.split('.')[1]),
                    'list-empty':lambda L: []
                    }
        
        self.defaults = {}
        self.background = {}
        self.plume= {}
        self.other = {}
        
        cats = {'background':self.background,
                'plume':self.plume,
                'other':self.other}
        self.cats = cats
        
        root = tree.getroot()
        all_parameters = root.findall('.parameter')
        for param in all_parameters:
            type = param.find('type').text
            value = param.find('value').text
            cat = param.find('category').text
            key = param.items()[0][1]
            value = actions[type](value)
            cats[cat][key]=value
            self.defaults[key]=value
            setattr(self, key, value)
                
    def update(self, **kwargs):
        """Updates default values to new values.
        
        Updates the stored value in both the overall and 
        category dictionaries for each key, value pair in kwargs.
        
        Args:
            kwargs: a dictionary where all the keys are already
                    in the defaults dictionary.
        
        Raises:
            KeyError if any of the keys do not already exist
        """
        for (key,val) in kwargs.iteritems():
            if key in self.defaults:
                self.defaults[key]=val
                setattr(self, key, val)
            else:
                raise KeyError(XMLDefaults.keyerr % key)
                
            for cat in self.cats.values():
                if key in cat:
                    cat[key]=val
                    
    def __getitem__(self, value):
        """Allows dictionary style access to get values for
        a given key"""
        return self.defaults[value]
    
    def __setitem__(self, key, val):
        """Allows setting attributes using dictionary-style.
        
        Uses self.update() for actual updating; requires that
        key already exists, and just updates the value
        """
        return self.update(**{key:val})
                    
    def new_key(self, key, val):
        """Registers a new key, value pair to be accepted.
        
        Sets defaults[key]=val, without adding it to a
        specific category. After registering key, val, you
        can update the value using update() method
        """
        if key in self.defaults:
            raise new_keyerr % (key, self.defaults[key])
        else:
            self.defaults[key] = val
            setattr(self, key, val)
            

def get_model_defaults():
    """Initializes an XMLDefaults object for the default parameter file.
    
    Uses data.defaults file, uses cElementTree to
    parse the XML file, and returns a XMLDefaults instance
    for the tree
    """
    T = ElementTree.parse(default_parameter_file)
    xml = XMLDefaults(T)
    return xml
