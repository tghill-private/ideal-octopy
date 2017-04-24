"""
    Module Colours.py

    Module for mapping values to colours, and making colour bars.
    
    class Colour represents a value x as an RGB colour
    function colour_bar creates a colour bar saved as a png image
"""

import numpy
import colorsys
import io
import StringIO

from matplotlib import pyplot as plt
import matplotlib as mpl

import KML
import Formats

class Colour(object):
    """Represents a numeric value x as an RGB colour.
    
    A value x is mapped linearly from a numeric value in the
    range [vmin, vmax] to a hue in the range [hmin, hmax], with
    saturation 1.0 and luminance 1.0.
    
    Attributes:
        vmin: Minimum value used in mapping
        vmax: Maximum value used in mapping
        hmin: Minimum hue used in mapping
        hmax: Maximum hue used in mapping
        s: Saturation (default 1.0)
        b: Brightness or Luminance (default 1.0)
        a: Transparency (default 'ff', fully opaque)
        value: internal storage of x
        rgb: Tuple of floats (0-1) (r, g, b)
        hue: hue resulting from mapping
    """
    _recognized = ['r','g','b','a']
    GE = '%a%b%g%r'
    plt = '#%r%g%b'

    def __init__(self, x, vmin=380, vmax=410, hmin=240., hmax=0., a='ff'):
        """Stores the HSL and RGB values of value x.

        A value x in the range [vmin, vmax] is mapped linearly to a
        hue value in the range [hmin, hmax]. That is, if x a factor of
        'k' along from vmin to vmax, the hue is exactly the same factor
        of 'k' along from hmin to hmax. This looks like:
        
        |---------x-------------------------|
        vmin      |                         vmax
        |---------h-------------------------|
        hmin                                hmax
        """
        if x>vmax:
           x=vmax
        elif x<vmin:
             x=vmin

        self.vmin = vmin
        self.vmax = vmax
        self.hmin = hmin
        self.hmax = hmax

        self.s = 1. # saturation
        self.b = 1. #brightness
        self.a = a

        self.value = self._get_colour(x)


    def cformat(self, fmt):
        """Returns the hex string corresponding to a colour.

        Args:
            fmt: string specifying how to format the colour
            
            fmt is specified like datetime.strftime with:
            %r -> red hex string ('00' to 'ff')
            %g -> green hex string ('00' to 'ff')
            %b -> blue hex string ('00' to 'ff')
            %a -> alpha hex string ('00' to 'ff')
        
        Returns:
            fmt
        
        Raises:
            ValueError if an unrecognized character is specified

        Example:
        c = Colour(50, vmin=0, vmax=100) # green
        c.cformat("#%r%g%b") ->"#00ff00"
        """
        replacement_keys = ['%'+char for char in Colour._recognized]
        r,g,b = map(lambda n: hex(int(255*n))[2:].zfill(2), self.rgb)
        replacement_values = [r, g, b, self.a]
        # replace all occurences of %r, %g, %b, %a with their values
        for key,val in zip(replacement_keys, replacement_values):
            fmt=fmt.replace(key, val)

        escaped = "".join(fmt.split("%%"))
        if "%" in escaped:
            ind = escaped.find("%")
            raise ValueError("Unrecognized format '%s'" % escaped[ind:ind+2])

        fmt.replace("%%","%")
        return fmt

    def _get_colour(self,x):
        """Calculates the hue and rgb values for value x
        
        This is where the value is internally converted to an
        (r, g, b) tuple. For public access to rgb values,
        use rgb attribute or cformat method
        
        Args:
            x
        Returns:
            x
        """
        full_circle = 360.
        hue = float(self.hmax-self.hmin)/float(self.vmax-self.vmin)*(x-self.vmax) + self.hmax
        normalized_h = float(hue)/full_circle % 1.
        self.hue = normalized_h
        self.rgb = colorsys.hsv_to_rgb(normalized_h,self.s,self.b) # converts hsv to rgb
        self.value = x
        return x

default_fontsize = 12
def colour_bar(file_name, cmin=KML.default_cmin, cmax=KML.default_cmax, label='Xco$_2$ (ppm)',
                hmin=240., hmax=0., fontsize=default_fontsize):
    """Creates a colour bar png file with limits cmin and cmax.

    The colour bar is saved as file_name, with a label underneath with the
    text of the label argument. The colours are calculated using
    class Colour. See class documentation for details on colour mapping.

    This is implemented by creating a matplotlib figure and plotting
    individual points, with the colour specified as the hex string
    '#rrggbb'
    
    Args:
        file_name: str, the file name to save the resulting png image as;
            if empty string "", does not save a file.
        cmin: The minimum value plotted on colour bar (int or float)
        cmax: The maximum value plotted on colour bar (int or float)
        label: The label added below the colour bar (string)
        hmin: Minimum hue to use in mapping
        hmax: Maximum hue to use in mapping
    
    Returns:
        file_name: The file path the colour bar was saved as (String) if
            file_name was not ""; if file_name was "", returns a ByteIO
            object containing the image in png format.
    """
    mpl.rcParams['mathtext.default'] = 'regular'
    
    x_ticks = numpy.linspace(cmin,cmax,5) # where to put ticks on colour bar

    nrows, ncols = (50,250) # shape of plot

    values = numpy.linspace(cmin, cmax, ncols) # values to plot colours for

    fig = plt.figure(figsize=(5,1.1))
    ax1 = fig.add_subplot(111)

    for col in range(ncols):
        val = values[col]
        colour_obj = Colour(val, vmin=cmin, vmax=cmax, hmin=hmin, hmax=hmax)
        colour = colour_obj.cformat(Colour.plt)
        for row in range(nrows):
            x = cmin + (float(cmax-cmin)/float(ncols))*col
            ax1.plot(x, row, color=colour, marker="s", markeredgecolor=colour)

    ax1.set_xticks(x_ticks)
    ax1.tick_params(axis='y', left='off', right='off',
                    labelleft='off', labelright='off')
    ax1.tick_params(labelsize=fontsize)
    ax1.set_xlabel(label, fontsize=fontsize, fontname=Formats.globalfont)

    if abs(cmin)>10 and abs(cmax)>10:
        ax1.set_xlim(int(cmin),int(cmax))
    else:
        ax1.set_xlim(cmin,cmax)
    
    Formats.set_tickfont(ax1)
    
    plt.tight_layout()
    if file_name:
        plt.savefig(file_name, dpi=600, bbox_inches='tight')
        return file_name
    else:
        file = io.BytesIO()
        cbar = plt.savefig(file, format='png', dpi=600,bbox_inches='tight')
        return file