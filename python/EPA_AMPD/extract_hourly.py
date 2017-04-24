#!/usr/bin/env python
"""
extract_hourly.py extracts the emissions information for one source and time.

Using the arguments from the command line, the emissions for
two days before and two days after the given time for the 
indicated source are written to a separate file. These emissions
can be easily read by humans opening the csv in excel, and
by the Emissions module for use in running the model.

Command Line Interface:
Args:
    * source_name: the name as it appears in the emissions files to extract
    * state: the two letter state shortform the power plant is in
    * date: the date, formatted as YYYY-MM-DD
            (eg. July 25, 2014 --> 2014-07-25)
    * output_file: the full or relative file path to save the extracted
            emissions as. Extension should be '.csv'.
            (eg. /EPA_Emissions/Hourly/source.csv)

(no returns or raises)
___________________________________________________________________

Example:
extract_hourly.py "2015-07-30" "Gen J M Gavin" "oh" "Gavin_hourly_emissions.csv"
"""

import argparse
import os
import csv
import datetime as dt

hourly_emissions_dir = '/wrk4/nassar/EPA_Emissions/Hourly/'

file_header = '"STATE","FACILITY_NAME","ORISPL_CODE","UNITID","OP_DATE",\
"OP_HOUR","OP_TIME","GLOAD (MW)","SLOAD (1000lb/hr)","SO2_MASS (lbs)",\
"SO2_MASS_MEASURE_FLG","SO2_RATE (lbs/mmBtu)","SO2_RATE_MEASURE_FLG",\
"NOX_RATE (lbs/mmBtu)","NOX_RATE_MEASURE_FLG","NOX_MASS (lbs)",\
"NOX_MASS_MEASURE_FLG","CO2_MASS (tons)","CO2_MASS_MEASURE_FLG",\
"CO2_RATE (tons/mmBtu)","CO2_RATE_MEASURE_FLG","HEAT_INPUT (mmBtu)",\
"FAC_ID","UNIT_ID"\n'

input_datefmt = '%Y-%m-%d'
csv_datefmt = '%m-%d-%Y'

def main(time, source_name, state, output_file):
    """Writes all lines within two days of time with source name source_name
    to a separate csv named output_file.
    
    The state is needed because the files are downloaded by state from
    the EPA AMPD database. The source files are in 
    /wrk4/nassar/EPA_Emissons/Hourly
    """
    time = dt.datetime.strptime(time, input_datefmt)
    days_before = 2
    days_after = 2
    overpass_day = dt.datetime(time.year, time.month, time.day)
    min_day = overpass_day + dt.timedelta(days=-2)
    max_day = overpass_day + dt.timedelta(days=2)
    
    with open(output_file, 'w') as output:
        output.write(file_header)
        files_to_search = set([])
        for daydelta in range(-days_before, days_after + 1):
            day = overpass_day + dt.timedelta(days=daydelta)
            emissions_file_dtfmt = '%Y{state}%m.csv'.format(state=state)
            emissions_file = day.strftime(emissions_file_dtfmt)
            emi_file_dir = os.path.join(hourly_emissions_dir, str(day.year))
            emi_file = os.path.join(emi_file_dir, emissions_file)
            files_to_search = files_to_search.union({emi_file})
    
        for emissions_file in files_to_search:
            lines_copied = 0
            print "Copying data from file", emissions_file
            with open(emissions_file, 'r') as emissions_csv:
                reader = csv.reader(emissions_csv, delimiter=',')
                header = reader.next()
                source_index = 1
                date_index = 4
                for row in reader:
                    source = row[source_index].strip().strip('\t')
                    date = dt.datetime.strptime(row[date_index], csv_datefmt)
                    datecheck = min_day<=date<=max_day
                    sourcecheck = source == source_name
                    if datecheck and sourcecheck:
                        output.write(','.join(row) + '\n')
                        lines_copied+=1
            print "Copied %d lines from %s" % (lines_copied, emissions_file)
    output_file_path = os.path.realpath(output_file)
    print "Data was extracted to", output_file_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('time',
                    help='time to extract data for, formatted as YYYY-mm-dd')
    parser.add_argument('source_name',
                    help='Full source name as shown in emissions data')
    parser.add_argument('state_name',
                    help='Short form of state the source is in (lower-case)')
    parser.add_argument('output_file',
                    help='file path to the output file')
    args = parser.parse_args()
    main(args.time, args.source_name, args.state_name.lower(), args.output_file)