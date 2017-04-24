#!/usr/bin/env python
"""
Collects the quarterly, daily emissions data into yearly files.

This script searches through each year subdirectory, listing all
the quarterly files according to what state they're for. It then
creates a new file, writing the contents of the 4 quarterly files
into the new file containing a whole year of emissions.

This is designed to work on unzipped files.
"""

import os
import argparse

local_directory = '/wrk4/nassar/EPA_Emissions/Daily/'

def get_state(fname):
    return fname[-8:-6]

def collect_yearly(years):
    print 'Making yearly files for', ', '.join(years)
    for year in years:
        year_dir = os.path.join(local_directory, year)
        all_files = os.listdir(year_dir)
        by_state = {}
        for file in all_files:
            filepath = os.path.join(year_dir, file)
            state = get_state(filepath)
            if state in by_state:
                by_state[state].append(filepath)
            else:
                by_state[state] = [filepath]
        for (state, flist) in by_state.iteritems():
            flist.sort()
            yfile = 'DLY_%s%s.csv' % (year, state)
            yfilepath = os.path.join(local_directory, yfile)
            print 'Reading/writing files for', state
            with open(yfilepath, 'w') as yearly_output:
                for (i, fname) in enumerate(flist):
                    with open(fname, 'r') as qfile:
                        if i==0:
                            yearly_output.write(qfile.readline())
                        else:
                            header = qfile.readline()
                        yearly_output.write(''.join(qfile.readlines()))
            
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('years', help='years to download data for', nargs='*')
    args = parser.parse_args()
    collect_yearly(args.years)
    
if __name__ == "__main__":
    main()