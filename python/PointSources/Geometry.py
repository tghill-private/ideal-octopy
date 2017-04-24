""" 
Module Geometry

Contains functions and classes for Geometry related
problems when working with OCO-2 sat data.

Main useful definitions are:

CoordGeom class for calculating distances in
various bases from lat/lon coordinates

SZA class for calculating model enhancements taking
into account zenith/azimuth angle corrections
"""

import sys
from math import sin, pi, acos, cos, atan2, tan
import math

import scipy
import scipy.integrate
import numpy
from osgeo import ogr

import PlumeModel

# Earth's radius in m
_earth_radius = 6.371e6


def convex_hull(points):
    """Computes the convex hull of a set of 2D points.
    
    Implements Andrew's monotone chain algorithm. O(n log n) complexity.

    Args: an iterable sequence of (x, y) pairs representing the points.
    
    Returns: a list of vertices of the convex hull in counter-clockwise order,
    starting from the vertex with the lexicographically smallest coordinates.
    """

    # Sort the points lexicographically (tuples are compared lexicographically).
    # Remove duplicates to detect the case we have just one unique point.
    points = sorted(set(points))

    # Boring case: no points or a single point, possibly repeated multiple times.
    if len(points) <= 1:
        return points

    # 2D cross product of OA and OB vectors, i.e. z-component of their 3D cross product.
    # Returns a positive value, if OAB makes a counter-clockwise turn,
    # negative for clockwise turn, and zero if the points are collinear.
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    # Build lower hull 
    lower = []
    for p in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    # Build upper hull
    upper = []
    for p in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    # Concatenation of the lower and upper hulls gives the convex hull.
    # Last point of each list is omitted because it is repeated at the beginning of the other list. 
    return lower[:-1] + upper[:-1]

    
def dist(lat1,lon1,lat2,lon2):
    """Computes the geodetic distance between two points.
    
    Function works naively, assuming Earth is a perfect sphere. Distance
    is calculated from the range between the two position vectors
    defined by (lat1, lon1) and (lat2, lon), and the radius of the Earth.
    
    Args:
        lat1, lon1, lat2, lon2: latitude and longitude of two points on
        Earth, measured in radians.
    
    Returns:
        Distance (float > 0) along the surface of the Earth (in meters)
        between points (lat1, lon1) and (lat2, lon2)
    
    Raises:
        ValueError if calculation fails
    """
    dlat = lat2-lat1
    dlon = lon2-lon1
    if dlat==0 and dlon==0:
        return 0.
    try:
        angle = acos((sin(lat1)*sin(lat2))+(cos(lat1)*cos(lat2)*cos(lon2-lon1)))
    except ValueError:
        raise ValueError("Math domain error. Coordinates given were\
                        ({0},{1}), ({2},{3})".format(lat1, lon1, lat2, lon2))
    r = _earth_radius*angle
    return r

             
