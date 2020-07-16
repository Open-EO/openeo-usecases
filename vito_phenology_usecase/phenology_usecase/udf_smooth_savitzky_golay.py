# -*- coding: utf-8 -*-
# Uncomment the import only for coding support
from openeo_udf.api.datacube import DataCube
from typing import Dict


def apply_datacube(cube: DataCube, context: Dict) -> DataCube:

    import xarray
    import numpy
    import pandas
    from scipy.signal import savgol_filter

    # access the underlying xarray
    inarr=cube.get_array()
    tdim='t'
    taxis=inarr.dims.index(tdim)
    
    # create date range with daily resolution (which is the least common denominator with the expected input)
    year=int((inarr.t.min()+(inarr.t.values.max()-inarr.t.min())/2).dt.year)#int(inarr.t.dt.year[0])
    daterange=numpy.arange(numpy.datetime64(str(year)+'-01-01'), numpy.datetime64(str(year+1)+'-04-01'))
    
    # create an xarray that matches input, except the time resolution and copy values over
    outshape=list(inarr.shape)
    outshape[taxis]=len(daterange)
    outcoords=dict(map(lambda x: (x.name,x.values),inarr.coords.values()))
    outcoords[tdim]=daterange
    outarr=xarray.DataArray(numpy.full(outshape,numpy.NaN),dims=inarr.dims,coords=outcoords)
    outarr=outarr.combine_first(inarr)

    # fill in empty values (NaN`s)
    outarr=outarr.interpolate_na(tdim).bfill(tdim).ffill(tdim)
    
    # perform a moving average smoothin with a:
    #   3 months window (largest timescale that still resolves trends looked at by phenology) 
    #   polynomial order 3 (allow an inflexion point)
    smootheddata=savgol_filter(outarr.values, 91, 3, axis=taxis, mode='interp')
    outarr=xarray.DataArray(smootheddata,dims=outarr.dims,coords=outarr.coords)

    # cropping to 03-01 to 12-31, because that's what is used by phenology
    outarr=outarr.loc[{'t':slice(numpy.datetime64(str(year)+'-04-01'),numpy.datetime64(str(year)+'-12-31'))}]

    # wrap back to datacube and return
    return DataCube(outarr)


