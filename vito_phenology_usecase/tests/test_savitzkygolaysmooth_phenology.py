'''
Created on Aug 22, 2020

@author: banyait
'''
import unittest
import os
import xarray
from phenology_usecase.utils import load_DataCube
from phenology_usecase import udf_savitzkygolaysmooth_phenology

class TestMergedSmoothAndPhenology(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestMergedSmoothAndPhenology, cls).setUpClass()
        cls.inpcube=load_DataCube(os.path.join(os.path.dirname(__file__),'test02_ganndvi.json'))
        cls.refcube=load_DataCube(os.path.join(os.path.dirname(__file__),'test04_phenology.json'))

    def test_defaults(self):
        refcube=self.refcube
        outcube=udf_savitzkygolaysmooth_phenology.apply_datacube(self.inpcube, {})
        xarray.testing.assert_allclose(outcube.get_array(), refcube.get_array())

    def test_passthrough(self):
        refcube=self.inpcube
        outcube=udf_savitzkygolaysmooth_phenology.apply_datacube(self.inpcube, dict(do_smoothing=False,do_phenology=False))
        xarray.testing.assert_allclose(outcube.get_array(), refcube.get_array())


