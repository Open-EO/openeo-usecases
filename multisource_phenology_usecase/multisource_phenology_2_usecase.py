'''
Created on May 14, 2020

@author: banyait
'''

import openeo
import logging
import shapely.geometry
import os
import utils


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

openeo_url='http://openeo-dev.vgt.vito.be/openeo/1.0.0/'
#openeo_url='http://openeo.vgt.vito.be/openeo/0.4.0/'

openeo_user=os.environ.get('OPENEO_USER','wrong_user')
openeo_pass=os.environ.get('OPENEO_PASS','wrong_password')

fieldgeom={
    "type":"FeatureCollection",
    "name":"small_field",
    "crs":{"type":"name","properties":{"name":"urn:ogc:def:crs:OGC:1.3:CRS84"}},
    "features":[
        {"type":"Feature","properties":{},"geometry":{"type":"Polygon","coordinates":[[[5.497022,51.130558],[5.498517,51.130266],[5.498855,51.129749],[5.496834,51.130137],[5.497022,51.130558]]]}}
    ]
}

year=2019
layerID_data="TERRASCOPE_S2_TOC_V2"
#layerID_data="S2_FAPAR_V102_WEBMERCATOR2"
#layerID_mask="S2_FAPAR_SCENECLASSIFICATION_V102_PYRAMID"

job_options={
    'driver-memory':'4G',
    'executor-memory':'2G'
}

def getImageCollection(eoconn, layerid, fieldgeom, year, bands):
#    startdate=str(year)+'-01-01'
#    enddate=str(year+1)+'-03-31'
    startdate=str(year)+'-01-01'
    enddate=str(year)+'-01-10'
    polys = shapely.geometry.GeometryCollection([shapely.geometry.shape(feature["geometry"]).buffer(0) for feature in fieldgeom["features"]])
    bbox = polys.bounds
    return eoconn.load_collection(
        layerid,
        temporal_extent=[startdate, enddate],
        bands=bands
    ).filter_bbox(crs="EPSG:4326", **dict(zip(["west", "south", "east", "north"], bbox)))
#     return eoconn \
#         .load_collection(layerid) \
#         .filter_temporal(startdate, enddate) \
#         .filter_bbox(crs="EPSG:4326", **dict(zip(["west", "south", "east", "north"], bbox)))

if __name__ == '__main__':
    eoconn=openeo.connect(openeo_url)
    eoconn.authenticate_basic(openeo_user,openeo_pass)
#    eoconn=openeo.session(openeo_user,openeo_url)

#    maskCollection=getImageCollection(eoconn, layerID_mask, fieldgeom, year)#.apply_dimension(utils.load_udf('udf_vito_save_to_public.py'),dimension='t',runtime="Python")
#    mskExec=maskCollection.execute()
    
    dataCollection=getImageCollection(eoconn, layerID_data, fieldgeom, year, ["TOC-B02_10M","TOC-B04_10M","TOC-B08_10M"])\
        .apply_dimension(utils.load_udf('udf_vito_save_to_public.py'),dimension='t',runtime="Python")\
        .execute_batch("tmp/batchtest.json",job_options=job_options)

#         .apply_dimension(utils.load_udf('udf_evi.py'),dimension='t',runtime="Python")\
#         .apply_dimension(utils.load_udf('udf_vito_save_to_public.py'),dimension='t',runtime="Python")\
    
#     dataCollection=dataCollection\
#         .graph_add_process(
#             process_id='rename_dimension',
#             args={
#                 'data':   dataCollection.node_id,
#                 'old': 'TOC-B05_20M',
#                 'new': 'nir'
#             }
#         )
# 
#     dataCollection=dataCollection\
#         .graph_add_process(
#             process_id='rename_dimension',
#             args={
#                 'data':   dataCollection.node_id,
#                 'old': 'TOC-B04_10M',
#                 'new': 'red'
#             }
#         )
#         
#         
#     dataCollection=dataCollection\
#         .apply_dimension(utils.load_udf('udf_vito_save_to_public.py'),dimension='t',runtime="Python")\
#         .ndvi()\
#         .execute()


#        {"name": "SCENECLASSIFICATION_20M"}
    
    
#     #.apply_dimension(utils.load_udf('udf_vito_save_to_public.py'),dimension='t',runtime="Python")
#     mergedCollection=maskCollection.graph_add_process(
#         process_id='resample_cube_temporal',
#         args={
#             'data':   maskCollection.node_id,
#             'target': dataCollection.node_id,
#             'method': 'mean'
#         }
#     )
#     
#     
#     curves=mergedCollection\
#         .apply_dimension(utils.load_udf('udf_vito_save_to_public.py'),dimension='t',runtime="Python")\
#         .execute_batch("tmp/batchtest.json",job_options=job_options)
# 
# 
# 
# #    imgcoll=getImageCollection(eoconn, layerid, fieldgeom, startdate, enddate).execute_batch("tmp/batchtest.json",out_format='json')
# #     polys = shapely.geometry.GeometryCollection([shapely.geometry.shape(feature["geometry"]).buffer(0) for feature in fieldgeom["features"]])
# #     imgcoll=getImageCollection(eoconn, layerid, fieldgeom, startdate, enddate).polygonal_mean_timeseries(polys).execute_batch("tmp/batchtest.json",)
# # 
# #     ts_savgol = pandas.Series(imgcoll).apply(pandas.Series)
# #     ts_savgol.head(10)
#     #imgcoll=getImageCollection(eoconn, layerid, fieldgeom, startdate, enddate).download('tmp/test.tif', format="GTIFF")
#     
# #    curves=imgcoll.apply_dimension(load_udf('smooth_savitzky_golay.py'),process='',dimension='temporal').download('tmp/test')
    
    logger.info('FINISHED')






