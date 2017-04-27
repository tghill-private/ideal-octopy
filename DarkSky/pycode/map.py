"""
Maps DarkSky data on a rectangular lat/lon grid as validation
"""

import numpy as np
from matplotlib import pyplot as plt

import getdata

csvfile = "/home/tim/virtual/DarkSky/data/GLOBE.csv"

def map(fname, source=csvfile):
	data = getdata.read(source)
	
	fig, ax = plt.subplots()
	
	cmap = ['r', 'r', 'g', 'g', 'b', 'b', 'purple', 'purple']
	
	for j in range(len(data)):
		lat = data.Latitude[j]
		lon = data.Longitude[j]
		mag = data.LimitingMag[j]
		
		ax.plot(lon, lat, marker='.', color=cmap[mag])
	
	fig.savefig(fname, dpi=600)

if __name__ == '__main__':
	map('../validation_plot.png')
		