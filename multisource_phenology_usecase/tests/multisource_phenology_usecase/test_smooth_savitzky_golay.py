'''
Created on May 25, 2020

@author: banyait
'''
import unittest
import os
import udf_smooth_savitzky_golay
from utils import load_UDF_Data
import xarray
from openeo_udf.api.datacube import DataCube
import numpy


class TestSavitzkyGolaySmooth(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestSavitzkyGolaySmooth, cls).setUpClass()
        cls.gridsize=8
        cls.inpcube=load_UDF_Data(os.path.join(os.path.dirname(__file__),'input_'+str(cls.gridsize)))
        cls.refcube=load_UDF_Data(os.path.join(os.path.dirname(__file__),'smoothed_'+str(cls.gridsize)))

    def test_singleBand(self):
        refcube=self.refcube
        outcube=udf_smooth_savitzky_golay.apply_hypercube(self.inpcube, {})
        xarray.testing.assert_allclose(outcube.get_array(), refcube.get_array())
                
    def test_multiBand(self):
        inparr1=self.inpcube.get_array()
        inparr2=self.inpcube.get_array().assign_coords(bands=['extraband'])
        refarr1=self.refcube.get_array()
        refarr2=self.refcube.get_array().assign_coords(bands=['extraband'])
        inpcube=DataCube(xarray.concat([inparr1,inparr2],dim='bands'))
        refcube=DataCube(xarray.concat([refarr1,refarr2],dim='bands'))
        outcube=udf_smooth_savitzky_golay.apply_hypercube(inpcube, {})
        xarray.testing.assert_allclose(outcube.get_array(), refcube.get_array())

    def test_hasNoDataTimeSeries(self):
        inpcube=DataCube(self.inpcube.get_array().where(self.inpcube.get_array().x!=3, numpy.nan, drop=False))
        refcube=DataCube(self.refcube.get_array().where(self.refcube.get_array().x!=3, numpy.nan, drop=False))
        outcube=udf_smooth_savitzky_golay.apply_hypercube(inpcube, {})
        xarray.testing.assert_allclose(outcube.get_array(), refcube.get_array())

    def test_coordinateOrderChanged(self):
        inpcube=DataCube(self.inpcube.get_array().transpose())
        refcube=DataCube(self.refcube.get_array().transpose())
        outcube=udf_smooth_savitzky_golay.apply_hypercube(inpcube, {})
        xarray.testing.assert_allclose(outcube.get_array(), refcube.get_array())

    def test_missingCoordinates(self):
        inpcube=DataCube(self.inpcube.get_array()[:,0,:,0])
        refcube=DataCube(self.refcube.get_array()[:,0,:,0])
        outcube=udf_smooth_savitzky_golay.apply_hypercube(inpcube, {})
        xarray.testing.assert_allclose(outcube.get_array(), refcube.get_array())
