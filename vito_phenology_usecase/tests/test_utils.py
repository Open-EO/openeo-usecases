'''
Created on May 25, 2020

@author: banyait
'''
import unittest
import xarray
import numpy
from openeo_udf.api.datacube import DataCube
from phenology_usecase.utils import save_DataCube, load_DataCube, reduceXY, plot_xarray_dataarray,\
    plot_timeseries


class TestUtils(unittest.TestCase):

    def build_array(self,width,height,mult=(1,1)):
        return xarray.DataArray(
            numpy.array([i[0]*100000+i[1]*10000+i[2]*mult[0]*100+i[3]*mult[1] for i in numpy.ndindex((3,2,width,height))]).reshape(3,2,width,height),
            dims=['t','bands','x','y'],
            coords={
                't': [numpy.datetime64('2020-07-01'),numpy.datetime64('2020-07-11'),numpy.datetime64('2020-07-21')],
                'bands': ['band0','band1']
            }
        )

    def test_LoadSave(self):
        cube1=DataCube(self.build_array(32, 16))
        save_DataCube('/tmp/test_LoadSave.json', cube1)
        cube2=load_DataCube('/tmp/test_LoadSave.json')
        xarray.testing.assert_allclose(cube1.get_array(), cube2.get_array())
        
    def test_Reduce(self):
        cube1=reduceXY(8, 2, DataCube(self.build_array(32, 16)))
        cube2=DataCube(self.build_array(4, 8, mult=(8,2)))
        xarray.testing.assert_allclose(cube1.get_array(), cube2.get_array())
        
    @unittest.skip
    def test_generate_merged_output(self):
        merge=load_DataCube('tests/merged_cube.json').get_array()
        hasPV=merge[:,3].dropna('t',how='all').t
        merge=merge.loc[{'t':hasPV.values}][19:21]
        merge=(merge*100.).astype(numpy.int64).astype(numpy.float64)/100.
        merge=merge.where(merge>-1.e10).where(merge<1.e10)
        save_DataCube('tests/test01_merged.json', DataCube(merge))
        plot_xarray_dataarray(merge)

    @unittest.skip
    def test_generate_ganndvi_output(self):
        merge=load_DataCube('tests/ndvi_cube.json')
        merge=reduceXY(16, 16, merge).get_array()
        save_DataCube('tests/test02_ganndvi.json', DataCube(merge))
        plot_timeseries(merge.drop('x').drop('y'))

    @unittest.skip
    def test_generate_smoothed_output(self):
        merge=load_DataCube('tests/smoothed_cube.json')
        merge=reduceXY(16, 16, merge).get_array()
        save_DataCube('tests/test03_smoothed.json', DataCube(merge))
        plot_timeseries(merge.drop('x').drop('y'))

    @unittest.skip
    def test_generate_phenology_output(self):
        merge=load_DataCube('tests/vito_phenology.json')
        merge=reduceXY(16, 16, merge).get_array()
        save_DataCube('tests/test04_phenology.json', DataCube(merge))
        plot_timeseries(merge.drop('x').drop('y'))
