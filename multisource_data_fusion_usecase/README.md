# Data fusion

This usecase demonstrates using multiple data sources (Sentinel-1, 2 and ProbaV) in a single process.

## Usage

Python pre-requisites on client side:
* openeo
* shapely
* numpy
* scipy

The main Python script is multisource_data_fusion_usecase.py, this is how to run it:
* setup environment variables OPENEO_USER and OPENEO_PASS with your credentials
* also define OPENEO_MODEL to the filepath of the AI model to be used 
* in the script update the year and the area of interest (as geojson)
* run the script and the result will be donwloaded to the local computer as phenology.gtiff. 

Remark: THIS PROCESS IS NOT TESTED WITH LARGE AREAS! Please split up your geometry to smaller areas, if possible.
