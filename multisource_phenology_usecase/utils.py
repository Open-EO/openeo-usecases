'''
Created on May 26, 2020

@author: banyait

Collection of useful client-side routines without any organization of functionality.

'''

import json
import xarray
from pathlib import Path
from openeo_udf.api.datacube import DataCube

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
