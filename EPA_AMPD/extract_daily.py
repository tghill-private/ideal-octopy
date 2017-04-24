#!/usr/bin/env python
"""
extract_daily.py extracts daily emissions data for given sources.

The raw downloaded EPA data is organized into files by state. This is
inconvenient for finding the emissions from a single source of interest.

This script writes a new file containing only the data from a certain
source. Arguments are the source name as it appears in the AMPD files,
the state name (two-letter short form), and the name of the file to make.
___________________________________________________________________

Example:

extract_daily.py "Gen J M Gavin" oh Gavin_yearly.csv
"""

import argparse
import os
import csv
import datetime as dt

hourly_emissions_dir = '/wrk4/nassar/EPA_Emissions/Hourly/'
daily_emissions_dir = '/wrk4/nassar/EPA_Emissions/Daily/'

file_header = '"STATE","FACILITY_NAME","ORISPL_CODE","UNITID","OP_DATE",\
"OP_HOUR","OP_TIME","GLOAD (MW)","SLOAD (1000lb/hr)","SO2_MASS (lbs)",\
"SO2_MASS_MEASURE_FLG","SO2_RATE (lbs/mmBtu)","SO2_RATE_MEASURE_FLG",\
"NOX_RATE (lbs/mmBtu)","NOX_RATE_MEASURE_FLG","NOX_MASS (lbs)",\
"NOX_MASS_MEASURE_FLG","CO2_MASS (tons)","CO2_MASS_MEASURE_FLG",\
"CO2_RATE (tons/mmBtu)","CO2_RATE_MEASURE_FLG","HEAT_INPUT (mmBtu)",\
"FAC_ID","UNIT_ID"\n'

input_datefmt = '%Y-%m-%d'
csv_datefmt = '%m-%d-%Y'

def extract(source_name, state, output_file):
    """Extracts data for the given source to its own file"""
    years = ['2014', '2015', '2016']
    with open(output_file, 'w') as output:
        write_header = True
        for year in years:
            fname = '%s/DLY_%s%s.csv' % (year, year, state)
            emissions_file = os.path.join(daily_emissions_dir, fname)
            lines_copied = 0
            print "Copying data from file", emissions_file
            with open(emissions_file, 'r') as emissions_csv:
                reader = csv.reader(emissions_csv, delimiter=',')
                header = reader.next()
                if write_header:
                    output.write(','.join(header) + '\n')
                    write_header = False
                source_index = 1
                date_index = 4
                for row in reader:
                    source = row[source_index]
                    if source==source_name:
                        output.write(','.join(row) + '\n')
                        lines_copied+=1
            print "Copied %d lines" % lines_copied
    output_file_path = os.path.realpath(output_file)
    print "Data was extracted to", output_file_path
    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source_name', help='Full source name as shown in emissions data')
    parser.add_argument('state_name', help='Short form of state the source is in (lower-case)')
    parser.add_argument('output_file', help='file path to the output file')
    args = parser.parse_args()
    extract(args.source_name, args.state_name.lower(), args.output_file)

if __name__ == "__main__":
    main()