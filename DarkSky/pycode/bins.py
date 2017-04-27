"""
Calculates and plots a 2D gridded map of the mean/median limiting magnitude
"""

from matplotlib import pyplot as plt
import scipy.stats as stats
import numpy as np

import getdata

csvfile = "/home/tim/virtual/DarkSky/data/archive/GaN2016.csv"

def statistic(x):
	if len(x)>0:
		val = np.mean(x)
	else:
		val = 8
	return val

def map(fname, source=csvfile, nlat=360, nlon=360, cmap='gist_ncar_r', cmin=0, cmax=7):
	data = getdata.read(source)
	
	Z, latedges, lonedges, binnumber = stats.binned_statistic_2d(data.Latitude, data.Longitude, data.LimitingMag, statistic=statistic, bins=(nlat, nlon))
	fig, ax = plt.subplots()
	
	print latedges[0]
	print latedges[-1]
	
	print lonedges[0]
	print lonedges[-1]
	
	im = ax.pcolormesh(lonedges, latedges, Z, cmap=cmap, vmin=cmin, vmax=cmax)
	cbar = fig.colorbar(im, ax=ax)
	
	ax.set_title('Limiting Magnitude (%s x %s)' % (nlat, nlon))
	
	fig.savefig(fname, dpi=600)

if __name__ == '__main__':
	map('../binned_cumulative.png')