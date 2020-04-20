import openeo
import logging              
import os
from datetime import datetime, date, time, timedelta
from shapely.geometry import Polygon
from pathlib import Path

logging.basicConfig(level=logging.INFO)

# initiate a session to the vito backend:
VITO_DRIVER_URL = "https://openeo.vito.be/openeo/0.4.0/"
session = openeo.connect(VITO_DRIVER_URL)
# load the image collection:
s1 = session.imagecollection("SENTINEL1_GAMMA0_SENTINELHUB",bands=["VV_DB","VH_DB"])

# ----------------------------------------------------------------------------------------------------------------------
# prepare a data cupe for the time and area of interest:
# ----------------------------------------------------------------------------------------------------------------------
# define the dates and area of interest:
start_date = date(2016,1,1)
end_date = date(2019,11,26)
aoi_polygon = Polygon(
    shell=[[-55.8771, -6.7614], [-55.8771, -6.6503], [-55.7933, -6.6503], [-55.7933, -6.7614],
           [-55.8771, -6.7614]])
myCRS = "EPSG:4326"

# filter to a smaller datacube:
s1_vh = s1.filter_temporal([start_date.strftime("%Y-%m-%dT%H:%M:%S"), end_date.strftime("%Y-%m-%dT%H:%M:%S")]) \
    .filter_bbox(west=aoi_polygon.bounds[0], east=aoi_polygon.bounds[2], north=aoi_polygon.bounds[3], south=aoi_polygon.bounds[1], crs=myCRS) \
    .filter_bands(["VH_DB"])

# ----------------------------------------------------------------------------------------------------------------------
# prepare functions to load the udf code:
# ----------------------------------------------------------------------------------------------------------------------
def get_resource(relative_path):
    return str(Path(relative_path))

def load_udf(relative_path):
    with open(get_resource(relative_path), 'r+') as f:
        return f.read()

# ----------------------------------------------------------------------------------------------------------------------
# load and apply the udf code on data cube::
# ----------------------------------------------------------------------------------------------------------------------
BFASTMonitor_udf = load_udf('BFAST_udf.py')

# apply the udf code to reduce the data cube along the time dimension and get a raster which values shows
# the day of the year 2019 where the break was detected:
break_days = s1_vh.reduce(BFASTMonitor_udf, dimension='time')

# ----------------------------------------------------------------------------------------------------------------------
# download the deforestation probability map for a certain date:
# ----------------------------------------------------------------------------------------------------------------------
# specify the raster output format
OUTFORMAT = "GTIFF"
# download the particular map:
break_days.download("breaks_detected_in_2019.tiff", format=OUTFORMAT)
# ----------------------------------------------------------------------------------------------------------------------
