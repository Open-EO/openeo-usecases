'''
Created on Jun 3, 2020

@author: banyait
'''
import unittest
from utils import load_UDF_Data
import os
import udf_evi


class TestEVI(unittest.TestCase):

    def test_evi(self):
        cube=load_UDF_Data(os.path.join(os.path.dirname(__file__),'data_2cf66a4eef024a698c8563e603b66a4e'))
        evi=udf_evi.apply_hypercube(cube, {})

