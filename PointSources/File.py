"""
Module File.py

Opens, reads, and interprets OCO-2 lite and full data files.
"""

import numpy
import h5py
import datetime as dt
import os

import PST
import Geometry
import PlumeModel

_co2_mass = 44.01
_avogadro = 6.022e23
_molecules_to_grams = float(_co2_mass)/float(_avogadro)
_full_xco2_coefficient = 1.e6
_co2_column_coefficient = _molecules_to_grams
_full_pressure_coefficient = 0.01

allowed_bias_correction = ["retrieved", "partial", "corrected", "S31"]

# Bias correction dictionaries

# TCCON: access as TCCON[observation mode][surface type]
_TCCON={'ND': [0.9955,1.], 'GL':[0.9970,0.9990], 'TG':[0.9970,1.]}

# FOOT adjustment: access as FOOT[fp][observation mode][surface type]
_FOOT = {   '1': {'ND':[ 0.19, 0.00], 'GL':[ 0.06,-0.23], 'TG':[ 0.06, 0.00]},
            '2': {'ND':[ 0.13, 0.00], 'GL':[ 0.07,-0.07], 'TG':[ 0.00, 0.00]},
            '3': {'ND':[ 0.00, 0.00], 'GL':[-0.05,-0.13], 'TG':[-0.12, 0.00]},
            '4': {'ND':[-0.01, 0.00], 'GL':[ 0.02,-0.10], 'TG':[ 0.00, 0.00]},
            '5': {'ND':[-0.16, 0.00], 'GL':[-0.13,-0.03], 'TG':[-0.05, 0.00]},
            '6': {'ND':[ 0.11, 0.00], 'GL':[ 0.18, 0.35], 'TG':[ 0.35, 0.00]},
            '7': {'ND':[-0.21, 0.00], 'GL':[-0.13,-0.03], 'TG':[-0.03, 0.00]},
            '8': {'ND':[-0.05, 0.00], 'GL':[-0.02, 0.24], 'TG':[ 0.24, 0.00]}
        }

# FOOT2: acess as FOOT2[fp][observation mode][surface type]
_FOOT2 = {  '1': {'ND':[-0.17, 0.00],'GL':[-0.13, 0.03], 'TG':[-0.17, 0.00]},
            '2': {'ND':[-0.10, 0.00],'GL':[-0.09, 0.00], 'TG':[-0.04, 0.00]},
            '3': {'ND':[-0.02, 0.00],'GL':[-0.01, 0.02], 'TG':[ 0.02, 0.00]},
            '4': {'ND':[-0.09, 0.00],'GL':[-0.14, 0.00], 'TG':[-0.10, 0.00]},
            '5': {'ND':[ 0.04, 0.00],'GL':[ 0.00, 0.00], 'TG':[ 0.05, 0.00]},
            '6': {'ND':[ 0.03, 0.00],'GL':[ 0.06,-0.08], 'TG':[ 0.01, 0.00]},
            '7': {'ND':[ 0.13, 0.00],'GL':[ 0.09, 0.02], 'TG':[ 0.07, 0.00]},
            '8': {'ND':[ 0.18, 0.00],'GL':[ 0.21, 0.01], 'TG':[ 0.16, 0.00]}
        }

