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


class TestPhenology(unittest.TestCase):

    def test_phenology(self):
        gridsize=8
        smoothedcube=load_UDF_Data(os.path.join(os.path.dirname(__file__),'smoothed_'+str(gridsize)))
        ref=load_UDF_Data(os.path.join(os.path.dirname(__file__),'phenology_'+str(gridsize))).get_array()
        phenology=udf_phenology_optimized.apply_hypercube(smoothedcube, {}).get_array()
        diff=phenology-ref
        print(diff.min().values,diff.max().values)
        print(phenology.shape,ref.shape)
        xarray.testing.assert_allclose(phenology, ref)
        
    
    def test_oldnewPhenologyIsSame(self):
        gridsize=8
        smoothedcube=load_UDF_Data(os.path.join(os.path.dirname(__file__),'smoothed_'+str(gridsize)))
        phenology_old=udf_phenology_old.apply_hypercube(smoothedcube, {}).get_array().assign_coords(t=numpy.datetime64("2019-01-01")).expand_dims('t').dt.dayofyear
        phenology_opt=udf_phenology_optimized.apply_hypercube(smoothedcube, {}).get_array()
        diff=phenology_old-phenology_opt
        print(diff.min().values,diff.max().values)
        print(phenology_old.shape,phenology_opt.shape)
        print(phenology_old.dims,phenology_opt.dims)
        print(phenology_old.t,phenology_opt.t)
        xarray.testing.assert_allclose(phenology_old, phenology_opt)
        
    
