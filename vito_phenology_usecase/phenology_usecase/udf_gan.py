# -*- coding: utf-8 -*-
# Uncomment the import only for coding support
from openeo_udf.api.datacube import DataCube
from typing import Dict



def apply_datacube(cube: DataCube, context: Dict) -> DataCube:

    import xarray
    import numpy
    import itertools
    from xarray.core.dataarray import DataArray
    import pandas
    from tensorflow.python.keras.models import load_model

    # BUILTIN CONFIG #########################

    NDVI='ndvi'
    PVid='ndvi'
    B4id='TOC-B04_10M'
    B8id='TOC-B08_10M'
    VHid='VH'
    VVid='VV'

    prediction_model=""
    
    gan_window_half='90D'
    gan_steps='5D'
    gan_samples=37 # this is 2*gan_window_half/gan_steps+1
    acquisition_steps='10D'

    if context is not None:
        prediction_model=context.get('prediction_model',prediction_model)

    # HELPER FUNCTIONS #########################

    def computeWindowLists(bboxWindow, imageSize, windowsize, stride):
        '''
        bboxWindow: ((xmin,xmax),(ymin,ymax)) or None to use full image
        imageSize: (width,height)
        windowSize: size of blocks to split bboxWindow
        stride: overlaps width neighbours
        
        returns: 2d list of windows, where each window element is in the format ((xmin,xmax),(ymin,ymax))
        '''
        if bboxWindow is None:  bbox=[0,0,imageSize[0],imageSize[1]]
        else: bbox=[bboxWindow[0][0],bboxWindow[1][0],bboxWindow[0][1],bboxWindow[1][1]]
        
        # because sride amount of frame is not filled in the wind with windowsize -> bbox has to be enlarged
        bbox[0]= bbox[0]-stride if bbox[0]-stride>=0 else 0 
        bbox[1]= bbox[1]-stride if bbox[1]-stride>=0 else 0
        bbox[2]= bbox[2]+stride if bbox[2]+stride<=imageSize[0] else imageSize[0]
        bbox[3]= bbox[3]+stride if bbox[3]+stride<=imageSize[1] else imageSize[1]
         
        # We need to check if we're at the end of the master image
        # We have to make sure we have a full subtile
        # so we need to expand such tile and the resulting overlap
        # with previous subtile is not an issue
        windowlist=[]
        for xStart in range(bbox[0], bbox[2], windowsize - 2 * stride):
            
            windowlist.append([])
            
            if xStart + windowsize > bbox[2]:
                xStart = bbox[2] - windowsize
                xEnd = bbox[2]
            else:
                xEnd = xStart + windowsize
    
            for yStart in range(bbox[1], bbox[3], windowsize - 2 * stride):
                if yStart + windowsize > bbox[3]:
                    yStart = bbox[3] - windowsize
                    yEnd = bbox[3]
                else:
                    yEnd = yStart + windowsize
    
                windowlist[len(windowlist)-1].append(((xStart, xEnd), (yStart, yEnd)))
        
                if (yEnd==bbox[3]): break
            if (xEnd==bbox[2]): break
    
        return windowlist
    
    
    def minmaxscaler(data, source):
        ranges = {}
        ranges[NDVI] = [-0.08, 1]
        ranges[VVid] = [-20, -2]
        ranges[VHid] = [-33, -8]
        # Scale between -1 and 1
        datarescaled = 2*(data - ranges[source][0])/(ranges[source][1] - ranges[source][0]) - 1
        return datarescaled


    def minmaxunscaler(data, source):
        ranges = {}
        ranges[NDVI] = [-0.08, 1]
        ranges[VVid] = [-20, -2]
        ranges[VHid] = [-33, -8]
        # Unscale
        dataunscaled = 0.5*(data + 1) * (ranges[source][1] - ranges[source][0]) + ranges[source][0]
        return dataunscaled


    def process_window(inarr, model, windowsize=128, nodata=0):
    
# SKIPPING THIS BECAUSE RELYING ON PROPERLY SETTING FILTER TEMPORAL IN THE OPENEO PROCESS
# THIS MIGHT THROWS NOT ALL DIMENSIONS FOUND IN t: output_index DATE RANGE IS BIGGER THAN WHAT IS IN INARR
#         # select +-90days interval relative to acquisitiondate
#         output_index = pd.date_range(acquisitiondate - pd.to_timedelta('90D'),
#                                      acquisitiondate + pd.to_timedelta('90D'),
#                                      freq='5D')
#         inarr=inarr.ffill(dim='t').resample(t='1D').ffill().sel({'t': output_index}, method='ffill')