# dictionaries to get fields from
# attributes are set for (key, value)
_full_file_attrs = \
    {   'albedo_1':'/AlbedoResults/albedo_o2_fph',
        'albedo_2':'/AlbedoResults/albedo_weak_co2_fph',
        'albedo_3':'/AlbedoResults/albedo_strong_co2_fph',
        'albedo_o2_fph':'/AlbedoResults/albedo_o2_fph',
        'albedo_weak_co2_fph':'/AlbedoResults/albedo_weak_co2_fph',
        'albedo_strong_co2_fph':'/AlbedoResults/albedo_strong_co2_fph',
        'aerosol_1_aod':'/AerosolResults/aerosol_1_aod',
        'aerosol_1_type':None,
        'aerosol_2_aod':'/AerosolResults/aerosol_2_aod',
        'aerosol_2_type':None,
        'aerosol_3_aod':'/AerosolResults/aerosol_3_aod',
        'aerosol_3_type':None,
        'aerosol_4_aod':'/AerosolResults/aerosol_4_aod',
        'aerosol_4_type':None,
        'aerosol_total_aod':'/AerosolResults/aerosol_total_aod',
        'aerosol_types':'/AerosolResults/aerosol_types',
        'air_column_layer_thickness':'/RetrievalResults/retrieved_dry_air_column_layer_thickness',
        'air_column_total':None,
        'albedo_o2':'/AlbedoResults/albedo_o2_fph',
        'albedo_strong_co2':'/AlbedoResults/albedo_strong_co2_fph',
        'albedo_weak_co2':'/AlbedoResults/albedo_weak_co2_fph',
        'aod_bc':None,
        'aod_dust':None,
        'aod_ice':None,
        'aod_oc':None,
        'aod_seasalt':None,
        'aod_sulfate':None,
        'aod_total':None,
        'aod_water':None,
        'co2_column_uncert':None,
        'co2_grad_del':'/RetrievalResults/co2_vertical_gradient_delta', # *1.e6
        'corrected_co2_column':None,
        'corrected_no_fp_xco2':None,
        'corrected_xco2':None,
        'S31_xco2':None,
        'S31_co2_column':None,
        'dp':None,
        'footprints':None,
        'id':'/RetrievalHeader/sounding_id',
        'logDWS':None,
        'log_DWS':None,
        'outcome_flag':'/RetrievalResults/outcome_flag',
        'partial_co2_column':None,
        'partial_xco2':None,
        'reduced_chi_squared_o2_fph':'/SpectralParameters/reduced_chi_squared_o2_fph',
        'reduced_chi_squared_strong_co2_fph':'/SpectralParameters/reduced_chi_squared_strong_co2_fph',
        'reduced_chi_squared_weak_co2_fph':'/SpectralParameters/reduced_chi_squared_weak_co2_fph',
        'retrieval_land_fraction':'/RetrievalGeometry/retrieval_land_fraction',
        'retrieval_land_water_indicator':'/RetrievalGeometry/retrieval_land_water_indicator',
        'retrieval_latitude':'/RetrievalGeometry/retrieval_latitude',
        'retrieval_longitude':'/RetrievalGeometry/retrieval_longitude',
        'retrieval_solar_azimuth':'/RetrievalGeometry/retrieval_solar_azimuth',
        'retrieval_solar_zenith':'/RetrievalGeometry/retrieval_solar_zenith',
        'retrieval_vertex_coordinates':None,
        'retrieval_vertex_latitude':'/RetrievalGeometry/retrieval_vertex_latitude',
        'retrieval_vertex_longitude':'/RetrievalGeometry/retrieval_vertex_longitude',
        'retrieval_zenith':'/RetrievalGeometry/retrieval_zenith',
        'retrieved_co2_column':'/RetrievalResults/retrieved_co2_column',
        'retrieved_o2_column':'/RetrievalResults/retrieved_o2_column',
        'retrieved_xco2':'/RetrievalResults/xco2',
        'smoothed_corrected_co2_column':None,
        'smoothed_corrected_xco2':None,
        'smoothed_partial_co2_column':None,
        'smoothed_partial_xco2':None,
        'smoothed_retrieved_co2_column':None,
        'smoothed_retrieved_xco2':None,
        'smoothed_S31_xco2':None,
        'smoothed_S31_co2_column':None,
        'snr_o2_l1b':'/L1bScSpectralParameters/snr_o2_l1b',
        'snr_strong_co2_l1b':'/L1bScSpectralParameters/snr_strong_co2_l1b',
        'snr_weak_co2_l1b':'/L1bScSpectralParameters/snr_weak_co2_l1b',
        'surface_pressure':'/RetrievalResults/surface_pressure_fph', # *0.01
        'surface_pressure_apriori':'/RetrievalResults/surface_pressure_apriori_fph', # *0.01
        'xco2_uncert':'/RetrievalResults/xco2_uncert',
        'k':None
    }

_lite_file_attrs = \
    {   'latitude':'/latitude',
        'longitude':'/longitude',
        'time':'/time',
        'date':'/date',
        'xco2':'/xco2',
        'warn_level':'/warn_level',
        'sounding_id':'/sounding_id',
        'source_files':'/source_files',
        'file_index':'/file_index',
        'xco2_raw':'/Retrieval/xco2_raw',
        'altitude':'/Sounding/altitude',
        'footprint':'/Sounding/footprint',
        'dp':'/Retrieval/dp',
        'aod_water':'/Retrieval/aod_water',
        'aod_dust':'/Retrieval/aod_dust',
        'aod_seasalt':'/Retrieval/aod_seasalt',
        'co2_grad_del':'/Retrieval/co2_grad_del',
        'logDWS':'/Retrieval/logDWS',
        'land_fraction':'/Sounding/land_fraction',
        'psurf':'/Retrieval/psurf',
        'psurf_apriori':'/Retrieval/psurf_apriori',
        'observation_mode':'/Sounding/operation_mode'
    }

