#!/bin/bash

# The following is an example of using the script map.py to make
#  Google Earth maps of GMAT Orbits from the command line

echo "Running test command:"
echo 'python map.py -w 5 -o "test.kmz" -c A9FF0012 "/home/dan/GMATData/DataFiles/16Hour0CR.txt"'
python map.py -w 5 -o "test.kmz" -c A9FF0012 "/home/dan/GMATData/DataFiles/16Hour0CR.txt"