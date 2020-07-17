'''
Created on May 14, 2020

@author: banyait
'''

import openeo
import logging
import shapely.geometry
import os
import numpy
import scipy.signal
from pathlib import Path

from openeo.rest.datacube import DataCube

from phenology_usecase import utils

#############################
# USER INPUT
#############################

openeo_user = os.environ.get('OPENEO_USER', 'wrong_user')
openeo_pass = os.environ.get('OPENEO_PASS', 'wrong_password')
openeo_model = os.environ.get('OPENEO_MODEL', 'wrong_model')

year = 2019
# fieldgeom = {
#     "type": "FeatureCollection",
#     "name": "small_field",
#     "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
#     "features": [
#         {"type": "Feature", "properties": {}, "geometry": {"type": "Polygon", "coordinates": [
#             [[5.0477606, 51.2138409], [5.0477606, 51.2225585], [5.0624407, 51.2225585], [5.0624407, 51.2138409],
#              [5.0477606, 51.2138409]]]}}
#     ]
# }
#         #        {"type":"Feature","properties":{},"geometry":{"type":"Polygon","coordinates":[[[5.074595,51.229408],[5.074950,51.212771],[5.099565,51.215100],[5.096555,51.229408],[5.074595,51.229408]]]}}

fieldgeom = {
    "type": "FeatureCollection",
    "name": "small_field",
    "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },
    "features": [
        { "type": "Feature", "properties": { }, "geometry": { "type": "Polygon", "coordinates": [ [ [ 5.008769, 51.218417 ], [ 5.008769, 51.227135 ], [ 5.023449, 51.227135 ], [ 5.023449, 51.218417 ], [ 5.008769, 51.218417 ] ] ] } }
    ]
}


#############################
# NON-USER CONFIG
#############################

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

openeo_url = 'http://openeo-dev.vgt.vito.be/openeo/1.0.0/'
# openeo_url='https://openeo.vito.be/openeo/1.0.0/'

startdate=str(year-1)+'-10-01'
enddate=str(year+1)+'-07-01'
# startdate = str(year) + '-08-01'
# enddate = str(year) + '-08-10'

job_options = {
    'driver-memory': '8G',
    'executor-memory': '8G',
    'driver-memoryOverhead': '8G',
    'executor-memoryOverhead': '8G'
}

#############################
# CODE
#############################


def get_resource(relative_path):
    return str(Path(relative_path))


def load_udf(relative_path):
    with open(get_resource(relative_path), 'r+') as f:
        return f.read()


def utm_zone(coordinates):
    if 56 <= coordinates[1] < 64 and 3 <= coordinates[0] < 12:
        return 32
    if 72 <= coordinates[1] < 84 and 0 <= coordinates[0] < 42:
        if coordinates[0] < 9:
            return 31
        elif coordinates[0] < 21:
            return 33
        elif coordinates[0] < 33:
            return 35
        return 37
    return int((coordinates[0] + 180) / 6) + 1


def epsg_code(coordinates):
    code = 32600 if coordinates[1] > 0. else 32700
    return int(code + utm_zone(coordinates))


def getImageCollection(eoconn, layer, fieldgeom, bands=None):
    polys = shapely.geometry.GeometryCollection(
        [shapely.geometry.shape(feature["geometry"]).buffer(0) for feature in fieldgeom["features"]])
    bbox = polys.bounds
    extent = dict(zip(["west", "south", "east", "north"], bbox))
    return eoconn.load_collection(
        layer,
        temporal_extent=[startdate, enddate],
        spatial_extent=extent,
        bands=bands
    )


def makekernel(size: int) -> numpy.ndarray:
    assert size % 2 == 1
    kernel_vect = scipy.signal.windows.gaussian(size, std=size / 3.0, sym=True)
    kernel = numpy.outer(kernel_vect, kernel_vect)
    kernel = kernel / kernel.sum()
    return kernel


def create_advanced_mask(band, band_math_workaround=True):
    # in openEO, 1 means mask (remove pixel) 0 means keep pixel
    classification = band

    # keep useful pixels, so set to 1 (remove) if smaller than threshold
    first_mask = ~ ((classification == 4) | (classification == 5) | (classification == 6) | (classification == 7))
    first_mask = first_mask.apply_kernel(makekernel(17))
    # remove pixels smaller than threshold, so pixels with a lot of neighbouring good pixels are retained?
    if band_math_workaround:
        first_mask = first_mask.add_dimension("bands", "mask", type="bands").band("mask")
    first_mask = first_mask > 0.057

    # remove cloud pixels so set to 1 (remove) if larger than threshold
    second_mask = (classification == 3) | (classification == 8) | (classification == 9) | (classification == 10)
    second_mask = second_mask.apply_kernel(makekernel(161))
    if band_math_workaround:
        second_mask = second_mask.add_dimension("bands", "mask", type="bands").band("mask")
    second_mask = second_mask > 0.1

    # TODO: the use of filter_temporal is a trick to make cube merging work, needs to be fixed in openeo client
    return first_mask.filter_temporal(startdate, enddate) | second_mask.filter_temporal(startdate, enddate)
    # return first_mask | second_mask
    # return first_mask