class File(object):
    """Class for opening, reading, and storing data from OCO-2 full and lite
    files.
    
    Full and Lite files are opened and read using the static methods File.full
    and File.lite"""
    # Convolution Kernel G
    G = numpy.array([   [1., 4., 7., 4., 1.],
                        [4.,16.,26.,16., 4.],
                        [7.,26.,41.,26., 7.],
                        [4.,16.,26.,16., 4.],
                        [1., 4., 7., 4., 1.]
                    ])

    
    def __init__(self, type=None, initiate=True):
        """Creates a File instance for kind of file type.
        
        Args:
          *  type = None: whether this is a full file, lite file, or just to
               store values. Default of None should be used unless you are
               specifically making a new object for a full or lite file and
               are not using the static methods full or lite.
        """
        self.type = type
        
        if initiate:
            for attr in _full_file_attrs:
                setattr(self, attr, [])

    def full_file(self,index):
        """Returns the full file associated with the data point 'index' in the lite file.
        Need to have .read() the file before finding the associated full file"""
        if self.type=="lite":
            sources = self.source_files
            file_indices = self.file_index
            lite_id = self.sounding_id

            Full_name = sources[file_indices[index]-1].split('/')[-1]
            datestr = Full_name.split('_')[3]
            year=int('20{0}'.format(datestr[:2]))
            month=int(datestr[2:4])
            day=int(datestr[4:])
            date = dt.datetime(year,month,day)
            numday=date.strftime('%j')
            fullpath = '/wrk7/SATDATA/OCO-2/Full/v07r/{0}/{1}/{2}'.format(year,numday,Full_name)
        
            try:
                F = h5py.File(fullpath)
                success = lite_id[index] in F['/RetrievalHeader/sounding_id']
                if success:
                    return_path = fullpath
                else:
                    print("Desired data does not match between lite and full file")
                    return_path = ""
            except IOError:
                print("IOError: Unable to open file {0}".format(fullpath))
                return ""
            except KeyError:
                print("Unable to open data from file {0}".format(fullpath))
                return ""
            except:
                print("Unexpected Exception Raised, returning empty string for file path")
                return ""
            return return_path

    
    def grid(self, *args):
        """Function that organizes the 1D OCO-2 data into
        the 2D type of array that we need to give to SparseFilter.
        Uses the timestamp to determine if two points are in
        the same row or not, and then takes the fp to place
        them within the row.
        
        Args:
          *  An arbitrary number of arrays to grid. Any number of
               arguments are accepted
        
        Output:
          *  A numpy.ndarray in the shape (n, 8, m) where n is the
               number of arrays passed to it in args, and m is the
               number of rows in each final gridded aray
        
        Raises:
          *  No exceptions"""
        
        for arg in args:
            if type(arg)==str:
                arg = self[arg]
        
        def SoundingTime(sounding_id):
            """Basic function to parse string to datetime.datetime.
            Not using dt.datetime.strptime since the final unit given
            is hundreds of milliseconds"""
            str_time = sounding_id[:-1]
            year=int(str_time[:4])
            month=int(str_time[4:6])
            day=int(str_time[6:8])
            hour=int(str_time[8:10])
            minute=int(str_time[10:12])
            second=int(str_time[12:14])
            millisecond=100000*int(str_time[14])
            time=dt.datetime(year,month,day,hour,minute,second,millisecond) 
            return time
        
        all_rows = [[] for arr in args]

        id = self.id
        avg_lat = self.retrieval_latitude
        avg_lon = self.retrieval_longitude

        threshold = dt.timedelta(seconds=0.1)
        dim = len(args[0])
        i=0              
        while i<dim:
            row_time = SoundingTime(str(id[i]))
            current_rows = [[0 for x in range(8)] for arr in args]
            row_length = 0
            
            k=0
            while (i+k)<dim and k<8:
                sounding_id = str(id[i+k])
                sounding_time = SoundingTime(sounding_id)
                delta = sounding_time - row_time
                if abs(delta)<abs(threshold):
                    footprint = int(sounding_id[-1])
                    if current_rows[0][footprint-1]!=0:
                        overwritten+=1
                    for ind, arr in enumerate(args):
                        current_rows[ind][footprint-1]=arr[i+k]
                    row_length+=1
                k+=1
            for ind, lst in enumerate(all_rows):
                lst.append(current_rows[ind])
            i+=row_length
        return numpy.array(all_rows)
        
    @staticmethod
    def sparse_filter(*args):
        """Function for smoothing a "sparse" array using a Gaussian smoothing kernel.
        
        args is an arbitrary number of of already "gridded" arrays, meant to be 
        from OCO-2 data. They can be full, but will more likely look like:
        [ [0 0 x x x 0 0 x]
          [x x x 0 0 x x x]
          [0 0 0 0 x 0 0 0]
          [x 0 x x 0 x x x]
          ... ]
        
        Redefined convolution so that:
        * It ignores any zeros in the averaging
        * For edges/corners, it puts the center of the convolution
          kernel over the point, and just uses the part of the kernel
          that's actually over the array
        
        This would work on any n*8 array
        """
        
        G = File.G
        
        def convolve(array,kernel):
            """Definition of the convolution operator.
            Calculates the convolution as normal,
            except it ignores any zeros. That is, in both
            the sum(array[i,j]*kernel[i,j]) and sum(kernel[i,j]),
            it skips the [i,j] entry if that entry is a zero.
            If all entries are zero (which means array was the zero array),
            it returns 0 instead of raising an error.
            """
            if numpy.shape(array)!=numpy.shape(kernel):
                print("Shape must match to convolve")
                print("Shape 'array'={0}, Shape 'kernel'={1}".format(numpy.shape(array),numpy.shape(kernel)))
            rows,cols=numpy.where(array==0.)
            dim = len(rows)
            sum_weights=0
            total=0
            kern=kernel.copy()
            for i in range(dim):
                kern[rows[i],cols[i]]=0.
            normalized=numpy.sum(kern)
            if normalized==0: 
                return 0.
            else:
                averaged = (1./normalized)*numpy.sum(array*kernel)
                return averaged
      
        smoothed_arrs=[]
        for sparse_array in args:
            num_rows,num_cols = sparse_array.shape
            smoothed = numpy.zeros((num_rows,num_cols))

            smoothed[0,0]=convolve(sparse_array[:3,:3],G[2:,2:])
            smoothed[0,1]=convolve(sparse_array[:3,:4],G[2:,1:])
            smoothed[0,-2]=convolve(sparse_array[:3,-4:],G[2:,:-1])
            smoothed[0,-1]=convolve(sparse_array[:3,-3:],G[2:,:-2])

            for col in range(2,num_cols-2):
                smoothed[0,col]=convolve(sparse_array[:3,col-2:col+3],G[2:])

                smoothed[-1,0]=convolve(sparse_array[-3:,:3],G[:3,2:])
                smoothed[-1,1]=convolve(sparse_array[-3:,:4],G[:3,1:])
                smoothed[-1,-2]=convolve(sparse_array[-3:,-4:],G[:3,:4])
                smoothed[-1,-1]=convolve(sparse_array[-3:,-3:],G[:3,:3])
            for col in range(2,num_cols-2):
                smoothed[-1,col]=convolve(sparse_array[-3:,col-2:col+3],G[:3])

                smoothed[1,0]=convolve(sparse_array[:4,:3],G[1:,2:])
                smoothed[1,1]=convolve(sparse_array[:4,:4],G[1:,1:])
                smoothed[1,-2]=convolve(sparse_array[:4,-4:],G[1:,:-1])
                smoothed[1,-1]=convolve(sparse_array[:4,-3:],G[1:,:-2])
            for col in range(2,num_cols-2):
                value=sparse_array[1,col]
                smoothed[1,col]=convolve(sparse_array[:4,col-2:col+3],G[1:])
              
                smoothed[-2,0]=convolve(sparse_array[-4:,:3],G[:4,2:])
                smoothed[-2,1]=convolve(sparse_array[-4:,:4],G[:4,1:])
                smoothed[-2,-2]=convolve(sparse_array[-4:,-4:],G[:4,:4])
                smoothed[-2,-1]=convolve(sparse_array[-4:,-3:],G[:4,:3])

            for col in range(2,num_cols-2):
                smoothed[-2,col]=convolve(sparse_array[-4:,col-2:col+3],G[:4])
          
          
            for row in range(2,num_rows-2):
                smoothed[row,0]=convolve(sparse_array[row-2:row+3,:3],G[:,2:])
                smoothed[row,1]=convolve(sparse_array[row-2:row+3,:4],G[:,1:])
                smoothed[row,-2]=convolve(sparse_array[row-2:row+3,-4:],G[:,:4])
                smoothed[row,-1]=convolve(sparse_array[row-2:row+3,-3:],G[:,:3])
                for col in range(2,num_cols-2):
                    smoothed[row,col]=convolve(sparse_array[row-2:row+3,col-2:col+3],G)

          
            zero_rows,zero_cols=numpy.where(sparse_array==0)

            for i in range(len(zero_rows)):
                smoothed[zero_rows[i],zero_cols[i]]=0
            flat_array=smoothed.flatten()
            flat_array=numpy.array(filter(lambda x: x!=0,flat_array))
            smoothed_arrs.append(flat_array)
        return numpy.array(smoothed_arrs)
    
    
    def get_offset(self, overpass, wind, return_index=False):
        """
        Calculates the offset (the (x,y) distance) from the source
        to the maximum enhancement (the center of the plume)
        
        Args:
          *  overpass, a PST.Overpass instance
          *  wind, a PST.Wind instance
          *  return_index = False; optionally returns the index in
             the file with the closest point
        
        Output: 
          *  (x_offset, y_offset); the x and y distances to the 
             center plume from the source
        """
        # List [(x1, y1), (x2, y2), ...] for all points in the instance
        posns = [Geometry.CoordGeom(wind).coord_to_wind_basis(overpass.lat,overpass.lon,lat,lon) for (lat,lon) in zip(self.retrieval_latitude,self.retrieval_longitude)]
        
        # List of [V(x1, y1), V(x2, y2), ...] for all positions (xi, yi) in posns
        all_enhancements = [PlumeModel.V(x,y,wind.speed,1.,overpass.a) for (x,y) in posns]
        
        # Index of the maximum enhancement found in all_enhancements
        closest_index = all_enhancements.index(max(all_enhancements))
        
        # (x, y) distance of the max enhancement with respect to the source. This way distances are measured from the center of the plume
        x_offset,y_offset = posns[closest_index]
        
        if return_index:
            return (x_offset, y_offset, closest_index)
        else:
            return (x_offset, y_offset)
    
    def get_secondary_offset(self, overpass, wind, return_index=False, secondary_sources=None):
        
        offset_positions = []
        if secondary_sources==None:
            secondary_sources = overpass.source.secondary
        for secondary in secondary_sources:
            # List [(x1, y1), (x2, y2), ...] for all points in the instance
            posns = [Geometry.CoordGeom(wind).coord_to_wind_basis(secondary.lat,secondary.lon,lat,lon) for (lat,lon) in zip(self.retrieval_latitude,self.retrieval_longitude)]
            
            # List of [V(x1, y1), V(x2, y2), ...] for all positions (xi, yi) in posns
            all_enhancements = [PlumeModel.V(x,y,wind.speed,1.,overpass.a) for (x,y) in posns]
            
            # Index of the maximum enhancement found in all_enhancements
            closest_index = all_enhancements.index(max(all_enhancements))
            
            # (x, y) distance of the max enhancement with respect to the source. This way distances are measured from the center of the plume
            x_offset,y_offset = posns[closest_index]
            if return_index:
                offset_positions.append((x_offset, y_offset, closest_index))
            else:
                offset_positions.append((x_offset, y_offset))
        return offset_positions

    
    
    def closest_full_row(self,overpass):
        """Searches through the data in self to find where the closest
        row is to the source with no data missing (footprints 1-8 are there).
        Returns a 1-D list of the indices in the data where this occurs"""
        self.retrieval_zenith = self.retrieval_zenith[:]
        
        x_offset, y_offset, k = self.get_offset(overpass, overpass.Average, return_index=True)
        closest_id = self.id[k]
        
        gridded_id = self.grid(self.id)[0]

        target_row, target_col = numpy.where(gridded_id==closest_id)
        target_row= target_row[0]
        target_col = target_col[0]
        
        i=0
        while i<gridded_id.shape[0]:
            if target_row+i<gridded_id.shape[0] and numpy.all(gridded_id[target_row+i]!=0.):
                row_index = target_row+i
                break
            elif target_row-1>=0 and numpy.all(gridded_id[target_row-i]!=0.):
                row_index = target_row-i
                break
            i+=1
        else:
            raise ValueError("No full rows exist in the file")
        
        target_ids = gridded_id[row_index]
        file_indices = [numpy.where(self.id[:]==target)[0][0] for target in target_ids]
        return numpy.array(file_indices)

    
    def sign_zenith_angle(self,overpass):
        """takes a self object and assigns signs to the zenith angle.
        Positive for forward scatter, negative for back scatter.
        Unfortunately the retrieval_zenith field doesn't come with a sign.
        
        For nadir we assume that the first 4 footprints are forward scatter
        and last 4 are back scatter"""
        if self.type!='full':
            raise TypeError("self object must reference a full file for zenith angle")
        
        if self.observation_mode=='ND':
            # assume the sensor zenith angle has only negligible effect
            # for nadir overpasses. Only changes by < 10m on the ground
            pass

        elif self.observation_mode=='GL': 
            # non-negligble effects if it's a Glint overpass
            x_offset, y_offset, k = self.get_offset(overpass, overpass.Average, return_index=True)
            closest_id = self.id[k]
            solar_azimuth_approx = self.retrieval_solar_azimuth[k] # the solar azimuth at closest approach
            solar_location = Geometry.CoordGeom.sgn(solar_azimuth_approx) # whether sun is East (+1) or West (-1) of soundings
            sensor_location = +1
            scatter_direction = -1*sensor_location*solar_location
            
            self.retrieval_zenith = self.retrieval_zenith[:]*scatter_direction
    
    def get_data(self,*args):
        """re-opens file and returns the datasets corresponding to
        all paths in args.
        
        Raises KeyError if a path is not valid"""
        if self.file_name==None:
            raise TypeError("File object must correspond to a lite or file file to read from")
            
        if not os.path.exists(self.file_name):
            raise IOError("File {0} does not exist".format(self.file_name))
        
        try:
            open_file = h5py.File(self.file_name, "r")
        except:
            raise
        
        return_data = []
        for attr in args:
            try:
                data = open_file[attr][:]
            except KeyError:
                raise KeyError("Attribute {0} not found in {1}, for file {2}".format(attr, open_file, self.file_name))
            except:
                raise
            return_data.append(data)
        
        open_file.close()
        return return_data
    
    def quality(self,i,snr_strong_co2_min=None, chi_squared_max=None,
                albedo_min=None, albedo_max=None,
                outcome_flags={1,2}, surface_pressure_min=None,
                surface_pressure_max=None):
        """Flag to filter data by quality.
        Returns True if the point i has all parameters within the
          values specified; False if not"""
        
        snr_test = self.snr_strong_co2_l1b[i] > snr_strong_co2_min if snr_strong_co2_min else True
        chi_squared_test = self.reduced_chi_squared_strong_co2_fph[i] < chi_squared_max if chi_squared_max else True
        albedo_test_high = self.albedo_strong_co2[i]<=albedo_max if albedo_max else True
        albedo_test_low = self.albedo_strong_co2[i]>=albedo_min if albedo_min else True
        albedo_test = albedo_test_low and albedo_test_high
        outcome_test = self.outcome_flag[i] in outcome_flags
        psurf_low = self.surface_pressure[i]>=surface_pressure_min if surface_pressure_min else True
        psurf_high = self.surface_pressure[i]<=surface_pressure_max if surface_pressure_max else True
        psurf_test = psurf_low and psurf_high
        
        return snr_test and chi_squared_test and albedo_test and outcome_test and psurf_test
    
    def _append_data(self, from_file, index):
        if from_file.type=='full':
            keys = _full_file_attrs.keys()
        elif from_file.type=='lite':
            keys = _lite_file_attrs.keys()
        else:
            raise TypeError("Must be appending data from a full or lite file")
        self.attrs = keys
        for attr in keys:
            if not hasattr(self,attr):
                setattr(self,attr,[])
            try:
                getattr(self,attr).append(getattr(from_file,attr)[index])
            except Exception as e:
                print e
                
    def append_data(self, from_file, index):
        warnings.warn("Use filter or append method instead")
        return self._append_data(from_file, index)
    
    def append(self, from_file, i):
        self.attrs = _full_file_attrs
        for attr in self.attrs:
            if not hasattr(self,attr):
                setattr(self,attr,[])
            try:
                getattr(self,attr).append(getattr(from_file,attr)[i])
            except:
                raise

    def __len__(self):
        return len(self.id)
    
    def __repr__(self):
        if self.type==None:
            return "File()"
        elif self.type=='full':
            return "File.full('{0}')".format(self.file_name)
        elif self.type=='lite':
            return "File.lite('{0}')".format(self.file_name)
    
    def __str__(self):
        if self.type==None:
            return "File() instance"
        
        elif self.type=='full':
            return "File {0}".format(self.file_name)
        
        else:
            return "File {0}".format(self.file_name)
    
    def __getitem__(self,key):
        if hasattr(self,key):
            return getattr(self,key)
        else:
            raise KeyError("Key {0} does not exist in File instance {1}".format(key,self))
    
    def _array(self):
        """Calls numpy.array() on each attribute of type list for self"""
        if type=='full':
            for attr in _full_file_attrs:
                val = getattr(self, attr)
                if type(val)==list:
                    setattr(self,attr,numpy.array(val))
        
        elif type=='lite':
            for attr in _lite_file_attrs:
                val = getattr(self, attr)
                if type(val)==list:
                    setattr(self,attr,numpy.array(val))
        
        else:
            for attr in self.attrs:
                setattr(self,attr,numpy.array(self[attr]))
        return self
    
    def filter(self, **kwargs):
        """Creates a new File instance with only the points that passed the
        quality filter of self. Only meant to work on full file instances
        
        kwargs: any filtering keywords:
            snr_strong_co2_min
            albedo_min
            albedo_max
            chi_squared_max
        
        Returns:
          * File instance with the same attributes as self, but only the
            points where quality() was True. Attributes are cast into
            numpy.ndarray"""
            
        if self.type!='full':
            raise TypeError("Filtering can only be done on full file File instances")
            
        filtered_data = File()
        for i in range(len(self)):
            if self.quality(i,**kwargs):
                filtered_data._append_data(self,i)
            
            filtered_data.observation_mode = self.mode
        
        return filtered_data._array()
        
