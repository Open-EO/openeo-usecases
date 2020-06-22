# Multi-source phonology use case

This usecase demonstrate the pixel-wise extraction of start and end dates of a season using the evi greenness time series.

## Calculation procedure

The layer being used is the Sentinel-2 based 'TERRASCOPE_S2_TOC_V2', which also offers a scene classification band. The process consists of the follwoing steps:
* Creating the cloud masking band based on te scene classification band (using apply_kernel). 
* Computing the vegetation index (from bands 2,4 and 8) using band math.
* Applying the mask on evi, this will replace filtered values with NaN-s in the datacube 
* Smoothing, interpolating and extrapolating the valid values over time by running an udf in apply_dimension.
* And finally the precosessed data is further processed by the actual phenology routing (again using an udf in an apply_dimension).

## Usage

Python pre-requisites on client side:
* openeo
* shapely
* numpy
* scipy
* xarray

The main Python script is multisource_phenology_usecase.py, this is how to run it:
* setup environment variables OPENEO_USER and OPENEO_PASS with your credentials
* in the script update the year and the area of interest (as geojson)
* run the script and the result will be donwloaded to the local computer as phenology.gtiff. 

This is a raster image with two bands (start of season: sos and end of season: eos). The values are floats as day of years from the first of january of the given year.

Remark: THIS PROCESS IS NOT TESTED WITH LARGE AREAS! Please split up your geometry to smaller areas, if possible.
