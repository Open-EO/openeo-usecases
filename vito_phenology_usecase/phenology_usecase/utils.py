'''
Created on May 26, 2020

@author: banyait

Collection of useful client-side routines without any organization of functionality.

'''

import json
import xarray
from pathlib import Path
from openeo_udf.api.datacube import DataCube
from matplotlib import pyplot
import re
import numpy
from builtins import int


class UDFString():
    def __init__(self, filename):
        with open(str(Path(filename)), 'r+') as f:
            self.value=f.read()
    def replace_option(self,option,new_value):
        self.value=re.sub('(\n\s*'+option+'\s*=).*\n','\\1 '+new_value+'\n',self.value,count=1)
        return self


def load_DataArray(filename) -> xarray.DataArray:
    with open(filename) as f:
        d=json.load(f)
        d['data']=numpy.array(d['data'],dtype=numpy.dtype(d['attrs']['dtype']))
        for k,v in d['coords'].items(): 
            d['coords'][k]['data']=numpy.array(v['data'],dtype=v['attrs']['dtype'])
            d['coords'][k]['atrs']={}
        d['attrs']={}
        r=xarray.DataArray.from_dict(d)
    return r


def save_DataArray(filename,array):
    jsonarray=array.to_dict()
    # add attributes that needed for re-creating xarray from json
    jsonarray['attrs']['dtype']=str(array.values.dtype)
    jsonarray['attrs']['shape']=list(array.values.shape)
    for i in array.coords.values():
        jsonarray['coords'][i.name]['attrs']['dtype']=str(i.dtype)
        jsonarray['coords'][i.name]['attrs']['shape']=list(i.shape)
    # custom print so arraying json is easy to read humanly
    with open(filename,'w') as f:
        def custom_print(data_structure, indent=1):
            f.write("{\n")
            needs_comma=False
            for key, value in data_structure.items():
                if needs_comma: 
                    f.write(',\n')
                needs_comma=True
                f.write('  '*indent+json.dumps(key)+':')
                if isinstance(value, dict): 
                    custom_print(value, indent+1)
                else: 
                    json.dump(value,f,default=str,separators=(',',':'))
            f.write('\n'+'  '*(indent-1)+"}")
            
        custom_print(jsonarray)


def load_DataCube(jsonfile):
    return DataCube(load_DataArray(jsonfile))


def save_DataCube(jsonfile,datacube):
    save_DataArray(jsonfile,datacube.get_array())


def reduceXY(xskip,yskip,datacube):
    dataarray=datacube.get_array()
    dataarray=dataarray.loc[{'x':dataarray.x[::xskip],'y':dataarray.y[::yskip]}]
    return DataCube(dataarray)


def resampleXY(xskip,yskip,datacube: DataCube):
    dataarray=datacube.get_array()
    return DataCube(dataarray.coarsen({'x':xskip,'y':yskip}).mean())


def plot_xarray_dataarray(
        data,
        title=None, 
        limits=None,
        show_bandnames=True,
        show_dates=True,
        oversample:int=1,
        cmap='RdYlBu_r', 
        cbartext:str=None,
        to_file:str=None,
        to_show=True
    ):
    
    if limits is None:
        vmin=data.min()
        vmax=data.max()
    else: 
        vmin=limits[0]
        vmax=limits[1]
    nrow=data.shape[0]
    ncol=data.shape[1]
    data=data.transpose('t','bands','y','x')
    dpi=100
    oversample=oversample
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
            img=ax.imshow(im[::-1,:],vmin=vmin,vmax=vmax,cmap=cmap)#'RdYlBu_r')#'terrain')#'jet')
            ax.set_xticklabels([])
            ax.set_yticklabels([])
            if show_bandnames:
                if i==0: ax.text(0.5,1.08, data.bands.values[j], size=10, va="center", ha="center", transform=ax.transAxes)
            if show_dates:
                if j==0: ax.text(-0.08,0.5, data.t.dt.strftime("%Y-%m-%d").values[i], size=10, va="center", ha="center", rotation=90,  transform=ax.transAxes)

    if title is not None:
        fig.text(0.,1.,title.split('/')[-1], size=10, va="top", ha="left",weight='bold')

    cbar_ax = fig.add_axes([0.01, 0.1, 0.04, 0.5])
    if cbartext is not None:
        fig.text(0.06,0.62,cbartext, size='medium', va="bottom", ha="center")
    fig.colorbar(img, cax=cbar_ax)
    
    if to_file is not None: pyplot.savefig(to_file)
    if to_show: pyplot.show()

    pyplot.close()


def plot_timeseries(arr):
    pyplot.figure(figsize=(19,9.5))
    year=int((arr.t.min()+(arr.t.values.max()-arr.t.min())/2).dt.year)
    days=arr.t.dt.dayofyear+(arr.t.dt.year-year)*365
    for ix in arr.x.values:
        for iy in arr.y.values:
            if len(arr.x.values)>1 and len(arr.x.values)>1:
                ic="#%02X%02X00"%(int(ix/(len(arr.x.values)-1)*255),int(iy/(len(arr.y.values)-1)*255))
            else: ic="#000000"
            pyplot.scatter(days,arr.values[:,0,ix,iy],c="#FFFFFF",edgecolors=ic,label="{}:{}".format(ix,iy))
            #pyplot.plot(   days,arr.values[:,0,ix,iy],c=ic,label="X:Y={}:{}".format(ix,iy))

    pyplot.tight_layout()
    #pyplot.ylim(arr.values.min(),arr.values.max())
    pyplot.xlim(0,500)
    pyplot.legend(fontsize='xx-small',markerscale=0.5,columnspacing=0.5,labelspacing=0.1,loc='upper left',bbox_to_anchor=(0.0, 1.0),ncol=arr.x.values.size, fancybox=True, shadow=True)
    pyplot.show()
    pyplot.close()
