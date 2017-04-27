"""
Plots a 2D histogram representing where the observations are
"""

import numpy as np
from matplotlib import pyplot as plt
from matplotlib import colors

import getdata

csvfile = "/home/tim/virtual/DarkSky/data/GLOBE.csv"

def hist(fname, source=csvfile, nlon=180, nlat=180, cmin=0.1, cmax=25, cmap='Blues'):
	data = getdata.read(source)
	
	xaxis = np.linspace(-180, 180, nlon)
	yaxis = np.linspace(-90, 90, nlat)
	
	fig, ax = plt.subplots()
	
	H, xedges, yedges = np.histogram2d(data.Latitude, data.Longitude, bins=(nlat, nlon))
	im = ax.pcolormesh(xaxis, yaxis, H, vmin=cmin, vmax=cmax, cmap=cmap)
	
	cbar = fig.colorbar(im, ax=ax, extend='max')
	
	ax.set_xlim(xaxis[0], xaxis[-1])
	ax.set_ylim(yaxis[0], yaxis[-1])
	
	ax.set_xlabel('Longitude')
	ax.set_ylabel('Latitude')
	
	fig.savefig(fname, dpi=600)

if __name__ == '__main__':
	hist('../hist2d.png')