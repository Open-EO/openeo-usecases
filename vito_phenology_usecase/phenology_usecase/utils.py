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

def get_resource(relative_path):
    return str(Path( relative_path))

def load_udf(relative_path):
    with open(get_resource(relative_path), 'r+') as f:
        return f.read()

def load_UDF_Data(jsonfile):
    with open(jsonfile+'.schema') as f:
        schema=json.load(f)
    with open(jsonfile+'.json') as f: 
        datadict=json.load(f)
        dataarray=xarray.DataArray.from_dict(datadict)
        dataarray=dataarray.astype(schema['dtype'],copy=False)
        for icoord,itype in schema['coords'].items():
            dataarray[icoord]=dataarray[icoord].astype(itype['dtype'],copy=False)
        datacube=DataCube(dataarray)
    return datacube

def save_UDF_Data(jsonfile,datacube):
    dataarray=datacube.get_array()
    with open(jsonfile+'.json','w') as f: 
        json.dump(dataarray.to_dict(),f,default=str)
    with open(jsonfile+'.schema','w') as f: 
        json.dump(dataarray.to_dict(data=False),f,default=str)

def reduceXY(xskip,yskip,datacube):
    dataarray=datacube.get_array()
    return DataCube(dataarray.where(dataarray.x%xskip==0,drop=True).where(dataarray.y%yskip==0,drop=True))

def resampleXY(xskip,yskip,datacube: DataCube):
    dataarray=datacube.get_array()
    return DataCube(dataarray.coarsen({'x':xskip,'y':yskip}).mean())

def plot_timeseries(arr):
    
    pyplot.figure(figsize=(19,9.5))
    year=int((arr.t.min()+(arr.t.values.max()-arr.t.min())/2).dt.year)
    days=arr.t.dt.dayofyear+(arr.t.dt.year-year)*365
    for ix in arr.x.values:
        for iy in arr.y.values:
            if len(arr.x.values)>1 and len(arr.x.values)>1:
                ic="#%02X%02X00"%(int(ix/(len(arr.x.values)-1)*255),int(iy/(len(arr.y.values)-1)*255))
            else: ic="#000000"
            #pyplot.scatter(days,arr.values[:,0,ix,iy],c="#FFFFFF",edgecolors=ic,label="{}:{}".format(ix,iy))
            pyplot.plot(   days,arr.values[:,0,ix,iy],c=ic,label="X:Y={}:{}".format(ix,iy))

    pyplot.tight_layout()
    pyplot.ylim(-0.2,1.2)
    pyplot.xlim(0,500)
    pyplot.legend(fontsize='xx-small',markerscale=0.5,columnspacing=0.5,labelspacing=0.1,loc='upper left',bbox_to_anchor=(0.0, 1.0),ncol=arr.x.values.size, fancybox=True, shadow=True)
    pyplot.show()
    pyplot.close()

def print_xarray_dataarray(title,data,to_file=False,to_show=True):
        
    vmin=data.min()
    vmax=data.max()        
    nrow=data.shape[0]
    ncol=data.shape[1]

    frame=0.25

    fig = pyplot.figure(figsize=((ncol+frame)*2.56,(nrow+frame)*2.56),dpi=100) 
    gs = pyplot.GridSpec(nrow,ncol,wspace=0.,hspace=0.,top=nrow/(nrow+frame),bottom=0.,left=frame/(ncol+frame),right=1.) 
     
    for i in range(nrow):
        for j in range(ncol):
            im = data[i,j]
            ax= pyplot.subplot(gs[i,j])
            img=ax.imshow(im,vmin=vmin,vmax=vmax,cmap='terrain')#'jet')
            ax.set_xticklabels([])
            ax.set_yticklabels([])
            if i==0: ax.text(0.5,1.08, data.bands.values[j], size=10, va="center", ha="center", transform=ax.transAxes)
            if j==0: ax.text(-0.08,0.5, data.t.dt.strftime("%Y-%m-%d").values[i], size=10, va="center", ha="center", rotation=90,  transform=ax.transAxes)

    fig.text(0.,1.,title.split('/')[-1], size=10, va="top", ha="left",weight='bold')

    cbar_ax = fig.add_axes([0.01, 0.25, 0.04, .5])
    fig.colorbar(img, cax=cbar_ax)
    
    if to_file: pyplot.savefig(title+'.png')
    if to_show: pyplot.show()

    pyplot.close()

