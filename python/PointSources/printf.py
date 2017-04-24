"""
	Module Printf.py
	
	Module contains decorators for printing arguments and keyword arguments
	passed to a function.
	
	Main decorator used is kwinfo, which prints the keywords supplied
	to a function.
"""

def kwinfo(func):
	
	def wrapper(*args, **kwargs):
		print "Optional parameters specified:"
		for key, item in kwargs.iteritems():
			print key, item
		vals = func(*args, **kwargs)
		return vals
	
	return wrapper

def info(func):
	def wrapper(*args, **kwargs):
		print "Required parameters values:"
		for argv in args:
			print argv
			
		print "Optional parameters specified:"
		for key, item in kwargs.iteritems():
			print key, item
		vals = func(*args, **kwargs)
		return vals
	
	return wrapper

def finfo(func):

	def wrapper(*args, **kwargs):
		print "Function {0}".format(func)
		print "{0}({1})".format(func.__name__, ', '.join(map(str,args)))
		print "Optional parameters specified:"
		for argv in args:
			print argv
		for key, item in kwargs.iteritems():
			print key, item
		vals = func(*args, **kwargs)
		return vals
	
	return wrapper