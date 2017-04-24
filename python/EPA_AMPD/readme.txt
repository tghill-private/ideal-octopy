Documentation for /home/tim/EPA_AMPD

This directory has python scripts for downloading EPA AMPD data from the
ftp ftp://ftp.epa.gov/

This server has hourly emissions data (available in monthly files) and
daily emissions data (available in quarterly files).

The script EPA_AMPD_download.py downloads the daily and/or monthly files.

collect_yearly.py collects the daily quarterly emissions files into yearly
files, as long as they are unzipped.

The similar scripts extract_hourly.py and extract_daily.py extract daily and
hourly data for a given source into its own file, so that it's convenient
to read from in later scripts.

The scripts all take arguments from the command line, and have docstrings
explaining the arguments they take.