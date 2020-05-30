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

openeo_url='http://openeo-dev.vgt.vito.be/openeo/0.4.0/'
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
layerID_data="S2_FAPAR_V102_WEBMERCATOR2"

job_options={
    'driver-memory':'4G',
    'executor-memory':'2G'
}

def getImageCollection(eoconn, layerid, fieldgeom, year, bands=None):
    startdate=str(year)+'-01-01'
    enddate=str(year+1)+'-03-31'
    polys = shapely.geometry.GeometryCollection([shapely.geometry.shape(feature["geometry"]).buffer(0) for feature in fieldgeom["features"]])
    bbox = polys.bounds
    return eoconn.load_collection(
        layerid,
        temporal_extent=[startdate, enddate],
        bands=bands
    ).filter_bbox(crs="EPSG:4326", **dict(zip(["west", "south", "east", "north"], bbox)))


if __name__ == '__main__':
    eoconn=openeo.connect(openeo_url)
    eoconn.authenticate_basic(openeo_user,openeo_pass)

    dataCollection=getImageCollection(eoconn, layerID_data, fieldgeom, year)\
        .apply_dimension(utils.load_udf('udf_smooth_savitzky_golay.py'),dimension='t',runtime="Python")\
        .apply_dimension(utils.load_udf('udf_phenology_optimized.py'),  dimension='t',runtime="Python")\
        .execute_batch("tmp/batchtest.json",job_options=job_options)

    logger.info('FINISHED')






