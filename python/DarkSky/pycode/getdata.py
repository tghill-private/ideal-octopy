"""
Module for opening Globe at Night observations data

https://www.globeatnight.org/infographic/2016

Class read opens and conveniently represents the data
"""

import csv

import numpy as np

class read(object):
	
	def __init__(self, file):
		self.file = file
		with open(file, 'r') as data:
			reader = csv.reader(data)
			headers = next(reader)
			
			self._keys = headers
			
			for key in headers:
				setattr(self, key, np.array([]))
			
			for j,row in enumerate(reader):
				if True:
					for (i, value) in enumerate(row):
						dset = getattr(self, headers[i])
						dset = np.append(dset, value)
						setattr(self, headers[i], dset)
		
		self.Latitude = self.Latitude.astype(float)
		self.Longitude = self.Longitude.astype(float)
		self.LimitingMag = self.LimitingMag.astype(int)
		
		mask = np.logical_and(self.LimitingMag>=0, self.LimitingMag<=7)
		
		for key in self.keys():
			dset = getattr(self, key)
			setattr(self, key, dset[mask])
		
		
					
	def keys(self):
		return self._keys
	
	def values(self):
		return np.array([getattr(self, key) for key in self.keys()])
	
	def __repr__(self):
		return 'read("%s")' % self.file
	
	def __str__(self):
		return '<read("%s")>' % self.file
	
	def iter(self):
		for item in self.keys():
			yield (item, getattr(self, item))
	
	def __len__(self):
		return len(self.LimitingMag)
			
if __name__ == '__main__':
	csvfile = "/home/tim/Virtual/DarkSky/data/GLOBE.csv"
	data = read(csvfile)
	print data
	print data.keys()
	print data.Latitude