def full(file):
    """Opens the full file indicated by file, and loads the
    data as attributes to the class self.
    
    Attributes are made for all (attr, path) pairs in _full_file_attrs
    
    Args:
      *  file is either a str corresponding to a full file path, or an object
           with a file_name attribute (like an Overpass instance)
    
    Raises:
      *  IOError if file does not exist
      *  TypeError if file is not file name as has no attribute "file_name"
      *  KeyError if a key from the attrs is not found in the full file
      
    Example usage:
    file_name = '/wrk7/SATDATA/OCO-2/Full/v07r/2015/211/oco2_L2StdND_05730a_150730_B7000r_151006211506.h5'
    full_file = full(file_name)
    """
    self = File('full', initiate=False)
    self.file_name = file
    
    if type(file)==str:
        if not os.path.exists(file):
            raise IOError("File {0} does not exist".format(file))
            
    elif isinstance(file, PST.Overpass):
        file = file.FullFile
    
    else:
        raise TypeError("Invalid valid given to full file. Can take full file name or overpass self. Given {0}".format(type(file)))
    
    try:
        open_file = h5py.File(file, "r")
        length = xrange(open_file['/Metadata/ActualRetrievals'][0])
    except:
        raise
    else: # set the attribute as the array from the OCO-2 full file
    # this should take vare of everything, but as you see below some variable need more work
        for (item, key) in _full_file_attrs.iteritems():
            if key:
                try:
                    value = open_file[key][:]
                except:
                    raise KeyError("Key {0} not found in {1} corresponding to file {2}".format(key, open_file, file))
                else:
                    setattr(self, item, value)
        
    self.retrieved_xco2 = self.retrieved_xco2*_full_xco2_coefficient
    self.xco2_uncert = self.xco2_uncert*_full_xco2_coefficient
    self.retrieved_co2_column = self.retrieved_co2_column[:]*_co2_column_coefficient
    
    self.k = numpy.array([float(self.retrieved_co2_column[i])/float(self.retrieved_xco2[i]) for i in length])
    self.co2_column_uncert = self.xco2_uncert*self.k
    
    self.operation_mode = open_file['/Metadata/OperationMode'][0]
    self.mode = self.operation_mode
    self.observation_mode = self.mode
    
    self.footprints = numpy.array([str(self.id[i])[-1] for i in length])
    
    self.retrieval_vertex_coordinates = numpy.array([numpy.array([self.retrieval_vertex_longitude[i][0], self.retrieval_vertex_latitude[i][0]]).T for i in length])
    
    self.air_column_total = numpy.sum(self.air_column_layer_thickness[:], axis=1)
    
    at1, at2, at3, at4 = self.aerosol_types[:].T
    self.aerosol_1_type = at1
    self.aerosol_2_type = at2
    self.aerosol_3_type = at3
    self.aerosol_4_type = at4
    
    self.co2_grad_del = self.co2_grad_del[:]*_full_xco2_coefficient
    self.surface_pressure = self.surface_pressure*_full_pressure_coefficient
    self.surface_pressure_apriori = self.surface_pressure_apriori*_full_pressure_coefficient
    self.dp = self.surface_pressure -self.surface_pressure_apriori
    
    dust_aod = (at1=='DU   ')*self.aerosol_1_aod + (at2=='DU   ')*self.aerosol_2_aod
    salt_aod = (at1=='SS   ')*self.aerosol_1_aod + (at2=='SS   ')*self.aerosol_2_aod
    sulfate_aod = (at1=='SO   ')*self.aerosol_1_aod + (at2=='SO   ')*self.aerosol_2_aod
    bc_aod = (at1=='BC   ')*self.aerosol_1_aod + (at2=='BC   ')*self.aerosol_2_aod
    oc_aod = (at1=='OC   ')*self.aerosol_1_aod + (at2=='OC   ')*self.aerosol_2_aod
    ice_aod = self.aerosol_3_aod
    water_aod = self.aerosol_4_aod
    
    self.aod_dust = dust_aod
    self.aod_salt = salt_aod
    self.aod_seasalt = self.aod_salt
    self.aod_sulfate = sulfate_aod
    self.aod_bc = bc_aod
    self.aod_oc = oc_aod
    self.aod_ice = ice_aod
    self.aod_water = water_aod
    self.aod_total = self.aerosol_1_aod + self.aerosol_2_aod + self.aerosol_3_aod + self.aerosol_4_aod
    
    self.log_DWS = numpy.array([numpy.log(max((numpy.e**-5.,dust_aod[n]+water_aod[n]+salt_aod[n]))) for n in length])
    self.logDWS = self.log_DWS
    
    partial = []
    corrected = []
    corrected_no_fp = []
    for i in length:
        fp=self.footprints[i]
        mode = self.mode
        retrieved_xco2 = self.retrieved_xco2
        land_fraction = self.retrieval_land_fraction[i]
        if land_fraction >80. or land_fraction<20.:
            land_water_ind = 0 if land_fraction>80. else 1
            FEATS = [0,0]
            FEATS[0] = -0.3*(self.dp[i] - 1.4) - 0.6*(self.log_DWS[i] + 2.9) - 0.028*(self.co2_grad_del[i] - 8.4)
            FEATS[1] = -0.08*(self.dp[i] - 3.1) + 0.077*(self.co2_grad_del[i] + 7.7)
            
            xco2_partial = (retrieved_xco2[i] - _FOOT[fp][mode][land_water_ind])/(_TCCON[mode][land_water_ind])
            
            xco2_corrected_no_fp = (retrieved_xco2[i] - _FOOT[fp][mode][land_water_ind] - FEATS[land_water_ind])/(_TCCON[mode][land_water_ind])
            xco2_corrected = xco2_corrected_no_fp - _FOOT2[fp][mode][land_water_ind]
            
            partial.append(xco2_partial)
            corrected.append(xco2_corrected)
            corrected_no_fp.append(xco2_corrected_no_fp)
        else:
            partial.append(retrieved_xco2[i])
            corrected.append(retrieved_xco2[i])
    
    # applying S31 bias correction; see math doc for explanation
    s31 = 0.2125*(self.albedo_3/self.albedo_1)
    s31_xco2 = numpy.array(corrected) + 7*(s31 - 0.2)
    self.S31_xco2 = s31_xco2
    self.S31_co2_column = self.S31_xco2*self.k
    
    self.corrected_xco2 = numpy.array(corrected)
    self.corrected_no_fp_xco2 = numpy.array(corrected_no_fp)
    self.corrected_co2_column = self.corrected_xco2*self.k
    
    self.partial_xco2 = numpy.array(partial)
    self.partial_co2_column = self.partial_xco2*self.k
    
    gridded = self.grid(self.corrected_xco2, self.partial_xco2,
                        self.retrieved_xco2, self.S31_xco2,
                        self.corrected_co2_column, self.partial_co2_column,
                        self.retrieved_co2_column, self.S31_co2_column)
    
    smoothed = self.sparse_filter(*gridded)
    
    self.smoothed_corrected_xco2 = smoothed[0]
    self.smoothed_partial_xco2 = smoothed[1]
    self.smoothed_retrieved_xco2 = smoothed[2]
    self.smoothed_S31_xco2 = smoothed[3]
    self.smoothed_corrected_co2_column = smoothed[4]
    self.smoothed_partial_co2_column = smoothed[5]
    self.smoothed_retrieved_co2_column = smoothed[6]
    self.smoothed_S31_co2_column = smoothed[7]
    
    open_file.close()
    return self
    
    
