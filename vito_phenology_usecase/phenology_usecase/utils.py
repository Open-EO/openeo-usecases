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
   
    days=arr.t.dt.dayofyear+(arr.t.dt.year-arr.t.dt.year[0])*365
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


