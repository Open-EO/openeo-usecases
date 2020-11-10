from shapely.geometry import Polygon

from openeo import ImageCollection
import openeo

import logging
import os
from pathlib import Path
import json

import numpy as np
import pandas as pd

#enable logging in requests library
from openeo.rest.imagecollectionclient import ImageCollectionClient
#%matplotlib inline

start = "2017-05-01"
end = "2017-10-01"


polygon = Polygon(shell= [
            [
              5.152158737182616,
              51.18469636040683
            ],
            [
              5.15183687210083,
              51.181979395425095
            ],
            [
              5.152802467346191,
              51.18192559252128
            ],
            [
              5.153381824493408,
              51.184588760878924
            ],
            [
              5.152158737182616,
              51.18469636040683
            ]
          ])

polygon = Polygon(shell=[[5.143297433853149,51.18163191723127],[5.143297433853149,51.18450357774117],[5.159090280532837,51.18450357774117],[5.159090280532837,51.18163191723127],[5.143297433853149,51.18163191723127]])

minx,miny,maxx,maxy = polygon.bounds

#enlarge bounds, to also have some data outside of our parcel
minx -= 0.001
miny -= 0.001
maxx+=0.001
maxy+=0.001
polygon.bounds

session = openeo.session("nobody", "http://openeo.vgt.vito.be/openeo/0.4.0")

#retrieve the list of available collections
collections = session.list_collections()
s2_radiometry = session.imagecollection("CGS_SENTINEL2_RADIOMETRY_V102_001") \
                    .bbox_filter(left=minx,right=maxx,top=maxy,bottom=miny,srs="EPSG:4326")



B02 = s2_radiometry.band('2')
B04 = s2_radiometry.band('4')
B08 = s2_radiometry.band('8')

evi_cube_nodate: ImageCollectionClient = (2.5 * (0.0001*B08 - 0.0001*B04)) / ((0.0001*B08 + 6.0 * 0.0001*B04 - 7.5 * 0.0001*B02) + 1.0)

evi_cube = evi_cube_nodate.date_range_filter(start,end)

import sys
sys.getsizeof(evi_cube)

#write graph to json, as example
OUT_DIR = "/home/user/PycharmProjects/openEO_test/Data"
def write_graph(graph, filename):
    with open(filename, 'w') as outfile:
        json.dump(graph, outfile,indent=4)
write_graph(evi_cube.graph,os.path.join(OUT_DIR,"evi_cube.json"))


s2_sceneclassification = session.imagecollection("S2_FAPAR_SCENECLASSIFICATION_V102_PYRAMID") \
                    .bbox_filter(left=minx,right=maxx,top=maxy,bottom=miny,srs="EPSG:4326")

mask = s2_sceneclassification.band('classification')

# by convention, 4 is the forest class in the classification layer:
mask = mask != 4


date = "2017-08-21"
date2 = "2017-05-06"
mask_for_date = mask.date_range_filter(date,date)

# download data for a specific date:
mask_for_date.download(os.path.join(OUT_DIR,"mask%s.tiff"%date),format='GTIFF')
s2_sceneclassification.date_range_filter(date,date).download(os.path.join(OUT_DIR,"scf%s.tiff"%date),format='GTIFF')
evi_cube_nodate.date_range_filter(date,date).download(os.path.join(OUT_DIR,"evi_unmasked%s.tiff"%date),format='GTIFF')
evi_cube_nodate.date_range_filter(date,date).mask(rastermask=mask_for_date,replacement=np.nan).download(os.path.join(OUT_DIR,"masked%s.tiff"%date),format='GTIFF')

evi_cube.date_range_filter(date,date).mask(rastermask=mask_for_date,replacement=np.nan).download(os.path.join(OUT_DIR,"evi_cube_%s.tiff"%date),format='GTIFF')
evi_cube.date_range_filter(date2,date2).mask(rastermask=mask_for_date,replacement=np.nan).download(os.path.join(OUT_DIR,"evi_cube_%s.tiff"%date2),format='GTIFF')


os.chdir(OUT_DIR)
from rasterio.plot import show, show_hist
import rasterio
import matplotlib.pyplot as pyplot
fig, (axr, axg) = pyplot.subplots(1,2, figsize=(14,14))
with rasterio.open("evi_unmasked%s.tiff"%date) as src:
    band = src.read(1)
    show(band,ax=axg,cmap='RdYlGn_r')
    show_hist(band,ax=axr)



fig, (axr, axg) = pyplot.subplots(1,2, figsize=(14,14))
with rasterio.open("masked%s.tiff"%date) as src:
    band = src.read(1)
    show(band,ax=axg,cmap='RdYlGn_r')
    show_hist(band,ax=axr)

print(json.dumps(s2_radiometry.date_range_filter(date,date).mask(rastermask=mask_for_date,replacement=np.nan).graph,indent=1))


evi_cube_masked = evi_cube.mask(rastermask=mask.date_range_filter(start,end),replacement=np.nan)

# some problems with the code below ----------------------------------------------------------------------------
import colortools
service = evi_cube_masked.tiled_viewing_service(type='WMTS',style={'colormap':'RdYlGn'})
print(service)
# end of the problem code  -------------------------------------------------------------------------------------



timeseries_raw_dc = evi_cube.polygonal_mean_timeseries(polygon)
timeseries_raw = pd.Series(timeseries_raw_dc.execute(),name="evi_raw")
timeseries_raw.head(15)




timeseries_masked_dc = evi_cube_masked.polygonal_mean_timeseries(polygon)
timeseries_masked = pd.Series(timeseries_masked_dc.execute(),name='evi_masked')
timeseries_masked.head(15)




# import matplotlib.pyplot as plt
#
# all_timeseries = pd.DataFrame([timeseries_raw.dropna(),timeseries_masked.dropna()]).T
# all_timeseries.index = pd.to_datetime(all_timeseries.index)
#
# all_timeseries.plot(figsize=(14,7))
#
# timeseries_masked.index = pd.to_datetime(timeseries_masked.index)
# timeseries_masked.interpolate(axis=0).plot(figsize=(14,7))
#
#
#
# from scipy.signal import savgol_filter
# smooth_ts = pd.DataFrame(timeseries_masked.dropna())
# smooth_ts['smooth_5'] = savgol_filter(smooth_ts.evi_masked, 5, 1)
# smooth_ts['smooth_9'] = savgol_filter(smooth_ts.evi_masked, 9, 1)
# smooth_ts['smooth_9_poly'] = savgol_filter(smooth_ts.evi_masked, 9, 2)
# smooth_ts.plot(figsize=(14,7))
#
#
#
# filled_df = pd.DataFrame(timeseries_masked.dropna().asfreq('D',method='pad'))
# filled_df['smooth_5'] = savgol_filter(filled_df.evi_masked, 5, 1)
# filled_df['smooth_9'] = savgol_filter(filled_df.evi_masked, 9, 1)
# filled_df['smooth_9_poly'] = savgol_filter(filled_df.evi_masked, 9, 2)
# filled_df['smooth_15_poly'] = savgol_filter(filled_df.evi_masked, 15, 2)
#
# filled_df.plot(figsize=(14,7))


# ----------------------------------------------------------------------------------------------------------------------
# test UDF code:
def get_resource(relative_path):
    return str(Path(relative_path))


def load_udf(relative_path):
    import json
    with open(get_resource(relative_path), 'r+') as f:
        return f.read()


smoothing_udf = load_udf('/home/user/LVM_share/openEO_udf/smooth_savitzky_golay.py')
print(smoothing_udf)


# check the api documentation:
evi_cube_masked.apply_dimension

























