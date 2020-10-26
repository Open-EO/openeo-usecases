import os
from pathlib import Path

import openeo
from openeo.rest.conversions import timeseries_json_to_pandas
import pandas as pd
from shapely.geometry import GeometryCollection
import json

connection = openeo.connect("https://openeo.vito.be")
connection.authenticate_basic("jrcusername","jrcusername123")

scl = connection.imagecollection(
    "TERRASCOPE_S2_TOC_V2",
    bands=["SCENECLASSIFICATION_20M"]
)
classification = scl.band("SCENECLASSIFICATION_20M")
scl_mask = (classification !=4)

#on Terrascope, NDVI is readily available, or compute it yourself from TERRASCOPE_S2_TOC_V2
datacube = connection.load_collection("TERRASCOPE_S2_NDVI_V2")

polygons_file = r'../data/BRP_Gewaspercelen_2017_subset.geojson'
import geopandas as gpd
#apply a
local_polygons = gpd.read_file(polygons_file)


def load_udf(relative_path):
    dir = Path(os.path.dirname(os.path.realpath(__file__)))
    with open(dir/relative_path, 'r+') as f:
        return f.read()

smoothing_udf = load_udf('./smooth_savitzky_golay.py')

#for zonal stats on large shp files: the file can be stored on terrascope, and batch jobs should be used
ndvi_zonal_statistics  = datacube\
    .mask(scl_mask)\
    .apply_dimension(smoothing_udf,dimension='t',runtime='Python')\
    .filter_temporal('2017-01-01', '2018-01-01')\
    .polygonal_mean_timeseries(GeometryCollection(list(local_polygons.geometry)))


print(json.dumps(ndvi_zonal_statistics.graph,indent=2))
#Backend can derive bbox from polygons provided to aggregate_spatial?
#.filter_bbox(west=5.251809,east=5.462144,north=51.838069,south=51.705835)\
result = ndvi_zonal_statistics.execute()

df = timeseries_json_to_pandas(result)
df.index = pd.to_datetime(df.index)
df.interpolate().plot()