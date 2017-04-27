"""
Calculates and plots a 2D gridded map of the mean/median limiting magnitude
"""

from matplotlib import pyplot as plt
from mpl_toolkits import basemap
from matplotlib import colors
from matplotlib import cm
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

ticksize = 20
titlefont = 24

def map(fname, source=csvfile, nlat=180, nlon=180, cmap='gist_ncar_r', cmin=0, cmax=7):
	data = getdata.read(source)
	
	Z, latedges, lonedges, binnumber = stats.binned_statistic_2d(data.Latitude, data.Longitude, data.LimitingMag, statistic=statistic, bins=(nlat, nlon))
	fig, ax = plt.subplots(figsize=(20,15))
	
	norm = colors.Normalize(vmin=cmin, vmax=cmax)
	scalar_map = cm.ScalarMappable(norm=norm, cmap=cmap)
	
	m = basemap.Basemap(projection='robin',lon_0=0,resolution='i', ax=ax)
	m.drawcoastlines(linewidth=0.2)
	m.fillcontinents(color = 'grey', lake_color = 'white')
	
	X, Y = np.meshgrid(lonedges[:-1], latedges[:-1])
	Xf = X.flatten()
	Yf = Y.flatten()
	Zf = Z.flatten()
	
	Xf = Xf[Zf<=7]
	Yf = Yf[Zf<=7]
	Zf = Zf[Zf<=7]
	color = scalar_map.to_rgba(Zf)
	
	x, y = m(Xf, Yf)
	
	for i in range(len(Zf)):
		m.plot(x[i], y[i], marker='s', ls='', color=color[i], markersize=2)
	
	scalar_map.set_array(Zf)
	cbar = plt.colorbar(scalar_map)
	cbar.ax.tick_params(labelsize=ticksize)
	
	ax.set_title('Limiting Magnitude (%s x %s)' % (nlat, nlon), fontsize=titlefont)
	fig.savefig(fname, dpi=300)

if __name__ == '__main__':
	map('../binned_robinson_cumulative_test_dpi.png')