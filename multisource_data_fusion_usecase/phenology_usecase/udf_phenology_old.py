# -*- coding: utf-8 -*-
# Uncomment the import only for coding support
from openeo_udf.api.datacube import DataCube
from typing import Dict


def apply_datacube(cube: DataCube, context: Dict) -> DataCube:

    import pandas
    import xarray
    import numpy
    
    class PhenologypParams:
        
        def __init__(self,year):
            self.year=  year # yer of the season, int
            self.sStart=pandas.DateOffset(months=4, days=2)  # Start date of interval for start of season
            self.sEnd=  pandas.DateOffset(months=6, days=10) # End date of tart interval for start of season
            self.mStart=pandas.DateOffset(months=6, days=10) # Start date of interval for mid of season
            self.mEnd=  pandas.DateOffset(months=9, days=1)  # End date of tart interval for mid of season
            self.eStart=pandas.DateOffset(months=9, days=1)  # Start date of interval for end of season
            self.eEnd=  pandas.DateOffset(months=12,days=31) # End date of tart interval for end of season
            self.tSos=  10.          # Threshold for start of season
            self.tEos=  10.          # Threshold for end of season
    
    
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
    class CropPhenology:
    
        def extractSeasonDates(self, timeseries, args):
    
            if timeseries is None:
                return None
            else:

                # Get the local maximum greenness
                mMax = self.getLocalMax(timeseries, pandas.Timestamp(args.year,args.mStart.months,args.mStart.days), pandas.Timestamp(args.year,args.mEnd.months,args.mEnd.days))
                dmMax = mMax['Times']
                ymMax = mMax['Greenness']
    
                # Get the start of season dates
                sos = self.getStartOfSeason(timeseries, pandas.Timestamp(args.year,args.sStart.months,args.sStart.days), pandas.Timestamp(args.year,args.sEnd.months,args.sEnd.days), float(args.tSos), float(ymMax))
    
                # Get the end of season dates
                eos = self.getEndOfSeason(timeseries, pandas.Timestamp(args.year,args.eStart.months,args.eStart.days), pandas.Timestamp(args.year,args.eEnd.months,args.eEnd.days), float(args.tEos), float(ymMax))
    
                #return result
                return [sos[3],eos[3]]
    
        def getLocalMax(self, df, start, end):
            df_range = df.loc[df['Times'].between(start, end)]
            return df_range.loc[df_range['Greenness'].idxmax()]
    
        """
            Calculate the start of the season based on selected interval [start, end] and a greenness curve (df). 
            Within this interval we will first look for the local minimum greenness, marked by (dsMin, ysMin). In the
            second step we will use the offset (%) to calculate the amount greenness offset that needs to be applied to 
            the minumum value in order to get the start of the season. This offset is calculated as a percentage of the 
            difference between the maximum greenness and the local minimum.
        """
        def getStartOfSeason(self, df, start, end, offset, yMax):
            # Get the local minimum greenness in the start season interval
            df_sRange = df.loc[df['Times'].between(start, end)]
            sMin = df_sRange.loc[df_sRange['Greenness'].idxmin()]
            dsMin = sMin['Times']
            ysMin = sMin['Greenness']
    
            # Calculate the greenness value corresponding to the start of the season
            ySos = ysMin + ((yMax - ysMin) * (offset / 100.0))
    
            # Get the closest value to this greenness
            df_sRange = df_sRange.loc[df_sRange['Times'] >= dsMin]
            sos = df_sRange.iloc[(df_sRange['Greenness'] - ySos).abs().argsort()[:1]]
            return (dsMin, ysMin, ySos, pandas.to_datetime(str(sos['Times'].values[0])))
    
        """
            Calculate the end of the season based on selected interval [start, end] and a greenness curve (df). 
            Within this interval we will first look for the local minimum greenness, marked by (deMin, yeMin). In the
            second step we will use the offset (%) to calculate the amount greenness offset that needs to be applied to 
            the minumum value in order to get the start of the season. This offset is calculated as a percentage of the 
            difference between the maximum greenness and the local minimum.
        """
    
        def getEndOfSeason(self, df, start, end, offset, yMax):
            # Get the local minimum greenness in the start season interval
            df_eRange = df.loc[df['Times'].between(start, end)]
            eMin = df_eRange.loc[df_eRange['Greenness'].idxmin()]
            deMin = eMin['Times']
            yeMin = eMin['Greenness']
    
            # Calculate the greenness value corresponding to the start of the season
            yEos = yeMin + ((yMax - yeMin) * (offset / 100.0))
    
            # Get the closest value to this greenness
            df_eRange = df_eRange.loc[df_eRange['Times'] <= deMin]
            eos = df_eRange.iloc[(df_eRange['Greenness'] - yEos).abs().argsort()[:1]]
            return (deMin, yeMin, yEos, pandas.to_datetime(str(eos['Times'].values[0])))    
        

    
    array=cube.get_array()
    cropphenology=CropPhenology()
    phenologyparams=PhenologypParams(int(array.t.dt.year[0])) 
    season=xarray.DataArray(numpy.zeros((2,array.x.shape[0],array.y.shape[0]),dtype=numpy.datetime64),dims=('bands','x', 'y'),coords={'bands': ['sos','eos']})
        
    for ix in array.x.values:
        for iy in array.y.values:
            iserie=pandas.DataFrame(data={
                'Greenness':array[:,0,ix,iy].values,
                'Times':array.t.values
            })
            iseason=cropphenology.extractSeasonDates(iserie, phenologyparams)
            #season.values[:,ix,iy]=[iseason[0].dayofyear,iseason[1].dayofyear]
            season.values[:,ix,iy]=iseason

    return DataCube(season)