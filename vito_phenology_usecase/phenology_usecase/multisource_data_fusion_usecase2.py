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
from phenology_usecase.utils import UDFString
from shapely import affinity

#############################
# USER INPUT
#############################

openeo_user = os.environ.get('OPENEO_USER', 'wrong_user')
openeo_pass = os.environ.get('OPENEO_PASS', 'wrong_password')
openeo_model = os.environ.get('OPENEO_MODEL', 'wrong_model')

year = 2019

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
logging.basicConfig(level=logging.DEBUG)
logging.getLogger().setLevel(logging.DEBUG)

openeo_url = 'http://openeo-dev.vgt.vito.be/openeo/1.0.0/'
# openeo_url='https://openeo.vito.be/openeo/1.0.0/'

startdate=str(year-1)+'-10-01'
enddate=str(year+1)+'-07-01'
# startdate = str(year) + '-08-01'
# enddate = str(year) + '-08-10'

#job_options = {
#    'driver-memory': '32G',
#    'executor-memory': '32G',
#    'executor-memoryOverhead': '16G',
#    'driver-memoryOverhead': '16G'
#}
job_options = {
    'driver-memory': '20G',
    'executor-memory': '20G',
    'executor-memoryOverhead': '10G',
    'driver-memoryOverhead': '10G'
}

#############################
# CODE
#############################

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

    # find the extents, utm zone in epsg code for lat/lon of centroid and the bounding box polygon
    polys = shapely.geometry.GeometryCollection(
        [shapely.geometry.shape(feature["geometry"]).buffer(0) for feature in fieldgeom["features"]])
    polys = affinity.scale(polys, 64., 64.)
    epsgcode = epsg_code((polys.centroid.x, polys.centroid.y))
    extent = dict(zip(["west", "south", "east", "north"], polys.bounds))
    extent['crs'] = "EPSG:4326"
    bboxpoly=shapely.geometry.Polygon.from_bounds(*polys.bounds)

    # connection
    eoconn = openeo.connect(openeo_url)
    eoconn.authenticate_basic(openeo_user, openeo_pass)

    # prepare the Sentinel-2 bands via masking by the scene classification layer 
    s2_sceneclassification = eoconn.load_collection('TERRASCOPE_S2_TOC_V2', bands=['SCENECLASSIFICATION_20M']) \
        .band('SCENECLASSIFICATION_20M')
    S2mask = create_advanced_mask(s2_sceneclassification)
    S2bands = eoconn.load_collection('TERRASCOPE_S2_TOC_V2', bands=['TOC-B04_10M', 'TOC-B08_10M'])
    S2bands = S2bands.mask(S2mask)
    
    # compute NDVI for Sentinel2
    B4band = S2bands.band('TOC-B04_10M')
    B8band = S2bands.band('TOC-B08_10M')
    S2ndvi = (B8band-B4band)/(B8band+B4band)
    S2ndvi = S2ndvi.add_dimension("bands", "S2ndvi", type="bands")

    # prepare the Sentinel-1 bands
    S1bands = eoconn.load_collection('TERRASCOPE_S1_GAMMA0_V1', bands=['VH', 'VV'])
    S1bands = S1bands.resample_cube_spatial(S2ndvi)

    # merge S1 into S2
    merged_cube = S2ndvi
    merged_cube = merged_cube.merge(S1bands)

    # prepare the ProbaV ndvi band
    PVndvi = eoconn.load_collection('PROBAV_L3_S10_TOC_NDVI_333M', bands=['ndvi'])
    PVndvi = PVndvi.resample_cube_spatial(S2ndvi)
    PVndvi = PVndvi.mask_polygon(bboxpoly)

    # merge ProbaV into S2&S1
    merged_cube = merged_cube.merge(PVndvi)
    merged_cube = merged_cube.filter_temporal(startdate, enddate).filter_bbox(**extent)

    # run gan to compute a single NDVI
    gan_udf_code = UDFString('udf_gan.py').replace_option('prediction_model', '"'+openeo_model+'"').value
    ndvi_cube = merged_cube.apply_neighborhood(openeo.UDF(code=gan_udf_code, runtime="Python",data={'from_parameter': 'data'}), size=[
        {'dimension': 'x', 'value': 112, 'unit': 'px'},
        {'dimension': 'y', 'value': 112, 'unit': 'px'}
    ], overlap=[
        {'dimension': 'x', 'value': 8, 'unit': 'px'},
        {'dimension': 'y', 'value': 8, 'unit': 'px'}
    ])
    ndvi_cube=ndvi_cube.add_dimension("bands", "ndvi", type="bands").band("ndvi")

    # run phenology
    phenology_cube = ndvi_cube.apply_dimension(UDFString('udf_savitzkygolaysmooth_phenology.py').value, dimension='t',runtime="Python")

    # execute the process
    phenology_cube.save_user_defined_process("vito_phenology", public=True)
#    phenology_cube.execute_batch("vito_phenology.json",out_format='json', job_options=job_options)
#     phenology_cube.execute_batch("vito_phenology.nc",out_format='netcdf', job_options=job_options)
    phenology_cube.execute_batch("eos_sos.tif",out_format='GTiff', job_options=job_options, parameters={"tiled":True}) #{"tiled":True})#{"catalog":True})

    logger.info('FINISHED')
