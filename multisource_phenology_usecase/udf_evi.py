# -*- coding: utf-8 -*-
# Uncomment the import only for coding support
from openeo_udf.api.datacube import DataCube
from typing import Dict


def apply_hypercube(cube: DataCube, context: Dict) -> DataCube:

    import numpy

    # get the xarray    
    array=cube.get_array()
    
    # compute reflectance
    B02=array.bands.values.tolist().index('TOC-B02_10M')
    B04=array.bands.values.tolist().index('TOC-B04_10M')
    B08=array.bands.values.tolist().index('TOC-B08_10M')
    result = (2.5 * (B08 - B04)) / ((B08 + 6.0 * B04 - 7.5 * B02) + 10000.0*1.0)

    # give proper name for results
    season=result.assign_coords(bands=['evi']).astype(numpy.float64)
    
    return DataCube(season)


