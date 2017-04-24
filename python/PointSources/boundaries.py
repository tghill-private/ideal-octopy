"""
Module for plotting the plume and background threshold boundaries
on the grid plots and combined plots
"""

import PlumeModel
import numpy as np
import Formats

class Boundaries(object):
    """Plots plume/background threshold boundaries for grid plots.
    
    Calculates the boundaries once, and plots the boundaries on
    and arbitrary number of axes instances.
    """
    _plume_args = {'ls':"-", "color":"k", "lw":0.5}
    _bg_args = {'ls':"-.", "color":"k", "lw":0.5}
    
    _text_x = 0.
    _text_y = 0.
    _textfont = 7

    _text_y_factor = 0.09
    
    def __init__(self,*args):
        """Constructs a Boundaries instance, with *args consisting
        of an arbitrary number of axes to plot boundaries on"""
        self.axes = args
    
    @staticmethod
    def offset_boundary(a,start=(0,0),offset=3000.,xmax=80.e3,**kwargs):
        """Calculates the boundaries for the given parameters.
        
        Args:
         * a: atmospheric stability parameter
         * start [(0,0)]: starting coordinates to plot the boundaries
                        from. If start=(100,100), the boundary
                        will be calculated as usual but plotted starting
                        at (100,100) instead of (0,0)
         * offset: background offset
         * xmax: maximum x-distance to consider as in the plume
         * kwargs: any other keyword argyments to pass to the
            PlumeModel.Background function
        
        Returns:
            Boundary: array[X, y positive boundary, y negative boundary]
        """
        X = np.linspace(start[0], xmax, 100)
        Y=[]
        X_s = []
        step = 10.
        for x in X:
            y=offset+start[1]
            x_shifted = x - start[0]
            y_shifted = y - start[1]
            if x_shifted>=0:
                while not PlumeModel.Background(x_shifted,y_shifted,1.,1.,a,offset=offset,**kwargs):
                    y+=step
                    y_shifted = y - start[1]
                    if y_shifted > 100.e3:
                        break
                X_s.append(x)
                Y.append(y)
        X_points = np.array(X_s)
        y_plus = np.array(Y)
        y_minus = 2*start[1] - np.array(Y)
        Boundary = np.array([X_points,y_plus,y_minus])/1000.
        return Boundary

    def _plot_positive(self, a, vertex, plume_thresholds, bg_thresholds, xmax, offset=3000.):
        """Plots the boundaries for positive y"""
        Boundaries_plus = [self.offset_boundary(a, start=vertex, background_factor=threshold, offset=0., xmax=xmax)[:2] for threshold in plume_thresholds]
        PlumeBoundary_endpoints=map(lambda A: A[1][-1],Boundaries_plus)
        
        Backgrounds_plus = [self.offset_boundary(a, start=vertex, background_factor=threshold, offset=offset, xmax=xmax)[:2] for threshold in bg_thresholds]
        Background_endpoints = map(lambda A: A[1][-1],Backgrounds_plus)
        
        for axis in self.axes:
            for (x,y) in Boundaries_plus:
                axis.plot(x,y,**Boundaries._plume_args)
            
            for (x,y) in Backgrounds_plus:
                axis.plot(x,y,**Boundaries._bg_args)

        
        endpoints = (PlumeBoundary_endpoints,Background_endpoints)
        return endpoints

    def _plot_negative(self, a, vertex, plume_thresholds, bg_thresholds, xmax, offset=3000.):
        """Plots the boundaries for negative y"""
        Boundaries_minus = [self.offset_boundary(a, start=vertex, background_factor=threshold, offset=0., xmax=xmax)[::2] for threshold in plume_thresholds]
        
        Backgrounds_minus = [self.offset_boundary(a, start=vertex, background_factor=threshold, offset=offset, xmax=xmax)[::2] for threshold in bg_thresholds]
        
        for axis in self.axes:
            for (x,y) in Boundaries_minus:
                axis.plot(x,y,**Boundaries._plume_args)
            
            for (x,y) in Backgrounds_minus:
                axis.plot(x,y,**Boundaries._bg_args)



    def plot(self, a, positive=(0,0), negative=(0,0),plume_thresholds=[0.10,0.25],bg_thresholds=[0.01], xmax=80.e3, ymax=50., offset=3000., fontsize=_textfont, fontname=Formats.globalfont):
        """Plots the positive and negative boundaries and text.
        
        Uses the helper methods _plot_positive and _plot_negative to plot the
        plume/background threshold boundaries on all axes associated with
        the Boundaries instance.
        
        The positive and negtive vertices are different for multiple sources,
        since we only want to plot the farthest outside boundaries
        """
        endpoints = self._plot_positive(a, positive, plume_thresholds, bg_thresholds,xmax, offset=offset)
        self._plot_negative(a, negative, plume_thresholds, bg_thresholds,xmax, offset=offset)
        plume_pts, bg_pts = endpoints
        
        thresh = plume_thresholds + bg_thresholds
        x_coord = xmax/1000. - Boundaries._text_x
        y_coords = [y for y in plume_pts + bg_pts]
        
        for axis in self.axes:
            for i,y in enumerate(y_coords):
                if y<ymax:
                    axis.text(x_coord, y, str(100*thresh[i])+"%",
                                fontsize=fontsize, fontname=fontname,
                                horizontalalignment='right',
                                verticalalignment='bottom')
        return endpoints
