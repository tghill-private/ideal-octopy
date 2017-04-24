"""
Contains Namespace class for storing, accessing, and updating values
"""

_keyerror = 'Invalid Key: "%s"'
_regerror = 'Key "%s" already registered'

class Namespace(object):
    """Namespace for storing, accessing, updating key-value pairs.
    
    Acts like a dictionary, except has conditions on
    updating and adding new (key, value) pairs.
    
    Can only update with keys the Namespace instance already knows,
    unless you explicitly register the keys as valid keys.
    
    Instance Attributes:
      * attr for any attr name the object is initialized with or registered
    """
    
    def __init__(self, **kwargs):
        """Creates a Namespace instance with each key, value passed as kwargs.
        
        Registers each key given as a keyword argument name as a valid key,
        which can be updated using update() method.
        """
        for (key, value) in kwargs.iteritems():
            setattr(self, key, value)
        self._valid_keys = kwargs.keys()
        self._dict = kwargs
    
    def update(self, **kwargs):
        """Changes the value associated with each key in kwargs.
        
        Only updates values for keys it already has registered.
        
        Raises KeyError if a key is passed it does not recognize
        """
        for (key, value) in kwargs.iteritems():
            if key not in self._valid_keys:
                raise KeyError(_keyerror % key)
            else:
                setattr(self, key, value)
                self._dict.update({key:value})
    
    def register(self, **kwargs):
        """Register a new key with the instance; sets value for key.
        
        Raises KeyError if any of the keys are already recognized
        """
        for (key, value) in kwargs.iteritems():
            if key in self._valid_keys:
                raise  KeyError(_regerror % key)
            else:
                setattr(self, key, value)
                self._valid_keys.append(key)
                self._dict.update({key:value})
                
    def remove(self, key):
        """Removes the value associated with key, and key itself.
        
        To update values, use update method. This removes all
        references to the key; you would have to register key again
        if you want to use the key again.
        
        Uses delattr to remove instance attribute, and removes key
        from the list of valid keys and the internal dictionary
        representation of the object
        
        Raises KeyError if the key is not found"""
        if key not in self._valid_keys:
            raise KeyError(_keyerror % key)
        else:
            self._valid_keys.remove(key)
            delattr(self, key)
            self._dict.pop(key)
                
    def __getitem__(self, key):
        """Allows dictionary-style access: self[key] -> getattr(self, key)
        
        Raises KeyError if key is not recognized"""
        if key not in self._valid_keys:
            raise KeyError(_keyerror % key)
        else:
            return getattr(self, key)
    
    def keys(self):
        """Returns a not-ordered list of the stored keys"""
        return self._valid_keys
    
    def values(self):
        """Returns a not-ordered list of stored values"""
        vals = [getattr(self, key) for key in self._valid_keys]
        return vals
    
    def iter(self):
        """Returns a generator instance for iterating over (key, value).
        
        This acts like the dict.iteritems() method, yielding
        (key, value) for each key registered with the instance
        """
        for (key, val) in zip(self.keys(), self.values()):
            yield (key, val)
        
    def __iter__(self):
        return self.iter()
        
    def __repr__(self):
        """Represents a Namespace using __init__ signature"""
        items = ['{}={}'.format(key,val) for (key, val) in self.iter()]
        return 'Namespace(%s)' % ', '.join(items)
        
    def __str__(self):
        """pretty printing"""
        items = ['{}={}'.format(key,val) for (key, val) in self.iter()]
        return '<Namespace: %s>' % ', '.join(items)
        
    def asdict(self):
        """Returns a dictionary with all keys, values in the instance"""
        return self._dict
        
    def __eq__(self, other):
        """Defines useful equality between Namespaces.
        
        Two Namespace instances are equal if they have the ame keys,
        and the same values for all the keys.
        """
        eqcheck = isinstance(other, Namespace)
        for (key,val) in self.iter():
            if hasattr(other, key):
                eqcheck = eqcheck and other[key]==val
            else:
                eqcheck = False
        for (key,val) in other.iter():
            if hasattr(self, key):
                eqcheck = eqcheck and self[key]==val
            else:
                eqcheck = False
        return eqcheck
    
class kwhandler(object):
    """Decorator to use Namespace instance to handle keyword arguments.
    
    Decorator allows you to define keyword arguments external to the function,
    and will update the default values with any given key/value pairs.
    
    Raises KeyError if an unrecognized (key not in defaults) value is given.
    
    Example:
    ns = Namespace(a=1, b=2, c=3)
    
    @kwhandler(ns)
    def echo(**kwargs):
        return kwargs
        
    echo() => {'a':1, 'b':2, 'c':3}
    echo(a=5) => {'a':5, 'b':2, 'c':3}
    
    echo(z=0) => raises KeyError: Invalid key: "z"
    """
    def __init__(self, ns):
        """Sets default arguments based on key-values in ns.
        
        Args:
         * ns; Namespace instnace
        """
        self.namespace = ns
    
    def __call__(self, func):
        """Allows kwhandler class to be used as decorator"""
        
        def wrap(*args, **kwargs):
            """Updates Namespace with any keywords; calls decorated function.
            
            Will raise KeyError if any unrecognized keyword arguments
            are passed.
            """
            self.namespace.update(**kwargs)
            result = func(*args, **self.namespace.asdict())
            return result
            
        return wrap