"""
Script for downloading OCO2 Level 1 data

Uses my credentials:

Username: TimHill
Password: ECCC_oco2_download
"""

import os

import numpy as np
from pydap.client import open_url
from pydap.cas.urs import setup_session
import h5py

user = 'TimHill'
psswrd = 'ECCC_oco2_download'

download_keys = [
    '_FootprintGeometry_footprint_vertex_latitude',
    '_FootprintGeometry_footprint_vertex_longitude',
    '_SoundingGeometry_sounding_latitude',
    '_SoundingGeometry_sounding_longitude',
    '_SoundingGeometry_sounding_solar_azimuth',
    '_SoundingGeometry_sounding_solar_zenith',
    '_SoundingGeometry_sounding_zenith',
    '_SoundingGeometry_sounding_azimuth',
    '_Metadata_OperationMode'
    ]
    
def split_dataset(s):
    """Splits a dataset name from the format of download_keys to the
    group name and the field name.
    
    Example:
    '_FootprintGeometry_footprint_vertex_latitude' ->
                    ('FootprintGeometry', 'footprint_vertex_latitude')
    """
    key = s.strip('_')
    group = key.split('_')[0]
    dset = '_'.join(key.split('_')[1:])
    return (group, dset)


def download(file_address, output_dir):
    """Downloads OCO2 level 1 files from the OPenDAP NASA server"""
    print "Initializing session for user", user
    session = setup_session(user, psswrd)
    
    print "Finding dataset at", file_address
    dataset = open_url(file_address, session=session)
    filename = os.path.split(file_address)[1]
    
    # file path for where to save the file
    local_path = os.path.join(output_dir, filename)
    
    print "Creating local file", local_path
    output = h5py.File(local_path, 'w')
    
    try:
        print "Writing datasets to local file..."
        
        # to download all keys, use
        # for key in dataset.keys():
        for key in download_keys:
            data_arr = dataset[key][:]
            
            # problem with h5py arrays: can't store dtype='U8' arrays; see
            #  https://github.com/h5py/h5py/issues/624
            if data_arr.dtype == np.dtype('U8'):
                data_arr = data_arr.astype('S')
                
            group, dset = split_dataset(key)
            print "making dataset", '/'.join([group, dset])
            
            try:
                if group in output.keys():
                    output[group].create_dataset(dset, data=data_arr)
                else:
                    output.create_group(group)
                    output[group].create_dataset(dset, data=data_arr)
            except:
                print 'Unable to read dataset', key
                raise
    
        print "Done writing local file. Saved as", local_path
    except:
        raise
    finally:
        output.close()
    

if __name__ == "__main__":
    download('https://oco2.gesdisc.eosdis.nasa.gov/opendap/OCO2_L1B_Science.7r/2016/004/oco2_L1bScGL_08031a_160104_B7200r_160218033447.h5', '.')
