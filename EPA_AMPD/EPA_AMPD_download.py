#!/usr/bin/env python
"""
Script for downloading hourly and daily EPA Air Markets Program Data (AMPD)

Data is downloaded from the ftp server ftp://ftp.epa.gov/
to the directory specified.

Unfortunately, their data is stored aggregated by state.

Hourly files are in the directory
dmdnload/emissions/hourly/monthly/,
formatted as "%Y"/%Y_{state}%m.zip"
For example, Georgia, February 2015 would be:
"2016/2016_ga02.zip"

Daily files arein the directory
dmdnload/emissions/daily/quarterly/,
formatted as DLY_{YYYY}{state}Q{quarter}.zip
For example, Alabama, 2016 Q1 would be:
"2016/DLY_2016alQ1.zip"

This script maintains the structure used on the ftp site,
storing files in subdirectories by the year.
___________________________________________________

Command Line Interface:
Arguments are the years to download data for, whether to
unzip the downloaded files, and to download hourly and/or daily files


./EPA_AMPD.py years [-u] [-H] [-D]

Args:
 * years: an arbitrary number of years to download data for
 * -u flag to unzip data. True if given, will store unzipped
        files. If not present, unzip is False, and files
        will be stored zipped.
 * -H flag to download hourly data
 * -D flag to download daily data

Example:
$ python EPA_AMPD.py 2012 2013 2014 -u -H
will download hourly emissions data for years 2012,
2013, 2014 unzipped in csv form

$ python EPA_AMPD.py 1995 1996 1997 1998 1999 2000 -D
will download daily emissions data for [1995, 2000]
inclusive in zipped form
"""

import ftplib
import zipfile
from StringIO import StringIO
import argparse
import os

# the address of the ftp server
AMPD_ftp_server = 'ftp.epa.gov'

# directory the hourly emissions are in on the ftp server
hourly_emissions_directory = 'dmdnload/emissions/hourly/monthly/'

# directory for quarterly files of daily emissions
daily_emissions_directory = 'dmdnload/emissions/daily/quarterly/'

# directory for annual files of daily emissions. This is
#  the preferred place to get daily emissions from
daily_yearly_emissions_directory = 'dmdnload/emissions/daily/annual/'
 
# local directory to download hourly emissions data to
host_hourly_emissions_dir = '/wrk4/nassar/EPA_Emissions/Hourly/'

# local directory to download daily emissions to
host_daily_emissions_dir = '/wrk4/nassar/EPA_Emissions/Daily/'


def download_hourly(years, unzip):
    """Downloads hourly emissions data from the EPA AMPD ftp site.
    
    Gets data for all years in years. If unzip is True, unzips the
    files and then saves the extracted files to our server
    """
    print "Connecting to USA EPA ftp server..."
    ftp = ftplib.FTP(AMPD_ftp_server, timeout=180*60*60)
    
    welcome = ftp.getwelcome()
    print "Welcome Message:"
    print welcome
    
    print "Logging in to server..."
    ftp.login()
    print "Logged in to server"
    
    ftp.cwd(hourly_emissions_directory)
    for year in years:
        print "Downloading %s data" % year
        ftp.cwd(year)
        save_dir = os.path.join(host_hourly_emissions_dir, year)
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)
        for fname in ftp.nlst():
            print 'Sending download request for %s...' % fname
            if unzip:
                zipdata = StringIO()
                ftp.retrbinary('RETR '+ fname, zipdata.write)
                zip_ref = zipfile.ZipFile(zipdata, 'r')
                zip_ref.extractall(save_dir)
                zip_ref.close()
                print 'Downloaded and unzipped'
            else:
                save_file = os.path.join(save_dir, fname)
                with open(save_file, 'w') as output:
                    ftp.retrbinary('RETR ' + fname, output.write)
                print 'Downloaded'
        ftp.cwd('..')
    ftp.quit()
    
def download_daily(years, unzip):
    """Downloads daily emissions data from the EPA AMPD ftp site.
    
    Gets data for all years in years. If unzip is True, unzips the
    files and then saves the extracted files to our server.
    
    Tries first to download the files from the annual directory;
    if the year doesn't exist there, it downloads the quarterly
    files.
    """
    print "Connecting to USA EPA ftp server..."
    ftp = ftplib.FTP(AMPD_ftp_server, timeout=180*60*60)
    
    welcome = ftp.getwelcome()
    print "Welcome Message:"
    print welcome
    
    print "Logging in to server..."
    ftp.login()
    print "Logged in to server"
    for year in years:
        print "Downloading %s data" % year
        yearly_directory = os.path.join(daily_yearly_emissions_directory, year)
        year_list = [s[-4:] for s in ftp.nlst(daily_yearly_emissions_directory)]
        if year in year_list:
            daily_directory = yearly_directory
        else:
            daily_directory = os.path.join(daily_emissions_directory, year)
        save_dir = os.path.join(host_daily_emissions_dir, year)
        print daily_directory
        ftp.cwd(daily_directory)
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)
        for fname in ftp.nlst():
            print 'Sending download request for %s...' % fname
            if unzip:
                zipdata = StringIO()
                ftp.retrbinary('RETR '+ fname, zipdata.write)
                zip_ref = zipfile.ZipFile(zipdata, 'r')
                zip_ref.extractall(save_dir)
                zip_ref.close()
                print 'Downloaded and unzipped'
            else:
                save_file = os.path.join(save_dir, fname)
                with open(save_file, 'w') as output:
                    ftp.retrbinary('RETR ' + fname, output.write)
                print 'Downloaded'
        ftp.cwd('/')
    ftp.quit()

    
def main():
    """Parses command line arguments and downloads appropriate files"""
    parser = argparse.ArgumentParser()
    parser.add_argument('years', help='Years to download data for', nargs='*')
    parser.add_argument('-u', '--unzip', help='Flag to unzip files', action='store_true')
    parser.add_argument('-H', '--hourly', help='Download hourly emissions', action='store_true')
    parser.add_argument('-D', '--daily', help='Download daily emissions', action='store_true')
    args = parser.parse_args()
    
    if args.daily==False and args.hourly==False:
        raise TypeError('Exactly one of "-d" or "-h" must be selected')
    elif args.daily==True and args.hourly==True:
        raise TypeError('Exactly one of "-d" or "-h" must be selected')
    elif args.daily:
        download_daily(args.years, args.unzip)
    elif args.hourly:
        download_hourly(args.years, args.unzip)
    else:
        raise TypeError('One of Daily and Hourly must be specified')

if __name__ == "__main__":
    main()