class CoordGeom(object):
    """Calculates distances between points in various bases.
    
    Uses dist function to compute absolute distance between two
    points, and uses either the lat/lon grid or the direction of
    the wind to define a basis to express this distance in.
    
    Attributes:
        wind: a PST.Wind instance defining the wind speed and direction;
              direction is used to define a wind basis (x\hat, y\hat)
    """
    def __init__(self, wind):
        """Initializes CoordGeom instance from a given Wind instance, wind."""
        self.wind = wind
    
    def coord_to_dist(self, lat1d, lon1d, lat2d, lon2d):
        """Converts lat/lon coordinate pairs to North/East distance coords.
        
        The distance between (lat1d, lon1d) and (lat2d, lon2d) along the
        surface of earth (assuming it is perfectly spherical) is calculated
        using the dist function, and is expressed as the pair (x, y); x is
        distance East, y is distance North.
        
        Args: 4 angles defining two lat/lon points, measured in degrees
        
        Returns: East, North distance coordinates (x, y)
        """
        lat1=lat1d*pi/180.
        lat2=lat2d*pi/180.
        lon1=lon1d*pi/180.
        lon2=lon2d*pi/180.
        dlon = lon2 - lon1
        dlat = lat2-lat1
        r = abs(dist(lat1,lon1,lat2,lon2))
        x = dist(lat1,lon1,lat1,lon2)*numpy.sign(dlon)
        y = dist(lat1,lon1,lat2,lon1)*numpy.sign(dlat)
        return (x,y)
    
    def distance(self, lat1d, lon1d, lat2d, lon2d):
        """Calculates the absolute distance between lat/lon pair.
        
        This is an alias for the dist function, but here the
        angles must be measured in degrees not radians
        
        Args:
            4 angles defining two lat/lon points, measured in degrees
        
        Returns:
            Distance (float>0) between pair of points along Earth's surface
        """
        lat1=lat1d*pi/180.
        lat2=lat2d*pi/180.
        lon1=lon1d*pi/180.
        lon2=lon2d*pi/180.
        dlon = lon2 - lon1
        dlat = lat2-lat1
        r = abs(dist(lat1,lon1,lat2,lon2))
        return r
    
    def to_wind_basis(self, x, y):
        """Converts North/East coordinates to wind basis coordinates.
        
        The wind basis is defined as x\hat in the direction along the wind,
        and y\hat in the direction perpendicular to the wind.
        
        This basis was accidentally defined in a left handed way. That is,
        x\hat (cross) y\hat = -1. Be careful when selecting y distances in
        subsequent functions/classes/methods.
        
        Args:
            x, y: East, North coordinates
        
        Returns:
            Tuple (xw, yw); the position (x, y) re-expressed in the basis along
            and perpendicular to the wind direction
        """
        theta = atan2(y,x) # angle of the vector (x, y) wrt positive x-axis
        alpha = atan2(self.wind.v, self.wind.u) # angle of the wind vector wrt positive x-axis
        beta = alpha-theta # angle between the wind vector and position vector
        r = (x**2 + y**2)**0.5
        x_new = (r*cos(beta))
        y_new = (r*sin(beta))
        return (x_new,y_new)
    
    def coord_to_wind_basis(self, lat1, lon1, lat2, lon2):
        """Converts lat/lon pair to a distance in the wind basis.
        
        Combines methods coord_to_dist and to_wind_basis to convert
        directly from a lat/lon pair specified in degrees to a
        coordinate pair in m along and perpendicular to the wind.
        
        Args:
            4 angles defining two lat/lon points, measured in degrees
        
        Returns:
            Tuple (x, y); distance along Earth's surface in the basis
            defined by the wind. Be careful that this basis is accidentally
            defined in a left-handed sense. Recommended to use KML maps
            to identify whether you want to use positive or negative y
        """
        x,y = self.coord_to_dist(lat1, lon1, lat2, lon2)
        x_new, y_new = self.to_wind_basis(x, y)
        return (x_new, y_new)
    
    def sza_offset(self, zenith, azimuth):
        """Calculates the relative offset caused by the zenith/azimuth angles.
        
        See the math document describing these offsets in much more deail.
        When the solar zenith and azimuth angles are taken into account, the
        model plume essentially must be shifted in the (x, y) direction by an
        amount determined by the height, solar zenith angle, and solar
        azimuth angle.
        
        Args:
            zenith: zenith angle in degrees
            azimuth: azmith angle in degrees
        
        Returns:
            Tuple (x, y); the x and y offsets necessary to correct the
            model enhancements by based on the solar geometry
        """
        azimuth *= pi/180.
        zenith *= pi/180.
        h = self.wind.height
        r = h*tan(zenith)
        x = r*sin(azimuth)
        y = r*cos(azimuth)
        return self.to_wind_basis(x,y)
    
    @staticmethod
    def cartesian_distance(v1, v2):
        """Calculates the Euclidean norm of (v2-v1).
        
        This function is meant to be used for small distances (~ a few km)
        since it assumes flat ground. It uses the standard formula for
        distance between two points in a plane (L2-norm).
        
        Args:
            2 tuples of (x, y) distance coordinates
        
        Returns:
            float>0 distance between the two points assuming flat ground"""
        x1, y1 = v1
        x2, y2 = v2
        return ((x2-x1)*(x2-x1) + (y2-y1)*(y2-y1))**0.5
    
    @staticmethod
    def sgn(x):
        """Determines which half of the plane (x>0 or x<0) the angle x lies in.
        
        x is measured north-clockwise positive, the standard convention for
        cardinal bearings. This function is useful for determing forward-
        or back-scatter for solar/sensor zenith angle corrections.
        
        Args:
            Angle x measured in degrees (0<=x<=360)
        
        Returns:
            int -1 or +1; -1 means angle is in left half of plane, 180<x<=360;
            +1 means angle is in right half of plane, 0<=x<=180
        """
        if not 0<=x<=360.:
            raise ValueError("Angle must be between 0 and 360 degrees. Given {0}".format(x))
        sign = 1 if x<=180 else -1
        return sign
    
    
    @staticmethod
    def area(vertices):
        """Computes the area enclosed within a polygon with lat/lon vertices.
        
        This function is only valid for relatively small polygons, since
        it was developed to work for OCO-2 footprints (~ <=10km^2) and
        assumes a flat plane between the vertices.
        
        Args:
            vertices: the lat/lon verticies describing the vertices of
            a polygon. Length should be 4, and it is assumed that
            the polygon is closed.
            
            vertices is the shape from OCO-2 files:
            [ [lon, lat]
              [lon, lat]
              [lon, lat]
              [lon, lat] ]
        
        Returns:
            float>0, the area in m^2 enclosed by vertices, assuming
            a flat plane.
        
        Raises:
            ValueError if the vertices are not shape (4, 2)
        """
        if not numpy.shape(vertices)==(4,2):
            raise ValueError("vertices must be shape (4,2). Given\n{0}".format(vertices))
        
        latitudes = vertices[:,1]
        longitudes = vertices[:,0]
        
        def reproject(latitude, longitude):
            """Returns the x & y coordinates in meters using a sinusoidal projection"""
            from math import pi, cos, radians
            lat_dist = pi * _earth_radius / 180.0

            y = [lat * lat_dist for lat in latitude]
            x = [long * lat_dist * cos(radians(lat)) 
                        for lat, long in zip(latitude, longitude)]
            return x, y
        
        ring = ogr.Geometry(ogr.wkbLinearRing)
        
        x_r, y_r = reproject(latitudes,longitudes)
        for (x,y) in zip(x_r,y_r):
            ring.AddPoint(x,y)
        ring.AddPoint(x_r[0],y_r[0]) # close the ring
        
        poly = ogr.Geometry(ogr.wkbPolygon)
        poly.AddGeometry(ring)
        area = poly.GetArea()
        
        return area

    
    

