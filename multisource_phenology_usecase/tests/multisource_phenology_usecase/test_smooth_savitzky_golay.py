'''
Created on May 25, 2020

@author: banyait
'''
import unittest
import os
import udf_smooth_savitzky_golay
from utils import load_UDF_Data
import xarray


class TestSmoothing(unittest.TestCase):

    def testUDF_SavitzkyGolaySmooth(self):
        gridsize=8
#        datacube=load_UDF_Data(os.path.join(os.path.dirname(__file__),'input_'+str(gridsize)))
        datacube=load_UDF_Data(os.path.join(os.path.dirname(__file__),'nan_phenology/data_f44891612e7d415b970f90a6f28b050f'))
        refcube=load_UDF_Data(os.path.join(os.path.dirname(__file__),'smoothed_'+str(gridsize)))
        smoothedcube=udf_smooth_savitzky_golay.apply_hypercube(datacube, {})
        xarray.testing.assert_allclose(smoothedcube.get_array(), refcube.get_array())
                


