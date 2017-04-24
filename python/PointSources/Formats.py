ppmformat = '%.3f'

windspeedformat = '%.2f'

winddirectionformat = '%.1f'

globalfont = 'FreeSans'

def strip(L):
    """Removes all unecessary decimals from a list of strings"""
    return ['{:n}'.format(float(x)) for x in L]
    
def set_tickfont(ax, fontname=globalfont):
    ax.set_xticklabels(strip(ax.get_xticks()), fontname=fontname)
    ax.set_yticklabels(strip(ax.get_yticks()), fontname=fontname)