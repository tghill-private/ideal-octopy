"""
Module FindOverpasses.py

Searches through OCO-2 lite files to find overpasses close to given sources,
and optionally makes KML files for each overpass it finds.

Writes the summary text files, writes data about the overpasses to a 
csv file, and makes Google Earth KML files for the overpasses. Can
download ECMWF if it finds we are missing any data for it.
"""

# built-in modules
import os
import datetime as dt
from contextlib import nested

# other point source modules
import PST
import Sources
import Overpasses
import ECMWF
import PlumeModel
import PlotOverpasses
import KML
import File
import data

# The root folder all the subfolders will be made in
KML_root_folder = '/home/tim/PointSources/KML_files'

# where the summary text files will be saved
summary_file_subfolder = '{0}/{0}_overpasses.txt'

# where KML files will be saved (if they have default colour limits)
KML_name = '{0}/{0}_{1}.kmz'

# file the overpass information will be written to
_csv_save_loc = os.path.join(data.modeldata, 'new_search_data.csv')

_summary_file_loc = os.path.join(KML_root_folder, summary_file_subfolder)
_kml_save_loc = os.path.join(KML_root_folder, KML_name)

lite_dir = '/wrk7/SATDATA/OCO-2/Lite/v07b/{0}/'
_lat_threshold = 0.5
_lon_threshold = 0.5

def Plot(overpass, min_xco2=KML.default_cmin, max_xco2=KML.default_cmax, **kwargs):
    """Makes a KML file, with the file name automatically
    generated from the overpass name.
    
    See PlotOverpasses module for more details on this function"""
    fname = _kml_save_loc.format(overpass.short, overpass.strf8)
    return PlotOverpasses.Plot(overpass, fname, min_xco2=min_xco2, max_xco2=max_xco2, **kwargs)
    
    
