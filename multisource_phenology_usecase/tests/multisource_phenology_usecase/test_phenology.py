'''
Created on May 25, 2020

@author: banyait
'''
import unittest
import os
from utils import load_UDF_Data
import udf_phenology_old
import udf_phenology_optimized
import xarray
import numpy
from openeo_udf.api.datacube import DataCube

class TestPhenology(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestPhenology, cls).setUpClass()
        cls.gridsize=8
        cls.inpcube=load_UDF_Data(os.path.join(os.path.dirname(__file__),'smoothed_'+str(cls.gridsize)))
        cls.refcube=load_UDF_Data(os.path.join(os.path.dirname(__file__),'phenology_'+str(cls.gridsize)))


    def test_singleBand(self):
        refcube=self.refcube
        outcube=udf_phenology_optimized.apply_hypercube(self.inpcube, {})
        xarray.testing.assert_allclose(outcube.get_array(), refcube.get_array())
        
#     def test_hasNoDataTimeSeries(self):
#         inpcube=DataCube(self.inpcube.get_array().where(self.inpcube.get_array().x!=3, numpy.nan, drop=False))
#         refcube=DataCube(self.refcube.get_array().where(self.refcube.get_array().x!=3, numpy.nan, drop=False))        
#         outcube=udf_phenology_optimized.apply_hypercube(inpcube, {})
#         xarray.testing.assert_allclose(outcube.get_array(), refcube.get_array())
#     
#     def test_oldnewPhenologyIsSame(self):
#         optcube=udf_phenology_optimized.apply_hypercube(self.inpcube, {})
#         oldcube=udf_phenology_old.apply_hypercube(self.inpcube, {})
#         optarr=optcube.get_array().squeeze('t',drop=True)
#         oldarr=oldcube.get_array().dt.dayofyear.astype(numpy.float64)
#         xarray.testing.assert_allclose(optarr,oldarr)