def cosdeg(x):
    """Converts x to radians from degrees and returns cos(x_radians)"""
    angle = x * pi/180.
    return cos(angle)
    
    

class SZA(object):
    """Controls zenith and azimuth angle adjustments.
    
    Recommended to look at the diagrams, equations in the math
    documentation before reading this class.
    
    Finds the model enhancements at the "incoming" and "reflected"
    points in the plume, and averages the model enhancements at
    these two points.
    
    Attributes:
        data: The object containing OCO-2 data
        wind: Wind instance to use as direction basis
        coord: CoordGeom instance used to compute distance offsets
    """
    def __init__(self,data,wind):
        """Initializes SZA instance.
        
        Args:
            data, a File.File instance to get datasets from
            wind, a PST.Wind instance to create a CoordGeom instance
                for computing distances, etc.
        """
        self.data = data
        self.wind = wind
        coord = CoordGeom(wind)
        self.coord = coord
    
    def offsets(self,i):
        """Calculates the (x,y) offsets for incoming and reflected ray.
        
        The (x, y) offsets must be used to shift the model enhancemnts to
        account for the discrepancy between the footprint on the ground,
        and where the rays actually pass through the plume.
        
        Args:
            i, the index in the data to calcualte the offset for
        
        Returns:
            List of tuples [(xi, yi), (xr, yr)] for incoming and reflected
            ray offsets. Offsets themselves are calculated using
            CoordGeom.sza_offset method
        """
        data = self.data
        incoming_coords = self.coord.sza_offset(data.retrieval_solar_zenith[i], data.retrieval_solar_azimuth[i])
        reflected_coords= self.coord.sza_offset(data.retrieval_zenith[i], data.retrieval_solar_azimuth[i])
        return (incoming_coords, (-reflected_coords[0], -reflected_coords[1]))
    
    def V(self,x,y,u,F,a,i,correction=False):
        """Computes the model enhancements including SZA offsets.
        
        Incoming and reflected offsets are calculated with offsets
        method. These offsets are applied to the position (x, y), and
        then enhancements are calculated using PlumeModel.V function.
        
        Args:
            Args passed to PlumeModel.V (x, y, u, F, a)
            i; index in file to use for zenith and azimuth angles
            correction; A Bool controlling whether to account for
                        the angle the ray passes through the plume in.
                        No longer implemented, since we are using a
                        2D plume model and this opens up too many
                        other uncertainties.
        
        Returns:
            Enhancements in g/m^2 that are expected at ground footprint (x,y)
        """
        (x_incoming, y_incoming), (x_reflected, y_reflected) = self.offsets(i)
        V_incoming = PlumeModel.V(x+x_incoming, y+y_incoming, u,F,a)
        V_reflected = PlumeModel.V(x+x_reflected, y+y_reflected, u,F,a)
        V_corrected = 0.5*(V_incoming + V_reflected)
        
        return V_corrected
    
    def __repr__(self):
        return "SZA({0},{1}".format(self.data, self.wind.__repr__())
    
    def __str__(self):
        return "SZA({0})".format(self.data)
        
        
