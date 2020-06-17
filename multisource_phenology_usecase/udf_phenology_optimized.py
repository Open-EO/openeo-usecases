# -*- coding: utf-8 -*-
# Uncomment the import only for coding support
from openeo_udf.api.datacube import DataCube
from typing import Dict


def apply_hypercube(cube: DataCube, context: Dict) -> DataCube:

    import xarray
    from xarray.ufuncs import fabs,isnan
    import numpy

    class Phenology:
        
        """
            sStartDate: First date of the interval for getting season start
            sEndDate: Last date of the interval for getting season start
        
            mStartDate: First date of the interval for getting maximum greenness
            mEndDate: Last date of the interval for getting maximum greenness
        
            eStartDate: First date of the interval for getting season end
            eEndDate: Last date of the interval for getting season end
        
            tSos: The offset (%) to add to the start date minimum to set the start of the season
            tEos: The offset (%) to subtract from the end date minimum to set the end of the season
        """
        def __init__(self,year,tdim,taxis):
            self.year=  year                                 # year of the season, int
            self.tdim = tdim                                 # the name of the time dimension (string)
            self.taxis = taxis                               # the index of the time dimension (int)
            self.sStart=numpy.datetime64(str(year)+'-04-02') # Start date of interval for start of season
            self.sEnd=  numpy.datetime64(str(year)+'-06-10') # End date of tart interval for start of season
            self.mStart=numpy.datetime64(str(year)+'-06-10') # Start date of interval for mid of season
            self.mEnd=  numpy.datetime64(str(year)+'-09-01') # End date of tart interval for mid of season
            self.eStart=numpy.datetime64(str(year)+'-09-01') # Start date of interval for end of season
            self.eEnd=  numpy.datetime64(str(year)+'-12-31') # End date of tart interval for end of season
            self.tSos=  10.                                  # Threshold for start of season
            self.tEos=  10.                                  # Threshold for end of season


        """
            Calculate the maximum greenness in the mid-season as reference
        """
        def getLocalMax(self,array):
            # Get the local maximum greenness
            seasonMid_Range=array.sel(t=slice(self.mStart,self.mEnd))
            seasonMid_MaxGreennessIdx=seasonMid_Range.argmax('t')
            #seasonMid_DateAtMax=seasonMid_Range.t[seasonMid_MaxGreennessIdx].dt.dayofyear
            seasonMid_MaxGreenness=seasonMid_Range.isel(t=seasonMid_MaxGreennessIdx)
            return seasonMid_MaxGreenness
    
    
        """
            Calculate the start of the season based on selected interval [start, end] and a greenness curve (df). 
            Within this interval we will first look for the local minimum greenness, marked by (dsMin, ysMin). In the
            second step we will use the offset (%) to calculate the amount greenness offset that needs to be applied to 
            the minumum value in order to get the start of the season. This offset is calculated as a percentage of the 
            difference between the maximum greenness and the local minimum.
        """
        def getStartOfSeason(self,array, sMmaxgreen):
            # compute the minimum in the season start
            seasonStart_Range=array.sel(t=slice(self.sStart,self.sEnd))
            seasonStart_MinGreennessIdx=seasonStart_Range.argmin('t')
            seasonStart_DateAtMin,seasonStart_MinGreenness=seasonStart_Range.t[seasonStart_MinGreennessIdx].dt.dayofyear,seasonStart_Range.isel(t=seasonStart_MinGreennessIdx)
            # Calculate the greenness value corresponding to the start of the season
            seasonStart_Greenness = seasonStart_MinGreenness + ((sMmaxgreen - seasonStart_MinGreenness) * (self.tSos / 100.0))
            # Get the closest date to this greenness
            #for i in range(len(seasonStart_Range[:])): seasonStart_Range[i]=seasonStart_Range[i]-seasonStart_Greenness
            seasonStart_Range=fabs(seasonStart_Range-seasonStart_Greenness)
            seasonStart_Idx=seasonStart_Range.where(seasonStart_Range.t.dt.dayofyear>=seasonStart_DateAtMin).argmin('t',skipna=True)
            seasonStart_Date=seasonStart_Range.t[seasonStart_Idx].dt.dayofyear
            return seasonStart_Date
    
    
        """
            Calculate the end of the season based on selected interval [start, end] and a greenness curve (df). 
            Within this interval we will first look for the local minimum greenness, marked by (deMin, yeMin). In the
            second step we will use the offset (%) to calculate the amount greenness offset that needs to be applied to 
            the minumum value in order to get the start of the season. This offset is calculated as a percentage of the 
            difference between the maximum greenness and the local minimum.
        """
        def getEndOfSeason(self, array, sMmaxgreen):
            # compute the minimum in the season start
            seasonEnd_Range=array.sel(t=slice(self.eStart,self.eEnd))
            seasonEnd_MinGreennessIdx=seasonEnd_Range.argmin('t')
            seasonEnd_DateAtMin,seasonEnd_MinGreenness=seasonEnd_Range.t[seasonEnd_MinGreennessIdx].dt.dayofyear,seasonEnd_Range.isel(t=seasonEnd_MinGreennessIdx)
            # Calculate the greenness value corresponding to the start of the season
            seasonEnd_Greenness = seasonEnd_MinGreenness + ((sMmaxgreen - seasonEnd_MinGreenness) * (self.tEos / 100.0))
            # Get the closest date to this greenness
            #for i in range(len(seasonEnd_Range[:])): seasonEnd_Range[i]=seasonEnd_Range[i]-seasonEnd_Greenness
            seasonEnd_Range=fabs(seasonEnd_Range-seasonEnd_Greenness)
            seasonEnd_Idx=seasonEnd_Range.where(seasonEnd_Range.t.dt.dayofyear<=seasonEnd_DateAtMin).argmin('t',skipna=True)
            seasonEnd_Date=seasonEnd_Range.t[seasonEnd_Idx].dt.dayofyear
            return seasonEnd_Date


    # get the xarray, selecting band zero if multiple bands present    
    # also building bands and t removed metadata
    array=cube.get_array()
    origdims=list(array.dims)
    array=array.isel(bands=range(0,1)).squeeze('bands',drop=True)
    dims=list(array.dims)
    dims.remove('t')
    coords=dict(array.coords)
    coords.pop('t')
    
    # guard agains missing data (Nan's)
    # input data should already be smoothed and interpolated
    missingmask=isnan(array).any('t')
    array=array.fillna(0.)

    # run phenology bundle    
    pp=Phenology(int(array.t.dt.year[0]),'t',array.dims.index('t')) 
    seasonMid_MaxGreenness=pp.getLocalMax(array)
    seasonStart_Date=pp.getStartOfSeason(array, seasonMid_MaxGreenness)
    seasonEnd_Date=pp.getEndOfSeason(array, seasonMid_MaxGreenness)

    # combine results
    seasonStart_Date=xarray.DataArray(seasonStart_Date,dims=dims,coords=coords)
    seasonEnd_Date=xarray.DataArray(seasonEnd_Date,dims=dims,coords=coords)
    season=xarray\
        .concat([seasonStart_Date,seasonEnd_Date],dim='bands')\
        .expand_dims('t',0)\
        .assign_coords(bands=['sos','eos'],t=[numpy.datetime64(str(pp.year)+"-01-01")])\
        .astype(numpy.float64)
    
    # set missing data to 0, exploiting that at this point t,bands are the first two coordinates
    season=season.where(~missingmask,0.)

    # set the original order of dimensions
    season=season.transpose(*origdims)
    
    return DataCube(season)


