import openeo
import logging              
import os
from datetime import datetime, date, time, timedelta
from shapely.geometry import Polygon
from pathlib import Path

logging.basicConfig(level=logging.INFO)
# chenge to your working dir:
workDir = '/home/milutin/rStudioProjects/final-user-workshop/WUR_BFAST_UseCase/Python/'
os.chdir(workDir)

# initiate a session to the vito backend:
VITO_DRIVER_URL = "https://openeo.vito.be/openeo/1.0/"
my_user = ''
my_pass = ''
#
session = openeo.connect(VITO_DRIVER_URL).authenticate_basic(username=my_user, password=my_pass)

#  upload our data manually:
s1 = session.load_disk_collection('GTiff', str('/data/users/Public/driesj/openeo/WUR/with_srs/S1A_VH*.tif'), options={'date_regex': '.*S1A_VH_(\d{4})-(\d{2})-(\d{2}).tif'})
s1_cube = s1.filter_bbox(west=-6105178, east=-6097840, north=-388911, south=-396249, crs="EPSG:3857")

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
# apply the udf:
udf_out = s1_cube.reduce_dimension(BFASTMonitor_udf, dimension='t', runtime='Python')


udf_out = s1_cube.apply_dimension(BFASTMonitor_udf, dimension='t', runtime='Python')

# the rest of the script to be run with SentinelHUB data

# load the image collection:
# session.list_collections()
# s1 = session.imagecollection("SENTINEL1_GAMMA0_SENTINELHUB", bands="VH_DB")

# ----------------------------------------------------------------------------------------------------------------------
# prepare a data cube for the time and area of interest:
# ----------------------------------------------------------------------------------------------------------------------
# define the dates and area of interest:
start_date = date(2016, 12, 31)
end_date = date(2019, 12, 31)
myCRS = "EPSG:4326"

# filter to a smaller datacube:
s1_vh = s1.filter_temporal([start_date.strftime("%Y-%m-%dT%H:%M:%S"), end_date.strftime("%Y-%m-%dT%H:%M:%S")]) \
    .filter_bbox(west=-54.815,
                 south=-3.515,
                 east=-54.810,
                 north=-3.510)


# s1_vh.max_time().download('S1_max_time_SentHUB.tif')

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
# break_days = s1_vh.reduce(BFASTMonitor_udf, dimension='time')
# break_days = s1_vh.run_udf(BFASTMonitor_udf)


# ----------------------------------------------------------------------------------------------------------------------
# download the deforestation probability map for a certain date:
# ----------------------------------------------------------------------------------------------------------------------
# specify the raster output format
OUTFORMAT = "GTIFF"
# download the particular map:
break_days.download("breaks_detected_in_2019.tiff", format=OUTFORMAT)
# ----------------------------------------------------------------------------------------------------------------------