def lite(file):
    """Opens the lite file indicated by file, and loads the
    data as attributes to the class self.
    
    Attributes are made for all (attr, path) pairs in _lite_file_attrs
    
    Args:
      *  file is either a str corresponding to a lite file path, or an object
           with a LiteFile attribute (like an Overpass instance)
    
    Raises:
      *  IOError if file does not exist
      *  TypeError if file is not file name as has no attribute "file_name"
      *  KeyError if a key from the attrs is not found in the lite file
      
    Example usage:
    file_name = '/wrk7/SATDATA/OCO-2/Lite/v07b/2015/oco2_LtCO2_20150730_B7000rb_COoffline.nc4'
    lite_file = lite(file_name)
    """
    self = File('lite', initiate=False)
    self.file_name = file
    
    if type(file)==str:
        if not os.path.exists(file):
            raise IOError("File {0} does not exist".format(file))
            
    elif isinstance(file, PST.Overpass):
        return lite(file.LiteFile)
    
    try:
        open_file = h5py.File(file, "r")
    except:
        raise
    else:
        for (item, key) in _lite_file_attrs.iteritems():
            if key:
                try:
                    value = open_file[key][:]
                except:
                    raise KeyError("Key {0} not found in {1} corresponding to file {2}".format(key, open_file, file))
                else:
                    setattr(self, item, value)
        
        
    # create aliases so you can use lite or full variables to access data
    self.id = self.sounding_id
    self.retrieval_latitude = self.latitude
    self.retrieval_longitude = self.longitude
    modes = {0:"ND",1:"GL",2:"TG",3:"TR"}
    self.observation_mode = numpy.array([modes[m] for m in self.observation_mode])
    
    open_file.close()       
    return self

if __name__ == "__main__":
    import Overpasses
    F = full(Overpasses.Gavin20150730)
    print F
