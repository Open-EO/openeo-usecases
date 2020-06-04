# -*- coding: utf-8 -*-
# Uncomment the import only for coding support
from openeo_udf.api.datacube import DataCube
from typing import Dict


def apply_hypercube(cube: DataCube, context: Dict) -> DataCube:

    import numpy
    import xarray

    # get the xarray    
    array=cube.get_array()
    result=xarray.zeros_like(array, numpy.float64)

#     # create a copy
#     result=array.copy()    
#     shape=list(array.shape)
#     shape[array.dims.index('bands')]=1
#     result=xarray.DataArray(
#         numpy.full(shape, 0., numpy.float64),
#         dims=array.dims,
#         coords={
#             't': array.coords['t'].values,
#             'bands': ['evi']
#         }
#     )

    # compute reflectance
    B02=array[:,array.bands.values.tolist().index('TOC-B02_10M')]
    B04=array[:,array.bands.values.tolist().index('TOC-B04_10M')]
    B08=array[:,array.bands.values.tolist().index('TOC-B08_10M')]
    result = (2.5 * (B08 - B04)) / ((B08 + 6.0 * B04 - 7.5 * B02) + 10000.0*1.0)
    
    #result[:,1:]= result[:,0]

    # give proper name for results
    #season=result.expand_dims('bands',3).assign_coords(bands=['evi']).astype(numpy.float64)
    #result=result.expand_dims('bands',1).assign_coords(bands=['evi']).astype(numpy.float64)
    
#    result=result.assign_coords('bands'=array.bands)
    
 #   result=xarray.DataArray(result,coords={'t': array.coords['t'].values})
    
    return DataCube(result)


# def apply_hypercube(cube: DataCube, context: Dict) -> DataCube:
# 
# #    import numpy
# 
#     # get the xarray    
#     array=cube.get_array()
# 
#     # create a copy
#     result=array.copy()    
# #     shape=list(array.shape)
# #     shape[array.dims.index('bands')]=1
# #     result=xarray.DataArray(
# #         numpy.full(shape, 0., numpy.float64),
# #         dims=array.dims,
# #         coords={
# #             't': array.coords['t'].values,
# #             'bands': ['evi']
# #         }
# #     )
# 
#     # compute reflectance
#     B02=array[:,array.bands.values.tolist().index('TOC-B02_10M')]
#     B04=array[:,array.bands.values.tolist().index('TOC-B04_10M')]
#     B08=array[:,array.bands.values.tolist().index('TOC-B08_10M')]
#     result.values[:,0] = (2.5 * (B08 - B04)) / ((B08 + 6.0 * B04 - 7.5 * B02) + 10000.0*1.0)
#     result.values[:,1:] = 0.
# 
#     # give proper name for results
#     #season=result.expand_dims('bands',3).assign_coords(bands=['evi']).astype(numpy.float64)
#     #result=result.assign_coords(bands=['evi','empty1','empty2']).astype(numpy.float64)
#     
#     return DataCube(result)