if __name__ == '__main__':
    # find the utm zone in epsg code for lat/lon of centroid
    geo = shapely.geometry.GeometryCollection(
        [shapely.geometry.shape(feature["geometry"]).buffer(0) for feature in fieldgeom["features"]])
    epsgcode = epsg_code((geo.centroid.x, geo.centroid.y))

    polys = shapely.geometry.GeometryCollection(
        [shapely.geometry.shape(feature["geometry"]).buffer(0) for feature in fieldgeom["features"]])
    bbox = polys.bounds
    extent = dict(zip(["west", "south", "east", "north"], bbox))
    extent['crs'] = "EPSG:4326"

    # connection
    eoconn = openeo.connect(openeo_url)
    eoconn.authenticate_basic(openeo_user, openeo_pass)

    s2_sceneclassification = eoconn.load_collection('TERRASCOPE_S2_TOC_V2', bands=['SCENECLASSIFICATION_20M']) \
        .band('SCENECLASSIFICATION_20M')
    # prepare the Sentinel-2 bands
    S2mask = create_advanced_mask(s2_sceneclassification)

    S2bands = eoconn.load_collection('TERRASCOPE_S2_TOC_V2', bands=['TOC-B04_10M', 'TOC-B08_10M'])
    S2bands = S2bands.mask(S2mask)

#     try: 
#         S2bands.filter_temporal(startdate, enddate).filter_bbox(**extent).execute_batch("S2bands.json",out_format='json', job_options=job_options, tiled=True)
#         logger.info("********** S2 BANDS ************")
#     except: pass

    # prepare the Sentinel-1 bands
    S1bands = eoconn.load_collection('TERRASCOPE_S1_GAMMA0_V1', bands=['VH', 'VV'])
    S1bands = S1bands.resample_cube_spatial(S2bands)

#     try: 
#         S1bands.filter_temporal(startdate, enddate).filter_bbox(**extent).execute_batch("S1bands.json",out_format='json', job_options=job_options, tiled=True)
#         logger.info("********** S1 BANDS ************")
#     except: pass

    # merge S1 into S2
    cube = S2bands
    cube = cube.merge(S1bands)

    # prepare the ProbaV ndvi band
    PVndvi = eoconn.load_collection('PROBAV_L3_S10_TOC_NDVI_333M', bands=['ndvi'])
    PVndvi:DataCube = PVndvi.resample_cube_spatial(S2bands)
    PVndvi = PVndvi.mask_polygon(polys.geoms[0])
    #PVndvi.filter_temporal('2019-08-01', '2019-08-01').filter_bbox(**extent).download("probavS2Resolution.tif")

#     try: 
#         PVndvi.filter_temporal(startdate, enddate).filter_bbox(**extent).execute_batch("PVbands.json",out_format='json', job_options=job_options, tiled=True)
#         logger.info("********** PV BANDS ************")
#     except: pass

    # merge ProbaV into S2&S1
    cube = cube.merge(PVndvi)
    cube = cube.filter_temporal(startdate, enddate).filter_bbox(**extent)

#     try: 
#         cube.execute_batch("pre_gan.json",out_format='json', job_options=job_options, tiled=True)
#         logger.info("********** PRE GAN ************")
#     except: pass


    # run gan to compute a single NDVI
    gan_udf_code = load_udf('udf_gan.py').replace('prediction_model=""', 'prediction_model="' + openeo_model + '"')
    ndvi_cube = cube.apply_neighborhood(openeo.UDF(code=gan_udf_code, runtime="Python",data={'from_parameter': 'data'}), size=[
        {'dimension': 'x', 'value': 112, 'unit': 'px'},
        {'dimension': 'y', 'value': 112, 'unit': 'px'}
    ], overlap=[
        {'dimension': 'x', 'value': 8, 'unit': 'px'},
        {'dimension': 'y', 'value': 8, 'unit': 'px'}
    ])

#     try: 
#         ndvi_cube.execute_batch("pre_pheno.json",out_format='json', job_options=job_options, tiled=True)
#         logger.info("********** PRE PHENO ************")
#     except: pass

    # run phenology
    smoothed_cube =  ndvi_cube.apply_dimension(utils.load_udf('udf_smooth_savitzky_golay.py'), dimension='t',runtime="Python")
    phenology_cube = smoothed_cube.apply_dimension(utils.load_udf('udf_phenology_optimized.py'), dimension='t',runtime="Python")

    phenology_cube.save_user_defined_process("vito_phenology", public=True)

    phenology_cube.execute_batch("eos_sos.tif",out_format='GTiff', job_options=job_options)#, parameters={"catalog":True}

#     try: 
#         phenology_cube.execute_batch("finished.json",out_format='json', job_options=job_options, tiled=True)
#         logger.info("********** FINISHED ************")
#     except: pass

    #S2bands.filter_temporal(startdate, enddate).filter_bbox(**extent).download('S2bands.json', format='json')
    # S1bands.filter_temporal(startdate,enddate).filter_bbox(**extent).download('S1bands.json',format='json')
    # PVndvi.filter_temporal(startdate,enddate).filter_bbox(**extent).download('PVbands.json',format='json')
    # ndvi_cube.filter_temporal(startdate,enddate).filter_bbox(**extent).execute_batch("gan.tif",job_options=job_options,tiled=True)
    logger.info('FINISHED')
