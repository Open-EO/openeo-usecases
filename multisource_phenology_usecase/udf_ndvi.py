# -*- coding: utf-8 -*-
# Uncomment the import only for coding support
from openeo_udf.api.datacube import DataCube
from typing import Dict


def apply_hypercube(cube: DataCube, context: Dict) -> DataCube:
 
    # get the xarray    
    array=cube.get_array()
 
    # compute reflectance
    B04=array[:,array.bands.values.tolist().index('TOC-B04_10M')]
    B08=array[:,array.bands.values.tolist().index('TOC-B08_10M')]
    result = (B08 - B04) / (B08 + B04)
 
    # return result
    return DataCube(result)


