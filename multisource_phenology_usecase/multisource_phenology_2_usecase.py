'''
Created on May 14, 2020

@author: banyait
'''

import openeo
import logging
import shapely.geometry
import os
import utils
import numpy
import scipy.signal

#############################
# USER INPUT
#############################

openeo_user=os.environ.get('OPENEO_USER','wrong_user')
openeo_pass=os.environ.get('OPENEO_PASS','wrong_password')
year=2019
fieldgeom={
    "type":"FeatureCollection",
    "name":"small_field",
    "crs":{"type":"name","properties":{"name":"urn:ogc:def:crs:OGC:1.3:CRS84"}},
    "features":[
        {"type":"Feature","properties":{},"geometry":{"type":"Polygon","coordinates":[[[5.497022,51.130558],[5.498517,51.130266],[5.498855,51.129749],[5.496834,51.130137],[5.497022,51.130558]]]}}
    ]
}

#############################
# CODE
#############################

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

openeo_url='http://openeo-dev.vgt.vito.be/openeo/1.0.0/'
#openeo_url='http://openeo.vgt.vito.be/openeo/1.0.0/'

layerID="TERRASCOPE_S2_TOC_V2"
startdate=str(year)+'-01-01'
enddate=str(year+1)+'-03-31'
# startdate=str(year)+'-01-01'
# enddate=str(year)+'-01-10'


job_options={
    'driver-memory':'4G',
    'executor-memory':'4G'
}

def getImageCollection(eoconn, layer, fieldgeom, bands):
    polys = shapely.geometry.GeometryCollection([shapely.geometry.shape(feature["geometry"]).buffer(0) for feature in fieldgeom["features"]])
    bbox = polys.bounds
    return eoconn.load_collection(
        layer,
        temporal_extent=[startdate, enddate],
        bands=bands
    ).filter_bbox(crs="EPSG:4326", **dict(zip(["west", "south", "east", "north"], bbox)))


def makekernel(size: int) -> numpy.ndarray:
    assert size % 2 == 1
    kernel_vect = scipy.signal.windows.gaussian(size, std=size / 3.0, sym=True)
    kernel = numpy.outer(kernel_vect, kernel_vect)
    kernel = kernel / kernel.sum()
    return kernel

def create_advanced_mask(band, band_math_workaround=True):
    # in openEO, 1 means mask (remove pixel) 0 means keep pixel
    classification=band
    
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

    # connection
    eoconn=openeo.connect(openeo_url)
    eoconn.authenticate_basic(openeo_user,openeo_pass)
    
    # compute the mask
    maskband=create_advanced_mask(getImageCollection(eoconn, layerID, fieldgeom, ["SCENECLASSIFICATION_20M"]).band("SCENECLASSIFICATION_20M"))
    maskband=maskband.apply_dimension(utils.load_udf('udf_save_to_file.py'),dimension='t',runtime="Python")

    # compute evi using band math
    brnbands=getImageCollection(eoconn, layerID, fieldgeom, ["TOC-B02_10M","TOC-B04_10M","TOC-B08_10M"])
    b2band=brnbands.band("TOC-B02_10M")
    b4band=brnbands.band("TOC-B04_10M")
    b8band=brnbands.band("TOC-B08_10M")
    # why is the 10000?
    eviband= (2.5 * (b8band - b4band)) / ((b8band + 6.0 * b4band - 7.5 * b2band) + 10000.0*1.0)
    # eviband= (2.5 * (b8band - b4band)) / ((b8band + 6.0 * b4band - 7.5 * b2band) + 1.0)
    eviband=eviband.apply_dimension(utils.load_udf('udf_save_to_file.py'),dimension='t',runtime="Python")

    # set NaN where mask is active
    eviband=eviband.mask(maskband)
    eviband=eviband.apply_dimension(utils.load_udf('udf_save_to_file.py'),dimension='t',runtime="Python")

    # run the smoother
    eviband=eviband.apply_dimension(utils.load_udf('udf_smooth_savitzky_golay.py'),dimension='t',runtime="Python")
    eviband=eviband.apply_dimension(utils.load_udf('udf_save_to_file.py'),dimension='t',runtime="Python")
    
    # run phenology
    eviband=eviband.apply_dimension(utils.load_udf('udf_phenology_optimized.py'),  dimension='t',runtime="Python")
    eviband=eviband.apply_dimension(utils.load_udf('udf_save_to_file.py'),dimension='t',runtime="Python")

    eviband.execute_batch("phenology.gtiff",job_options=job_options)
    

    logger.info('FINISHED')






