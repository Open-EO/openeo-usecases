'''
Created on Jul 16, 2020

@author: banyait
'''
import unittest
import xarray
from phenology_usecase.utils import reduceXY, save_UDF_Data,load_UDF_Data
import json
import numpy
import sys
import os
from openeo_udf.api.datacube import DataCube
from phenology_usecase import udf_gan,udf_smooth_savitzky_golay, udf_phenology_optimized
from unittest.case import skip
from matplotlib import pyplot


class TestGan(unittest.TestCase):

    def load_array(self,filename) -> xarray.DataArray:
        with open(filename) as f:
            d=json.load(f)
            d['data']=numpy.array(d['data'],dtype=numpy.float64)#,dtype=numpy.dtype(d['attrs']['dtype']))
            for k,v in d['coords'].items(): 
                d['coords'][k]['data']=numpy.array(v['data'],dtype=v['attrs']['dtype'])
                d['coords'][k]['atrs']={}
            d['attrs']={}
            r=xarray.DataArray.from_dict(d)
        return r

    def print_xarray_dataarray(self,title,data, limits=None, to_file=False,to_show=True):
        
        if limits is None:
            vmin=data.min()
            vmax=data.max()
        else: 
            vmin=limits[0]#91#243#91#data.min()
            vmax=limits[1]#365#160#data.max()+20
        nrow=data.shape[0]
        ncol=data.shape[1]
        data=data.transpose('t','bands','y','x')
        dpi=100
        oversample=3
        xres=len(data.x)/dpi
        yres=len(data.y)/dpi
    
        frame=0.33
    
        fig = pyplot.figure(figsize=((ncol+frame)*xres*1.1,(nrow+frame)*yres),dpi=dpi*oversample) 
        gs = pyplot.GridSpec(nrow,ncol,wspace=0.,hspace=0.,top=nrow/(nrow+frame),bottom=0.,left=frame/(ncol+frame),right=1.) 
         
        for i in range(nrow):
            for j in range(ncol):
                im = data[i,j]
                ax= pyplot.subplot(gs[i,j])
                ax.set_axis_off()
                img=ax.imshow(im[::-1,:],vmin=vmin,vmax=vmax,cmap='RdYlBu_r')#'terrain')#'jet')
                ax.set_xticklabels([])
                ax.set_yticklabels([])
                if i==0: ax.text(0.5,1.08, data.bands.values[j], size=10, va="center", ha="center", transform=ax.transAxes)
                #if j==0: ax.text(-0.08,0.5, data.t.dt.strftime("%Y-%m-%d").values[i], size=10, va="center", ha="center", rotation=90,  transform=ax.transAxes)
    
        #fig.text(0.,1.,title.split('/')[-1], size=10, va="top", ha="left",weight='bold')
    
        cbar_ax = fig.add_axes([0.01, 0.1, 0.04, 0.5])
        fig.text(0.06,0.62,'day of\nyear', size='medium', va="bottom", ha="center")
        fig.colorbar(img, cax=cbar_ax)#.ax.set_title('day of\nyear')#, label='day of\nyear')
        
        if to_file: pyplot.savefig(title+'.png')
        if to_show: pyplot.show()
    
        pyplot.close()


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


    def test01_Gan_UDF(self):
        
        S1=self.load_array('phenology_usecase/S1bands_2.json')
        S2=self.load_array('phenology_usecase/S2bands_2.json')
        PV=self.load_array('phenology_usecase/PVbands_2.json')
        
        cc=xarray.concat([S1,S2,PV],dim='bands').drop(['x','y'])
        bands=cc.bands.values.astype(str)
        cc=cc.assign_coords(bands=bands)
        cube=DataCube(cc)
        
        result=udf_gan.apply_datacube(cube, {
            #'prediction_model':"/home/banyait/eclipse-workspace/openeo-usecases/multisource_data_fusion_usecase/tests/tmp/cropsar2d_gan_conv3d_enhancedgenerator_90D_32_V1_discriminator_weights_epoch_214.h5"
            #'prediction_model':"/home/banyait/eclipse-workspace/openeo-usecases/multisource_data_fusion_usecase/tests/tmp/cropsar2d_gan_conv3d_enhancedgenerator_90D_32_V1_generator_weights_epoch_214.h5"
            'prediction_model':"tests/gan_model.h5"
        })
        
        save_UDF_Data("../gan_results", result)
            
    def test02_smoother(self):
        cube=load_UDF_Data("../gan_results")
        result=udf_smooth_savitzky_golay.apply_datacube(cube,{})
        save_UDF_Data("../smooth_results", result)
        
    def test03_phenology(self):
        cube=load_UDF_Data("../smooth_results")
        result=udf_phenology_optimized.apply_datacube(cube,{})
        save_UDF_Data("../phenology_results", result)
        
    def test04_drawing(self):
        
        gan=load_UDF_Data("../gan_results").get_array()
        smt=load_UDF_Data("../smooth_results").get_array()
        phe=load_UDF_Data("../phenology_results").get_array()
      
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
        self.print_xarray_dataarray("usecase2_sos_eos", phe,     (91,365),  True, True)
        
      
        
        