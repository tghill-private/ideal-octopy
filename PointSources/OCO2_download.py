"""
  Module OCO2_download.py
  
  Module for downloading both full and lite OCO-2 data files.
  
  Replace the list 'files' with the files you wish to download, and run
  the script. Works for both full and lite files, saving them in the
  right directories and folder structures
  
  Full files are saved in
    "/wrk7/SATDATA/OCO-2/Full/v07r/[YYYY]/[day of year]/"
  
  Lite files are saved in
    "/wrk7/SATDATA/OCO-2/Lite/v07b/[YYYY]/[mm]/"
    
    or, if you are familiar with datetime string formatting
    Full Files: "/wrk7/SATDATA/OCO-2/Full/v07r/%Y/%j/"
    Lite Files: "/wrk7/SATDATA/OCO-2/Lite/v07b/%Y/%m/"
  
  This is partly based on the NASA automatically generated download script,
  but has been customized to download both lite and full files to the
  directories we want to keep them in, and to check the quality of the
  file after downloading.
"""

from urllib import urlretrieve
from urlparse import urlparse
import os
import datetime
import sys
from time import time

import h5py


# Change this to be the files you want to download
files = []

# file name for the list of bad files
log_file = 'download_bad_urls.txt'

# directories the files should save to
full_file_dir = '/{dir}/SATDATA/OCO-2/Full/v07r/%Y/%j/' # dir is wrk6 or wrk7
lite_file_dir = "/wrk7/SATDATA/OCO-2/Lite/v07b/%Y/"

# format of lite and full file dates for parsing to datetime
full_dt_fmt = '%y%m%d'
lite_dt_fmt = '%y%m%d'

_start_mssg = """

Downloading %d files from %s
================================================="""
_end_mssg = """

=================================================
Downloaded %d files
Logged %d bad files in %s
"""

def save_file(url, dir):
    """Saves the file at location url to the directory dir.
    
    save_file maintains the name of the file from the url"""
    fname = os.path.split(url)[1]
    print "\nDownloading: " + url
    full_name = os.path.join(dir, fname)
    
    try:
        urlretrieve(url, full_name, reporthook)
    
    except Exception as e:
        print "Error downloading {0}: error: {1}".format(url, e)
        return None
    else:
        return full_name
        
def reporthook(count, block_size, total_size):
    """reporthook keeps track of the status of the download"""
    global start_time
    if count == 0:          # first pass, initialize the time
        start_time = time()
        return
    duration = time() - start_time
    size     = int(count * block_size)
    speed    = int(size / (1024 * duration))
    percent  = min(int(count * block_size * 100 / total_size),100)
    sys.stdout.write("\r...%d%% @ %d KBytes/second, Download time: %d  seconds" % \
               (percent, speed, duration))
    sys.stdout.flush()
    

def main(file_list, log):
    """downloads each file in file_list, writing bad files to text file log
    
    Checks the quality of each file by attempting to open it
    after downloading. If it encounters an exception, it writes
    the file name to the text file with name log.
    """
    if file_list==[]:
        raise IndexError("No files were given to download")
    bad_urls = []
    parsed_url = urlparse(file_list[0])
    domain_to_print = parsed_url.scheme + "://" + parsed_url.netloc
    print _start_mssg % (len(file_list), domain_to_print)
    
    for url in file_list:
        if url.endswith("h5"):
            dt = datetime.datetime.strptime(url.split('_')[5], full_dt_fmt)
            dir = 'wrk6' if int(dt.year)>=2017 else 'wrk7'
            dir_fmt = full_file_dir.format(dir=dir)
            quality_test_field = "/Metadata"
            
        elif url.endswith("nc4"):
            dir_fmt = lite_file_dir
            dt = datetime.datetime.strptime(url.split("_")[3], lite_dt_fmt)
            quality_test_field = "sounding_id"
            
        else:
            val_err = "Couldn't recognize form of url %s to parse date" % url
            raise ValueError(val_err)
            
        save_dir = dt.strftime(dir_fmt)
        
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)
        
        if os.path.isfile(os.path.join(save_dir, os.path.split(url)[1])):
            print 'File already exists'
        else:
            try:
                saved_file = save_file(url, save_dir)
                F = h5py.File(saved_file)
                metadata = F[quality_test_field]
                F.close()
            
            except Exception as e:
                print "Could not save file from {0}".format(url)
                print e
                bad_urls.append(url)
    
    with open(log, "a") as output_file:
        output_file.write('\n'.join(bad_urls))
    print _end_mssg % (len(file_list), len(bad_urls), "/".join([os.getcwd(),log]))
    print "\nDone"

if __name__=="__main__":
    import download_20171904 as dwnld
    # main(["http://co2web.jpl.nasa.gov/thredds/fileServer/OCO-2/B7305Br_r02/2017/01/06/LtCO2/oco2_LtCO2_170106_B7305Br_170223011050s.nc4"], log_file)
    n = 50
    sep = [dwnld.full[i:i+n] for i in xrange(0, len(dwnld.full), n)]
    for files in sep[1:]:
        main(files, log_file)