def find(sources, lat_threshold=_lat_threshold, lon_threshold=_lon_threshold, min_date=None, max_date=None, download=True, min_points=0):
        """searches all OCO-2 lite files for soundings close to each source in sources.
        
        Writes a text file summarizing the overpass (number of observations,
        time, file names, etc), and writes overpass data to a CSV file.
        
        option download will download ECMWF data for the overpass date if we
        don't already have that data downloaded
        """
        print "Starting search for %d sources" % len(sources)
        print "Lat threshold: %s" % lat_threshold
        print "Lon threshold: %s" % lon_threshold
        print "Minimum points found: %d" % min_points
        print "Sources being searched:"
        for src in sources:
            print src.short
        print ""
        
        if min_date==None and max_date==None:
            year_list = ['2014','2015','2016']
        
        elif min_date==None:
            year_list = map(str, range(2014,max_date.year+1))
        
        elif max_date == None:
            year_list = map(str, range(min_date.year, 2017))
        
        else:
            year_list = map(str, range(min_date.year, max_date.year + 1))
        
        if min_date==None:
            min_date = dt.datetime(2014,1,1,0,0)
        if max_date==None:
            max_date = dt.datetime(2016,12,31,23,59)

        fnames = [_summary_file_loc.format(source.short) for source in sources]
        for s in fnames:
            dir = os.path.dirname(s)
            if not os.path.exists(dir):
                os.mkdir(dir)
        
        # use 'with' context manager so if this crashes or is stopped you don't lose all the data!
        with open(_csv_save_loc,'w') as csv_output:
            csv_output.write(PST.Overpass.header)
            with nested(*[open(nm,"w") for nm in fnames]) as open_files:
                summary_files = {source.short: open_files[i] for i,source in enumerate(sources)}
            
                for name,file in summary_files.items():
                    file.write('Overpasses for %s' % name)
                    file.write('Fields are ID, Date [Year Month Day Hour Minute Second Millisecond], Number of soundings found, Filename\n')
                
                for year in year_list:
                    print year
                    for lite_name in os.listdir(lite_dir.format(year)):
                        date = dt.datetime.strptime(lite_name.split('_')[2],'%Y%m%d')
                        if min_date<=date<=max_date:
                            # dict of name:[# nadir, # glint, # target, # other] overpasses
                            all_overpasses={source.short:[0,0,0,0] for source in sources}
                            lite_file = os.path.join(lite_dir.format(year),lite_name)
                            lite_data = File.lite(lite_file)
                            print lite_file
                            lats = lite_data.latitude
                            lons = lite_data.longitude
                            times = lite_data.date
                            lite_id = lite_data.sounding_id
                            mode = lite_data.observation_mode
                            
                            found = []
                            close_indices = []
                            
                            for k in range(len(lite_data)):
                                sounding_lat = lats[k]
                                sounding_lon = lons[k]
                                for source in sources:
                                    key = source.short
                                    lat = source.lat
                                    lon = source.lon
                                    dlat = abs(sounding_lat-lat) % 360.
                                    dlon = abs(sounding_lon-lon) % 360.
                                    if dlat<=lat_threshold and dlon<=lon_threshold:
                                        if not key in found:
                                            close_indices.append(k)
                                            found.append(key)
                                            print("Found overpass for %s: dlat=%f, dlon=%f" % (source.short,dlat, dlon))
                                        else:
                                            pass
                                        if mode[k]=="ND":
                                            all_overpasses[key][0]+=1
                                        elif mode[k]=="GL":
                                            all_overpasses[key][1]+=1
                                        elif mode[k]=="TG":
                                            all_overpasses[key][2]+=1
                                        else:
                                            all_overpasses[key][3]+=1
                            
                            for (i,source_name) in zip(close_indices,found):
                                print "Processing %s overpass" % source_name
                                nadir,glint,tg,other = all_overpasses[source_name]
                                total_points = nadir+glint+tg+other
                                if total_points<min_points:
                                    print "Only {0} points".format(total_points)
                                else:
                                    id = lite_id[i]
                                    id_info = 'ID: {0}'.format(id)
                                    type_info = 'Nadir: {0}, Glint: {1}, Target: {2}, Transition: {3}'.format(nadir,glint,tg,other)
                                    source = Sources.Sources[source_name]
                                    time = PST.Time(None,source,time_string=str(times[i]))
                                    
                                    if download:
                                        ECMWF.download(time)
                                    
                                    full = lite_data.full_file(i)
 
                                    overpass = PST.Overpass.new(source, time, full, lite_file)
                                    file_info = 'File: {0}, {1}'.format(lite_file, full)
                                    overpass_info=', '.join([id_info,str(times[i]),type_info,file_info])
                                    if full!="":
                                        csv_output.write(overpass.write())
                                        summary_file = summary_files[source_name]
                                        summary_file.write(overpass_info+'\n')
                
            print("Done")
        
        print("Saved overpass information to {0}".format(_csv_save_loc))
        return _csv_save_loc


def new_search(sources, map=True, lat_threshold=_lat_threshold, lon_threshold=_lon_threshold, min_date=None, max_date=None, min_points=0, download=False, **kml_args):
    """Searches OCO-2 data; writes overpass data and plots KML files"""
    # make directory if it doesn't exist
    if not os.path.exists(KML_root_folder):
        os.mkdir(KML_root_folder)
        
    written_csv_name = find(sources,lat_threshold=lat_threshold, lon_threshold=lon_threshold, min_date=min_date, max_date=max_date, min_points=min_points, download=download)
    overpasses = Overpasses.OverpassContainer(written_csv_name)
    
    if map:
        for overpass in overpasses:
            try:
                Plot(overpass, lat_thresh=lat_threshold, lon_thresh=lon_threshold, **kml_args)
            except Exception as e:
                print "Exception Raised and Ignored:", e
                pass

if __name__=="__main__":
    # sample small search
    new_search([Sources.Gavin, Sources.Ghent], min_date = dt.datetime(2015,7,28), max_date=dt.datetime(2015,8,15), download=False)