# TODO: test: window loader in parcelremoves all dateswhere even a single pixel is nodata in any of the variables

        inarr=inarr.ffill(dim='t').resample(t='1D').ffill().resample(t=gan_steps).ffill()
        
        # older tensorflows expect exact number of samples in every dimension
        if len(inarr.t)>gan_samples:
            trimfront=int((len(inarr.t)-gan_samples)/2)
            trimback=trimfront + (0 if (len(inarr.t)-gan_samples)%2==0 else 1)
            inarr=inarr.sel(t=inarr.t[trimfront:-trimback])
        if len(inarr.t)<gan_samples:
            trimfront=int((gan_samples-len(inarr.t))/2)
            trimback=trimfront + (0 if (gan_samples-len(inarr.t))%2==0 else 1)
            front=pandas.date_range(end=inarr.t.values.min()-pandas.to_timedelta(gan_steps), periods=trimfront, freq=gan_steps).values.astype(inarr.t.dtype)
            back=pandas.date_range(start=inarr.t.values.max()+pandas.to_timedelta(gan_steps), periods=trimback, freq=gan_steps).values.astype(inarr.t.dtype)
            inarr=inarr.reindex({'t':numpy.concatenate((front,inarr.t.values,back))})
        
        # grow it to 5 dimensions
        inarr=inarr.expand_dims(dim=['d0','d5'],axis=[0,5])
        
        # select bands
        PV=inarr.sel(bands=PVid)
        B4=inarr.sel(bands=B4id)
        B8=inarr.sel(bands=B8id)
        VH=inarr.sel(bands=VHid)
        VV=inarr.sel(bands=VVid)
     
        # Scale S1
        VV = minmaxscaler(VV, VVid)
        VH = minmaxscaler(VH, VHid)
    
        # Concatenate s1 data
        s1_backscatter = xarray.concat((VV, VH), dim='d5')
    
        # Calculate NDVI
        s2_ndvi = (B8-B4)/(B8+B4)
    
        # Scale NDVI
        s2_ndvi = minmaxscaler(s2_ndvi, NDVI)
        probav_ndvi = minmaxscaler(PV, NDVI)
    
        # Remove any nan values
        # Passing in numpy arrays because reduces RAM usage (newer tensorflows copy out from xarray into a numpy array) and backwards compatibility goes further back in time
        s2_ndvi=s2_ndvi.fillna(nodata).values
        s1_backscatter=s1_backscatter.fillna(nodata).values
        probav_ndvi=probav_ndvi.fillna(nodata).values
    
        # Run neural network
        predictions = model.predict((s1_backscatter, s2_ndvi, probav_ndvi))
    
        # Unscale
        predictions = minmaxunscaler(predictions, NDVI)
    
        return predictions.reshape((windowsize, windowsize))

    # MAIN CODE #########################

    # extract xarray
    inarr=cube.get_array()
            
    # rescale
    inarr.loc[{'bands':PVid}]=0.004*inarr.sel(bands=PVid)-0.08
    inarr.loc[{'bands':B4id}]*=0.0001
    inarr.loc[{'bands':B8id}]*=0.0001
    inarr.loc[{'bands':VHid}]=10.*xarray.ufuncs.log10(inarr.sel(bands=VHid))
    inarr.loc[{'bands':VVid}]=10.*xarray.ufuncs.log10(inarr.sel(bands=VVid))
    
    # compute windows
    xsize,ysize=inarr.x.shape[0],inarr.y.shape[0]
    windows=computeWindowLists(((0,xsize),(0,ysize)), (xsize,ysize), 128, 8)
    windowlist=list(itertools.chain(*windows))
    
    # load the model
    model=load_model(prediction_model)

    # compute acquisition dates
    acquisition_dates = pandas.date_range(
        inarr.t.values.min() + pandas.to_timedelta(gan_window_half),
        inarr.t.values.max() - pandas.to_timedelta(gan_window_half),
        freq=acquisition_steps
    )

    # result buffer
    shape=[len(acquisition_dates),1,1,1]
    shape[inarr.dims.index('x')]=xsize
    shape[inarr.dims.index('y')]=ysize
    predictions=DataArray(numpy.full(shape,numpy.nan),dims=inarr.dims,coords={'bands':['predictions'],'t':acquisition_dates})
    
    # run processing
    for idate in acquisition_dates:
        for iwin in windowlist:
            data=inarr.sel({
                'x':slice(iwin[0][0],iwin[0][1]),
                'y':slice(iwin[1][0],iwin[1][1]),
                't':slice(idate-pandas.to_timedelta(gan_window_half), idate+pandas.to_timedelta(gan_window_half))
            })
            ires = process_window(data, model, 128, 0.)
            predictions.loc[{'t':idate,'x':range(iwin[0][0],iwin[0][1]),'y':range(iwin[1][0],iwin[1][1])}]=ires
            
    # return the predictions
    return DataCube(predictions)
