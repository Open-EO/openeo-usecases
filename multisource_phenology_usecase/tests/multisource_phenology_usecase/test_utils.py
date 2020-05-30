'''
Created on May 25, 2020

@author: banyait
'''
import unittest
import os
from matplotlib import pyplot
import udf_smooth_savitzky_golay
from utils import load_UDF_Data, reduceXY, save_UDF_Data
import udf_phenology_optimized
import xarray


class TestUtils(unittest.TestCase):

    def test_LoadSave(self):
        gridsize=8
        cube1=load_UDF_Data(os.path.join(os.path.dirname(__file__),'input_'+str(gridsize)))
        save_UDF_Data('/tmp/test', cube1)
        cube2=load_UDF_Data('/tmp/test')
        xarray.testing.assert_allclose(cube1.get_array(), cube2.get_array())
        
    def test_Reduce(self):
        cube8=load_UDF_Data(os.path.join(os.path.dirname(__file__),'input_8'))
        ref4=load_UDF_Data(os.path.join(os.path.dirname(__file__),'input_4'))
        cube4=reduceXY(2, 2, cube8)
        xarray.testing.assert_allclose(cube4.get_array(), ref4.get_array())

    @unittest.skip
    def test_produce_downsample(self):
        datacube=load_UDF_Data(os.path.join(os.path.dirname(__file__),'data_ee02d1fa29dd4a76a14477cf8106d28e'))
        for i in 1,2,4,8,16,32,64,128,256:
            print("downsampling "+str(i))
            icube=reduceXY(256/i, 256/i, datacube)
            save_UDF_Data(os.path.join(os.path.dirname(__file__),'input_'+str(i)), icube)

    @unittest.skip
    def test_produce_smoothed(self):
        gridsize=8
        datacube=load_UDF_Data(os.path.join(os.path.dirname(__file__),'input_'+str(gridsize)))
        smoothedcube=udf_smooth_savitzky_golay.apply_hypercube(datacube, {})
        save_UDF_Data(os.path.join(os.path.dirname(__file__),'smoothed_'+str(gridsize)), smoothedcube)

    @unittest.skip
    def test_produce_phenology(self):
        gridsize=8
        smoothedcube=load_UDF_Data(os.path.join(os.path.dirname(__file__),'smoothed_'+str(gridsize)))
        phenologycube=udf_phenology_optimized.apply_hypercube(smoothedcube, {})
        save_UDF_Data(os.path.join(os.path.dirname(__file__),'phenology_'+str(gridsize)), phenologycube)
        
    @unittest.skip
    def test_produce_plots(self):
        gridsize=32
        plot_timeseries=True
        plot_seasons=True
        datacube=load_UDF_Data(os.path.join(os.path.dirname(__file__),'input_'+str(gridsize)))
        
        
        if plot_timeseries:
            pyplot.figure(figsize=(19,9.5))
       
        if plot_timeseries:
            arr=datacube.get_array()
            days=arr.t.dt.dayofyear+(arr.t.dt.year-arr.t.dt.year[0])*365
            for ix in arr.x.values:
                for iy in arr.y.values:
                    if len(arr.x.values)>1 and len(arr.x.values)>1:
                        ic="#%02X%02X00"%(int(ix/(len(arr.x.values)-1)*255),int(iy/(len(arr.y.values)-1)*255))
                    else: ic="#000000"
                    pyplot.scatter(days,arr.values[:,0,ix,iy],c="#FFFFFF",edgecolors=ic,label="{}:{}".format(ix,iy))
                    #pyplot.plot(arr.t,arr.values[:,0,ix,iy],c=ic,label="X:Y={}:{}".format(ix,iy))

        datacube=udf_smooth_savitzky_golay.apply_hypercube(datacube, {})
        #udf_vito_save_to_public
        
        if plot_timeseries:
            arr=datacube.get_array()
            days=arr.t.dt.dayofyear+(arr.t.dt.year-arr.t.dt.year[0])*365
            for ix in arr.x.values:
                for iy in arr.y.values:
                    if len(arr.x.values)>1 and len(arr.x.values)>1:
                        ic="#%02X%02X00"%(int(ix/(len(arr.x.values)-1)*255),int(iy/(len(arr.y.values)-1)*255))
                    else: ic="#000000"
                    #pyplot.scatter(arr.t,arr.values[:,0,ix,iy],c=ic,marker="x")
                    pyplot.plot(days,arr.values[:,0,ix,iy],c=ic)

        datacube=udf_phenology_optimized.apply_hypercube(datacube, {})
        
        if plot_timeseries:
            arr=datacube.get_array()
            for ix in arr.x.values:
                for iy in arr.y.values:
                    if len(arr.x.values)>1 and len(arr.x.values)>1:
                        ic="#%02X%02X00"%(int(ix/(len(arr.x.values)-1)*255),int(iy/(len(arr.y.values)-1)*255))
                    else: ic="#000000"
                    pyplot.plot([arr.values[0,0,ix,iy]]*2,[0,200],c=ic)
                    pyplot.plot([arr.values[0,1,ix,iy]]*2,[0,200],c=ic)
        
        if plot_timeseries:        
            pyplot.tight_layout()
            pyplot.ylim(0,200)
            pyplot.xlim(0,500)
            pyplot.legend(fontsize='xx-small',markerscale=0.5,columnspacing=0.5,labelspacing=0.1,loc='upper left',bbox_to_anchor=(0.0, 1.0),ncol=gridsize, fancybox=True, shadow=True)
            pyplot.show()
            pyplot.close()

        if plot_seasons:
            fig, axes = pyplot.subplots(ncols=2)
            fig.set_size_inches(19,9.5)
            fig.tight_layout()
            datacube.get_array()[0,0,:,:].plot(ax=axes[0])
            datacube.get_array()[0,1,:,:].plot(ax=axes[1])
            pyplot.show()
            pyplot.close()
        
        print('FINISHED')


