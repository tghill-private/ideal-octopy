"""
Module ECMWF.py

Downloads ECMWF ERA Interim data

Uses MARS request server (using my login credentials) to download
ECMWF ERA Interim data, at 0.75x0.75 degree spatial resolution and
6h frequency.

Downloads the two files surrounding each time.

To download for specific overpasses, update the list 'time_list'
in the __name__=="__main__" block to the overpasses you want
to download.
"""

import datetime as dt
import os

from ecmwfapi import ECMWFDataServer

            
_filefmt = "/wrk8/ECMWF/%Y/EI%Y%m%d%H" # directory to save files to

# vertical levels we want data for:
_levs = "0/1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/21/22/23/24/\
            25/26/27/28/29/30/31/32/33/34/35/36/37/38/39/40/41/42/43/44/45/46/47\
            /48/49/50/51/52/53/54/55/56/57/58/59/60"

def download(times):
    """Downloads ECMWF data for each time in times.
    
    Function sends request to download the two files
    surrounding each time in times. If the files already
    exist in the directory it is saving to, it prints
    a message indicating the file already exists and
    proceeds with the next file, ignoring the current one.
    
    Args:
        times: iterable of datetime.datetime instances
    
    (returns None and does not raise Exceptions)
    """
    if not hasattr(times, "__iter__"):
        times = [times]
        
    server = ECMWFDataServer()
    vars = {'U':'131.128', 'V':'132.128',
            'Log Pressure':'152.128', "Cloud":"164.128", 
            "10m U":"165.128", "10m V":"166.128",
            "Pressure":"134.128"
            }
    _dtfmt = "%Y-%m-%d"
    _time_res=6
    _timefmt = "%H:00:00"
    for time in times:
        hr_min = _time_res*int(time.hour//_time_res)
        hr_max = hr_min + _time_res
        
        t_min = dt.datetime(time.year, time.month, time.day, hr_min)
        t_max = t_min + dt.timedelta(hours=6)
        
        for current_time in [t_min, t_max]:
            file_name = current_time.strftime(_filefmt)
            if os.path.exists(file_name):
                print "File %s already exists; skipping download" % file_name
            else:
                server.retrieve({
                "class": "ei",
                "dataset": "interim",
                "date": current_time.strftime(_dtfmt),
                "expver": "1",
                "grid": "0.75/0.75",
                "levelist": _levs,
                "levtype": "sfc/ml",
                "param": "/".join(sorted(vars.values())),
                "step": "0",
                "stream": "oper",
                "time": current_time.strftime(_timefmt),
                "type": "an",
                "target": file_name,
                })
                
if __name__ == "__main__":
    from Overpasses import *
    time_list=[Bayswater20160219,
                Bayswater20160728,
                Bayswater20161101,
                Beilun20140917,
                Callide20141020,
                Gladstone20161027,
                Gladstone20161128,
                Haramachi20150310,
                Hsinta20160725,
                JorfLasfar20150308,
                JorfLasfar20150409,
                JorfLasfar20160310,
                Liddell20160219,
                Liddell20160728,
                Liddell20161101,
                Shangdu20141008,
                Shangdu20141125,
                Shangdu20141227,
                Shangdu20150128,
                Shangdu20150301,
                Shangdu20150925,
                Shinchi20150310,
                Stanwell20141020,
                Stanwell20160923,
                Talin20160725,
                Zouxian20160918,
                Bayswater20150912,
                Bluewaters20151118,
                Bluewaters20161104,
                Brindisi20140908,
                Brindisi20141125,
                Callide20150225,
                Callide20160315,
                Callide20160721,
                Callide20160923,
                Collie20161104,
                Ghazlan20160204,
                Gladstone20141107,
                Gladstone20151009,
                Gladstone20151110,
                Liddell20161203,
                Mailiao20160108,
                Manjung20160124,
                Maziuru20150216,
                Maziuru20150710,
                Perm20160520,
                Poryong20150823,
                Rabigh20150313,
                Rabigh20160228,
                Sabiya20150312,
                Shand20150913,
                Shangdu20160305,
                Shangdu20161114,
                Stanwell20161228,
                Tesla20150812,
                Tomatoasuma20150709,
                TripoleHoms20160308,
                Waigaoqiao20150312,
                Xuangang20141013,
                Xuangang20150914,
                Xuangang20161103,
                YanbuSWCC20151226,
                Yimin20141012
                ] # Change me to download what you want
    # time_list = [Yimin20141012]
    download(time_list)