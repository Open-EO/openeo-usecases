'''
Created on Jul 21, 2020

@author: banyait
'''
import xarray
import tensorflow as tf
import unittest
from phenology_usecase.udf_gan import apply_datacube
from openeo_udf.api.datacube import DataCube
import pandas
import numpy

class TestGan(unittest.TestCase):

    def build_array(self):
        # the dates, only two layer won't be missing to test ffill
        acquisition_dates = list(pandas.date_range(
            start=numpy.datetime64('2020-06-25'),
            periods=10,
            freq='2D'
        ))        
        # init full missing
        arr=xarray.DataArray(
            numpy.full([len(acquisition_dates),4,128,128], numpy.nan),
            dims=['t','bands','x','y'],
            coords={
                't':acquisition_dates,
                'bands':['S2ndvi','VH','VV','ndvi']
            }
        )
        # init at two dates
        ictr=1.
        for idate in [numpy.datetime64('2020-06-29'),numpy.datetime64('2020-07-09')]:
            arr.loc[{'t':[idate]}]=ictr
            arr.loc[{'t':[idate], 'bands':['S2ndvi'], 'x':range(0,64),   'y':range(0,64)}]  +=0.1
            arr.loc[{'t':[idate], 'bands':['VH'],     'x':range(64,128), 'y':range(0,64)}]  +=0.2
            arr.loc[{'t':[idate], 'bands':['VV'],     'x':range(0,64),   'y':range(64,128)}]+=0.3
            arr.loc[{'t':[idate], 'bands':['ndvi'],   'x':range(64,128), 'y':range(64,128)}]+=0.4
            ictr+=1.    
        return arr


    def test_gan(self):

        # load and inverse scale according to UDF
        arr=self.build_array()
        arr.loc[{'bands':'ndvi'}]=250.*(arr.loc[{'bands':'ndvi'}]+0.08)
        arr.loc[{'bands':'VH'}]  =10.**(arr.loc[{'bands':'VH'}]/10.)
        arr.loc[{'bands':'VV'}]  =10.**(arr.loc[{'bands':'VV'}]/10.)        

        # Create a simple model that averages over time and then over bands 
        inS1=tf.keras.Input(shape=[19,128,128,2])
        avS1=tf.keras.layers.Lambda(lambda x: tf.reduce_mean(x, axis=1, keepdims=False))(inS1)
        inS2=tf.keras.Input(shape=[19,128,128,1])
        avS2=tf.keras.layers.Lambda(lambda x: tf.reduce_mean(x, axis=1, keepdims=False))(inS2)
        inPV=tf.keras.Input(shape=[19,128,128,1])
        avPV=tf.keras.layers.Lambda(lambda x: tf.reduce_mean(x, axis=1, keepdims=False))(inPV)
        ct=tf.keras.layers.Concatenate(axis=3)([avS1,avS2,avPV])
        av=tf.keras.layers.Lambda(lambda x: tf.reduce_mean(x, axis=3, keepdims=True))(ct)
        model=tf.keras.Model([inS1,inS2,inPV],av)
        model.save('/tmp/test_gan_model.h5')

        # run gan
        result=apply_datacube(DataCube(arr), dict(
            prediction_model='/tmp/test_gan_model.h5',
            gan_window_half='9D',
            gan_steps='2D',
            gan_samples=19,
            acquisition_steps='10D',
            scaler='passthrough'
        ))

        # compute check: with this setup
        # 6 front NaNs
        # 5 data of 2020-06-29
        # 3 data of 2020-07-01
        # 5 trailing Nans
        # NaNs get filled with zeros
        check=arr.dropna('t')
        check=5./19.*check[0]+3./19.*check[1]
        check=check.mean('bands').expand_dims({'bands':['predictions']})
        check=check.expand_dims({'t':[numpy.datetime64('2020-07-04')]})
        
        xarray.testing.assert_allclose(check.astype(numpy.float32), result.get_array())