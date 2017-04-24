"""
module timing.py

exists to contain the decorator function timer to time existing code
"""

import time

def timer(func):
	
	def wrapper(*args, **kwargs):
		t1 = time.time()
		result=func(*args, **kwargs)
		t2 = time.time()
		delta_t = t2-t1
		print "{0} ran for {1} seconds".format(func, delta_t)
		return result
		
	return wrapper
