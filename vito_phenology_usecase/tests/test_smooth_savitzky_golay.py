'''
Created on May 25, 2020

@author: banyait
'''
import unittest
import os
import xarray
from openeo_udf.api.datacube import DataCube
import numpy
from phenology_usecase.utils import load_DataCube
from phenology_usecase import udf_savitzkygolaysmooth_phenology


class TestSavitzkyGolaySmooth(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestSavitzkyGolaySmooth, cls).setUpClass()
        cls.inpcube=load_DataCube(os.path.join(os.path.dirname(__file__),'test02_ganndvi.json'))
        cls.refcube=load_DataCube(os.path.join(os.path.dirname(__file__),'test03_smoothed.json'))

    def test_singleBand(self):
        refcube=self.refcube
        outcube=udf_savitzkygolaysmooth_phenology.apply_datacube(self.inpcube, dict(do_smoothing=True,do_phenology=False))
        xarray.testing.assert_allclose(outcube.get_array(), refcube.get_array())
                
    def test_multiBand(self):
        inparr1=self.inpcube.get_array()
        inparr2=self.inpcube.get_array().assign_coords(bands=['extraband'])
        refarr1=self.refcube.get_array()
        refarr2=self.refcube.get_array().assign_coords(bands=['extraband'])
        inpcube=DataCube(xarray.concat([inparr1,inparr2],dim='bands'))
        refcube=DataCube(xarray.concat([refarr1,refarr2],dim='bands'))
        outcube=udf_savitzkygolaysmooth_phenology.apply_datacube(inpcube, dict(do_smoothing=True,do_phenology=False))
        xarray.testing.assert_allclose(outcube.get_array(), refcube.get_array())

    def test_hasNoDataTimeSeries(self):
        inpcube=DataCube(self.inpcube.get_array().where(self.inpcube.get_array().x!=3, numpy.nan, drop=False))
        refcube=DataCube(self.refcube.get_array().where(self.refcube.get_array().x!=3, numpy.nan, drop=False))
        outcube=udf_savitzkygolaysmooth_phenology.apply_datacube(inpcube, dict(do_smoothing=True,do_phenology=False))
        xarray.testing.assert_allclose(outcube.get_array(), refcube.get_array())

    def test_coordinateOrderChanged(self):
        inpcube=DataCube(self.inpcube.get_array().transpose())
        refcube=DataCube(self.refcube.get_array().transpose())
        outcube=udf_savitzkygolaysmooth_phenology.apply_datacube(inpcube, dict(do_smoothing=True,do_phenology=False))
        xarray.testing.assert_allclose(outcube.get_array(), refcube.get_array())

    def test_missingCoordinates(self):
        inpcube=DataCube(self.inpcube.get_array()[:,0,:,0])
        refcube=DataCube(self.refcube.get_array()[:,0,:,0])
        outcube=udf_savitzkygolaysmooth_phenology.apply_datacube(inpcube, dict(do_smoothing=True,do_phenology=False))
        xarray.testing.assert_allclose(outcube.get_array(), refcube.get_array())
