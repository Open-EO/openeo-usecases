# -*- coding: utf-8 -*-
# Uncomment the import only for coding support
from typing import Dict
from scipy.signal import savgol_filter
from openeo.udf import XarrayDataCube

def apply_datacube(cube: XarrayDataCube, context: dict) -> XarrayDataCube:
    import functools
    import xarray
    import numpy
    from xarray.core.dataarray import DataArray
    import pandas
    from cropsar_px.model import load_generator_model

    # BUILTIN CONFIG #########################

    NDVI = 'ndvi'
    S2id = 'S2ndvi'
    VHid = 'VH'
    VVid = 'VV'

    gan_window_half = '90D'
    gan_steps = '5D'
    gan_samples = 37  # this is 2*gan_window_half/gan_steps+1
    acquisition_steps = '5D'
    gan_window_size = 256
    startdate = None
    enddate = None

    scaler = 'default'

    # FILL FROM CONTEXT IF THERE IS #########################

    if context is not None:
        gan_window_half = context.get('gan_window_half', gan_window_half)
        gan_steps = context.get('gan_steps', gan_steps)
        gan_samples = context.get('gan_samples', gan_samples)
        acquisition_steps = context.get('acquisition_steps', acquisition_steps)
        gan_window_size = context.get('gan_window_size', gan_window_size)
        scaler = context.get('scaler', scaler)
        startdate = context.get('startdate', startdate)
        enddate = context.get('enddate', enddate)

    # HELPER FUNCTIONS #########################

    @functools.lru_cache(maxsize=25)
    def load_datafusion_model():
        return load_generator_model()

    class default_scaler():

        def minmaxscaler(self, data, source):
            ranges = {}
            ranges[NDVI] = [-0.08, 1]
            ranges[VVid] = [-20, -2]
            ranges[VHid] = [-33, -8]
            # Scale between -1 and 1
            datarescaled = 2 * (data - ranges[source][0]) / (ranges[source][1] - ranges[source][0]) - 1
            return datarescaled

        def minmaxunscaler(self, data, source):
            ranges = {}
            ranges[NDVI] = [-0.08, 1]
            ranges[VVid] = [-20, -2]
            ranges[VHid] = [-33, -8]
            # Unscale
            dataunscaled = 0.5 * (data + 1) * (ranges[source][1] - ranges[source][0]) + ranges[source][0]
            return dataunscaled

    class passthrough_scaler():

        def minmaxscaler(self, data, source):
            return data

        def minmaxunscaler(self, data, source):
            return data

    def process_window(inarr, model, scaler, windowsize=256, nodata=0):

        inarr = inarr.ffill(dim='t').resample(t='1D').ffill().resample(t=gan_steps).ffill()

        # older tensorflows expect exact number of samples in every dimension
        if len(inarr.t) > gan_samples:
            trimfront = int((len(inarr.t) - gan_samples) / 2)
            trimback = trimfront + (0 if (len(inarr.t) - gan_samples) % 2 == 0 else 1)
            inarr = inarr.sel(t=inarr.t[trimfront:-trimback])
        if len(inarr.t) < gan_samples:
            trimfront = int((gan_samples - len(inarr.t)) / 2)
            trimback = trimfront + (0 if (gan_samples - len(inarr.t)) % 2 == 0 else 1)
            front = pandas.date_range(end=inarr.t.values.min() - pandas.to_timedelta(gan_steps), periods=trimfront,
                                      freq=gan_steps).values.astype(inarr.t.dtype)
            back = pandas.date_range(start=inarr.t.values.max() + pandas.to_timedelta(gan_steps), periods=trimback,
                                     freq=gan_steps).values.astype(inarr.t.dtype)
            inarr = inarr.reindex({'t': numpy.concatenate((front, inarr.t.values, back))})

        # grow it to 5 dimensions
        inarr = inarr.expand_dims(dim=['d0', 'd5'], axis=[0, 5])

        # select bands
        S2 = inarr.sel(bands=S2id)
        VH = inarr.sel(bands=VHid)
        VV = inarr.sel(bands=VVid)

        # Scale S1
        VV = scaler.minmaxscaler(VV, VVid)
        VH = scaler.minmaxscaler(VH, VHid)

        # Concatenate s1 data
        s1_backscatter = xarray.concat((VV, VH), dim='d5')

        # Scale NDVI
        s2_ndvi = scaler.minmaxscaler(S2, NDVI)

        # Remove any nan values
        # Passing in numpy arrays because reduces RAM usage (newer tensorflows copy out from xarray into a numpy array) and backwards compatibility goes further back in time
        s2_ndvi = s2_ndvi.fillna(nodata).values
        s1_backscatter = s1_backscatter.fillna(nodata).values

        # Run neural network
        predictions = model.predict((s1_backscatter, s2_ndvi))

        # Unscale
        predictions = scaler.minmaxunscaler(predictions, NDVI)

        return predictions.reshape((windowsize, windowsize))

    # MAIN CODE #########################

    # extract xarray
    inarr = cube.get_array()

    # rescale
    inarr.loc[{'bands': VHid}] = 10. * xarray.ufuncs.log10(inarr.sel(bands=VHid))
    inarr.loc[{'bands': VVid}] = 10. * xarray.ufuncs.log10(inarr.sel(bands=VVid))

    # compute windows
    xsize, ysize = inarr.x.shape[0], inarr.y.shape[0]
    windowlist = [((0, gan_window_size), (0, gan_window_size))]

    # init scaler
    sc = default_scaler()
    if scaler == 'passthrough': sc = passthrough_scaler()

    # load the model
    model = load_datafusion_model()

    # compute acquisition dates
    acquisition_dates = pandas.date_range(
        pandas.to_datetime(startdate) + pandas.to_timedelta(gan_window_half),
        pandas.to_datetime(enddate) - pandas.to_timedelta(gan_window_half),
        freq=acquisition_steps
    )

    # result buffer
    shape = [len(acquisition_dates), 1, 1, 1]
    shape[inarr.dims.index('x')] = xsize
    shape[inarr.dims.index('y')] = ysize
    predictions = DataArray(numpy.full(shape, numpy.nan, dtype=numpy.float32), dims=inarr.dims,
                            coords={'bands': ['predictions'], 't': acquisition_dates})

    # run processing
    for idate in acquisition_dates:
        for iwin in windowlist:
            data = inarr.isel({
                'x': slice(iwin[0][0], iwin[0][1]),
                'y': slice(iwin[1][0], iwin[1][1]),

            }).sel(t= slice(idate - pandas.to_timedelta(gan_window_half), idate + pandas.to_timedelta(gan_window_half)))
            ires = process_window(data, model, sc, gan_window_size, 0.).astype(numpy.float32)
            predictions.loc[{'t': idate, 'x': range(iwin[0][0], iwin[0][1]), 'y': range(iwin[1][0], iwin[1][1])}] = ires

    # return the predictions
    return XarrayDataCube(predictions)

def load_cropsar_px_udf()->str:
    import os
    with open(os.path.realpath(__file__), 'r+') as f:
        return f.read()