## Following class is able to calcualte model enhancements by
## integrating along paths from the ground to the 3D point (x,y,z)
## to calculate more accurately the expected enhancements. This was
## tested and would work properly if we used a full 3D Gaussian plume
## model. This was never actually implemented in the production Model.
# class Line:
    # """class for parameterizing a line between two (x, y, z) coordinates.
    # Uses the position (x_source, y_source, 0) as the source, and calculates
    # the parameterization of the line.
    
    # Conveniently, you can iterate over a Line instance and it will yield
    # (x, y, z) for each point on the line.
    
    # Calculates the path integral along the line for a specified scalar field,
    # or along a vertical path with x, y fixed.
    
    # This lets you calculate the additional factor due to increased path length
    # through the CO2 plume
    
    # The first point must be the ground footprint point, unless you specify
    # explicitly in the vertical_line_integral method"""
    
    # def __init__(self,p1=None, p2=None):
        # self.points = []
        # if p1:
            # self.points.append(p1)
        
        # if p2:
            # self.points.append(p2)
    
    # def add_point(self, pnt):
        # if len(self.points)==2:
            # err_msg = "This line is already associated with points {0}, {1};\
            # can not add point {2}".format(self.points[0],self.points[1],pnt)
            # raise ValueError(err_msg)
        # self.points.append(pnt)
    
    # def remove_point(self,index=-1):
        # self.points.pop(index)
    
    # def discrete(self,npoints=101):
        # """Returns a list of [x_points, y_points, z_points] where each is an
        # array of points in that dimension on the line"""
        # if len(self.points)!=2:
            # raise ValueError("Line must have two points to parameterize")
        
        # try:
            # (x1, y1, z1), (x2, y2, z2) = self.points
        # except:
            # raise
        # else:
            # x_pts = numpy.linspace(x1,x2,npoints)
            # y_pts = numpy.linspace(y1,y2,npoints)
            # z_pts = numpy.linspace(z1,z2,npoints)
            # return [x_pts, y_pts, z_pts]
    
    # def __iter__(self,npoints=101):
        # """Allows iteration over discrete points on the line.
        
        # Yields:
            # (x, y, z) for each point on the line, calculated at
            # npoints number of discrete points"""
        # x_pts, y_pts, z_pts = self.discrete(npoints)
        # for (x,y,z) in zip(x_pts, y_pts, z_pts):
            # yield (x,y,z)
    
    # def __repr__(self):
        # pts = ', '.join([str(p) for p in self.points])
        # return "Line({0})".format(pts)
    
    # def parameterize(self):
        # """Function representing the parameterization of the line.
        
        # Returns:
            # A function object 
            # L(t) = (a*t + x0, b*t + y0, c*t + z0)
            
            # Function returns the vector (x(t), y(t), z(t)"""
        # (x1, y1, z1), (x2, y2, z2) = self.points
        # a, b, c = self.coefficients()
        # def line(t):
            # return (a*t+x1, b*t+y1, c*t+z1)
        # return line
    
    
    # def coefficients(self):
        # """Calculates the coefficients (really this is the derivative) of
        # the line.
        
        # Returns:
            # Let the line be parameterized by
            # L = (a*t + x0, b*t + y0, c*t + z0)
            # self.coefficients() returns (a, b, c)"""
        # (x1, y1, z1), (x2, y2, z2) = self.points
        # vector = (x2-x1, y2-y1, z2-z1)
        # norm = numpy.linalg.norm(vector)
        # return numpy.array(vector)/norm
    
    
    # def integrate(self, function, t_lower=-numpy.inf, t_upper=numpy.inf):
        # """Calls scipy.integrate after setting up a path integral.
        
        # Args:
            # function is a scalar field F(x,y,z)
        
        # Returns:
            # scalar path integral along path described by self, through scalar
            # field F, from t_lower to t_upper
        # """
        # a,b,c = self.coefficients()
        # (x1,y1,z1) = self.points[0]
        # dt = (a*a + b*b + c*c)**0.5
        
        # def integrand(t):
            # return function(a*t+x1, b*t+y1, c*t+z1)*dt
        
        # return scipy.integrate.quad(integrand, t_lower, t_upper)[0]
    
    # def vertical_line_integral(self, function, point=0, 
                                # t_lower=-numpy.inf, t_upper=numpy.inf):
        # """Calls scipy.integrate after setting up a path integral.
        # Integrates vertically from point at index point
        
        # Args:
            # function is a scalar field F(x,y,z)
        
        # Returns:
            # scalar path integral along path described by self, through scalar
            # field F, from t_lower to t_upper
        # """
        
        # (x1,y1,z1) = self.points[point]
        
        # def vertical_function(t):
            # """ No dt since the norm of the derivative is 1, as we
            # defined the coefficient of z to be 1"""
            # return function(x1,y1,t+z1)

        # vertical_path = scipy.integrate.quad(vertical_function, t_lower, t_upper)[0]
        # return vertical_path
    
    # def airmass_factor(self,function):
        # return float(self.integrate(function))/float(self.vertical_line_integral(function))
