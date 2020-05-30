# -*- coding: utf-8 -*-
# Uncomment the import only for coding support
from openeo_udf.api.datacube import DataCube
from typing import Dict


def apply_hypercube(cube: DataCube, context: Dict) -> DataCube:

    import xarray
    import numpy
    from scipy.signal import savgol_filter

    # access the underlying xarray
    inarr=cube.get_array()
    
    # create date range with daily resolution (that is the least common denominator with the expected input)
    year=int(inarr.t.dt.year[0])
    daterange=numpy.arange(numpy.datetime64(str(year)+'-01-01'), numpy.datetime64(str(year+1)+'-03-31'))
    
    # create an xarray that matches input, except the time resolution and copy values over
    outarr=xarray.DataArray(numpy.full((len(daterange),inarr.bands.shape[0],inarr.x.shape[0],inarr.y.shape[0]),numpy.NaN),dims=inarr.dims,coords={'t':daterange,'bands':inarr.bands})
    outarr.loc[inarr.t.loc[daterange[0]:daterange[-1]]]=inarr.loc[inarr.t.loc[daterange[0]:daterange[-1]]]
    
    # fill in empty values (NaN`s)
    outarr=outarr.interpolate_na('t').bfill('t').ffill('t')
    
    # perform a moving average smoothin with a:
    #   3 months window (largest timescale that still resolves trends looked at by phenology) 
    #   polynomial order 3 (allow an inflexion point)
    outarr=xarray.DataArray(savgol_filter(outarr.values, 91, 3, axis=outarr.dims.index('t'), mode='interp'),dims=outarr.dims,coords=outarr.coords)

    # cropping to 03-01 to 12-31, because that's what is used by phenology & wrap back to datacube
    r=DataCube(outarr.loc[numpy.datetime64(str(year)+'-04-01'):numpy.datetime64(str(year)+'-12-31')])
    return r


