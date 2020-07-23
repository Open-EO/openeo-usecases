'''
Created on May 25, 2020

@author: banyait
'''
import unittest
import os
import xarray
import numpy
from openeo_udf.api.datacube import DataCube
from phenology_usecase.utils import load_DataCube
from phenology_usecase import udf_phenology_optimized, udf_phenology_old

class TestPhenology(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestPhenology, cls).setUpClass()
        cls.inpcube=load_DataCube(os.path.join(os.path.dirname(__file__),'test03_smoothed.json'))
        cls.refcube=load_DataCube(os.path.join(os.path.dirname(__file__),'test04_phenology.json'))

    def test_singleBand(self):
        refcube=self.refcube
        outcube=udf_phenology_optimized.apply_datacube(self.inpcube, {})
        xarray.testing.assert_allclose(outcube.get_array(), refcube.get_array())

    def test_multiBand(self):
        inparr1=self.inpcube.get_array()
        inparr2=self.inpcube.get_array().assign_coords(bands=['extraband'])
        inpcube=DataCube(xarray.concat([inparr1,inparr2],dim='bands'))
        outcube=udf_phenology_optimized.apply_datacube(inpcube, {})
        xarray.testing.assert_allclose(outcube.get_array(), self.refcube.get_array())
        
    def test_hasNoDataTimeSeries(self):
        inpcube=DataCube(self.inpcube.get_array().where(self.inpcube.get_array().x!=3, numpy.nan, drop=False))
        refcube=DataCube(self.refcube.get_array().where(self.refcube.get_array().x!=3, 0., drop=False))        
        outcube=udf_phenology_optimized.apply_datacube(inpcube, {})
        xarray.testing.assert_allclose(outcube.get_array(), refcube.get_array())
     
    def test_oldnewPhenologyIsSame(self):
        optcube=udf_phenology_optimized.apply_datacube(DataCube(self.inpcube.get_array().drop(['x','y'])), {})
        oldcube=udf_phenology_old.apply_datacube(DataCube(self.inpcube.get_array().drop(['x','y'])), {})
        optarr=optcube.get_array().squeeze('t',drop=True)
        oldarr=oldcube.get_array().dt.dayofyear.astype(numpy.float64)
        xarray.testing.assert_allclose(optarr,oldarr)

    def test_coordinateOrderChanged(self):
        inpcube=DataCube(self.inpcube.get_array().transpose())
        refcube=DataCube(self.refcube.get_array().transpose())
        outcube=udf_phenology_optimized.apply_datacube(inpcube, {})
        xarray.testing.assert_allclose(outcube.get_array(), refcube.get_array())
 
    def test_missingCoordinates(self):
        inpcube=DataCube(self.inpcube.get_array()[:,:,0,:])
        refcube=DataCube(self.refcube.get_array()[:,:,0,:])
        outcube=udf_phenology_optimized.apply_datacube(inpcube, {})
        xarray.testing.assert_allclose(outcube.get_array(), refcube.get_array())


