"""
Module Filter.py

This module filters overpasses by distance along and perpendicular to wind.

This was used when filtering all 1 degree overpasses to only keep the
ones that could potentially be useful.
"""

import numpy

import Geometry
import PST
import timing
import File


def check_distance(overpass, wind_source="MERRA", max_distance=35.e3, delta=20, epsilon=10.e3):
    """checks the along-wind and across-wind distance for an overpass.
    
    If both distances are less than max_distance (default 35km),
    the overpass passes and it returns True. Else returns False.
    
    Args:
    * overpass: an Overpass instance
    * wind_source: a string corresponding to a wind source to use,
                    one of "MERRA", "GEM", or "ECMWF"
    * max_distance [35.e3]: a float giving the maximum along-wind
                    distance to consider overpasses with
    * epsilon [10.e3]: a float giving the minimum y-distance to
                    keep the overpass. A large minimum y-distance
                    means missing data in the plume
    """
    print "Opening full file for %s" % overpass.info
    full_file = File.full(overpass)
    wind = getattr(overpass, wind_source)
    coordinate = Geometry.CoordGeom(wind)
    y_distances = [abs(coordinate.coord_to_wind_basis(overpass.lat, overpass.lon, full_file.retrieval_latitude[i], full_file.retrieval_longitude[i])[1]) for i in range(len(full_file))]
    
    min_dist = min(y_distances)
    min_location = numpy.where(y_distances==min_dist)[0][0]

    if min_dist>epsilon:
        x=-1
    else:
        x = coordinate.coord_to_wind_basis(overpass.lat, overpass.lon, full_file.retrieval_latitude[min_location], full_file.retrieval_longitude[min_location])[0]
    
    direction_check = x>0
    if not direction_check:
        print "Failed direction check"
    distance_check = (min_dist <= epsilon) and (x<=max_distance)
    if not distance_check:
        print "Failed distance check:"
    
    return direction_check and distance_check
    
@timing.timer
def main(overpasses, fname, **kwargs):
    """Writes all good overpasses to file name with fname.
    
    Uses check_distance to define what is a good
    overpass, and writes a csv file with only the good
    overpasses in it
    """
    with open(fname, "w") as output:
        output.write(PST.Overpass.header)
        for overpass in overpasses:
            check = check_distance(overpass, **kwargs)
            print check
            if check:
                output.write(overpass.write())
            
            
if __name__ == "__main__":
    import Overpasses
    main(Overpasses.all_overpasses, "../WindData/filtered_1deg_overpasses_10km.csv")