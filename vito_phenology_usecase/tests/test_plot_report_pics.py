'''
Created on Jul 16, 2020

@author: banyait
'''
import unittest
from openeo_udf.api.datacube import DataCube
from phenology_usecase import udf_gan, udf_savitzkygolaysmooth_phenology
from unittest.case import skip
from matplotlib import pyplot
from phenology_usecase.utils import load_DataCube, load_DataArray, save_DataCube,\
    plot_xarray_dataarray
import os

@skip
class TestGan(unittest.TestCase):

    def plot_line(self,title,gan,smt,sea, to_file=False,to_show=True):     
        pyplot.figure(figsize=(9.5,4.5))
        pyplot.ylim(0.,1.)
        pyplot.xlim(0,365)
        pyplot.xlabel('day of year',fontsize='x-large')
        pyplot.ylabel('vegetation index',fontsize='x-large')
        pyplot.xticks(fontsize='large')
        pyplot.yticks(fontsize='large')

        if gan is not None:
            year=int((gan.t.min()+(gan.t.values.max()-gan.t.min())/2).dt.year)
            days=gan.t.dt.dayofyear+(gan.t.dt.year-year)*365
            pyplot.scatter([-1],[-1.],c="#000000",edgecolors='#000000',label="raw time series")
            for ix in gan.x.values:
                for iy in gan.y.values:
                    pyplot.scatter(days,gan.values[:,0,ix,iy],c="#000000",edgecolors='#000000')

        if smt is not None:
            year=int((smt.t.min()+(smt.t.values.max()-smt.t.min())/2).dt.year)
            days=smt.t.dt.dayofyear+(smt.t.dt.year-year)*365
            pyplot.plot([-1],[-1.],c='#000000',label="smoothed time series")
            for ix in smt.x.values:
                for iy in smt.y.values:
                    pyplot.plot(days,smt.values[:,0,ix,iy],c='#000000')

        if sea is not None:
            pyplot.plot([-1,-1],[-1.,-1.],c='#5680a8',label="start of season",marker='o')
            for ix in sea.x.values:
                for iy in sea.y.values:
                    pyplot.plot([sea.values[0,0,ix,iy],sea.values[0,0,ix,iy]],[-1.,smt[int(sea.values[0,1,ix,iy])-int(smt.t.dt.dayofyear[0]),0,ix,iy]],c='#5680a8',marker='o')

        if sea is not None:
            pyplot.plot([-1,-1],[-1.,-1.],c='#de0e0c',label="end of season",marker='o')
            for ix in sea.x.values:
                for iy in sea.y.values:
                    pyplot.plot([sea.values[0,1,ix,iy],sea.values[0,1,ix,iy]],[-1.,smt[int(sea.values[0,1,ix,iy])-int(smt.t.dt.dayofyear[0]),0,ix,iy]],c='#de0e0c',marker='o')

        pyplot.tight_layout()
        pyplot.legend(fontsize='x-large',markerscale=0.5,columnspacing=0.5,labelspacing=0.1,loc='upper left',bbox_to_anchor=(0.0, 1.0),fancybox=True, shadow=True)

        if to_file: pyplot.savefig(title+'.png')
        if to_show: pyplot.show()

        pyplot.close()

    @skip("This is not working any more because computewindowlist is removed from GAN UDF.")
    def test01_Gan_UDF(self):
        cubearr=load_DataArray('phenology_usecase/merged_cube.json')
        cube=DataCube(cubearr.drop(['x','y']))
        result=udf_gan.apply_datacube(cube, {
            'prediction_model':"tests/gan_model.h5"
        })
        save_DataCube("../gan_results.json", result)
            
    def test02_smoother(self):
        cube=load_DataCube(os.path.join(os.path.dirname(__file__),'ndvi_cube.json'))
        cube=DataCube(cube.get_array().drop(['x','y']))
        result=udf_savitzkygolaysmooth_phenology.apply_datacube(cube,{})
        save_DataCube(os.path.join(os.path.dirname(__file__),'results_smoothed.json'), result)
        
    def test03_phenology(self):
        cube=load_DataCube(os.path.join(os.path.dirname(__file__),'results_smoothed.json'))
        result=udf_savitzkygolaysmooth_phenology.apply_datacube(cube,{})
        save_DataCube(os.path.join(os.path.dirname(__file__),'results_phenology.json'), result)
    
    @skip("this is the actual drawing, comment for generating the pictures")
    def test04_drawing(self):
        
        gan=load_DataArray(os.path.join(os.path.dirname(__file__),'ndvi_cube.json')).drop(['x','y'])
        smt=load_DataArray(os.path.join(os.path.dirname(__file__),'results_smoothed.json'))
        phe=load_DataArray(os.path.join(os.path.dirname(__file__),'results_phenology.json'))
      
        st=20
        x2=135-int(st/2)
        y2=57-int(st/2)
        pt=4
      
        gan2=gan[:,:,x2:x2+st:pt,y2:y2+st:pt]
        smt2=smt[:,:,x2:x2+st:pt,y2:y2+st:pt]
        phe2=phe[:,:,x2:x2+st:pt,y2:y2+st:pt]
        
        #self.plot_line(gan1,smt1,phe1)
        self.plot_line("usecase2_gan",  gan2,smt2,None,True,True)
        self.plot_line("usecase2_pheno",None,smt2,phe2,True,True)
        
        #phe[:,:,x2:x2+st:pt,y2:y2+st:pt]=0
        phe=phe.assign_coords(bands=['start of season','end of season'])
        plot_xarray_dataarray(
            phe, 
            limits=(91,365), 
            show_bandnames=True, 
            show_dates=False, 
            oversample=3, 
            cbartext="day of\nyear", 
            to_file="usecase2_sos_eos", 
            to_show=True
        )        
      
        
        