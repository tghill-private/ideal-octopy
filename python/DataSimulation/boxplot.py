"""

Creates boxplots for data simulation experiment data

"""

from matplotlib import pyplot as plt
import numpy as np

ticklabelfont = 8
subtitlefont = 10
titlefont = 12
axislabelfont = 10

emissions_labels = ['6','13','25']
    
def boxplot(results, figname, title='Boxplots of Emission Estimates'):
    kwargs = {}
    boxplot_arrs= []
    for F in emissions_labels:
        arr = []
        for col in range(1, 5):
            arr.append(results[:,col][results[:,0]==F])
        boxplot_arrs.append(np.array(arr).astype(float).T)
    arr6, arr13, arr25 = boxplot_arrs
    
    fig, axes = plt.subplots(figsize=(8,4), ncols=3)
    (ax1, ax2, ax3) = axes
    
    for ax in axes:
        ax.set_xlabel('Resolution (km$^2$)', fontsize=axislabelfont)
        ax.set_xticklabels(['2x2', '4x4', '7x7', '10x10'])
        ax.tick_params(labelsize=ticklabelfont)
    ax1.boxplot(arr6)
    ax1.axhline(6, color='g')
    ax1.set_title('6 Mt/yr', fontsize=subtitlefont)
    ax1.set_ylabel('Estimated Emissions (Mt CO$_2$/yr)', fontsize=axislabelfont)
    
    ax2.boxplot(arr13)
    ax2.axhline(13, color='g')
    ax2.set_title('13 Mt/yr', fontsize=subtitlefont)
    
    ax3.boxplot(arr25)
    ax3.axhline(25, color='g')
    ax3.set_title('25 Mt/yr', fontsize=subtitlefont)
    
    plt.subplots_adjust(top=0.85, right=0.975, left=0.05)
    fig.suptitle(title, fontsize=titlefont)
    fig.savefig(figname, dpi=400)
    fig.clf()
