import openeo
from pathlib import Path
# -------------------------------------
# The backend credentials:
from openeo.rest.datacube import DataCube

DRIVER_URL = "https://openeo-dev.vito.be"
my_user = 'milutin'
my_pass = ''
# connect to the backend:
session = openeo.connect(DRIVER_URL).authenticate_basic(username=my_user, password=my_pass)

s1 = session.load_collection("SENTINEL1_GAMMA0_SENTINELHUB",bands=["VH"])
s1_cube: DataCube = s1.filter_bbox(west=-54.8125,south=-3.5125,east=-54.8100,north=-3.5100)\
    .filter_temporal("2019-05-01", "2019-12-29")

fieldgeom = {
    "type": "FeatureCollection",
    "name": "small_field",
    "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
    "features": [
        {"type": "Feature", "properties": {}, "geometry": {"type": "Polygon", "coordinates": [
            [[5.008769, 51.218417], [5.008769, 51.227135], [5.023449, 51.227135], [5.023449, 51.218417],
             [5.008769, 51.218417]]]}}
    ]
}
import shapely
from shapely import affinity

polys = shapely.geometry.GeometryCollection(
    [shapely.geometry.shape(feature["geometry"]).buffer(0) for feature in fieldgeom["features"]])
polys = affinity.scale(polys, 1., 1.)
extent = dict(zip(["west", "south", "east", "north"], polys.bounds))
extent['crs'] = "EPSG:4326"

s1_belgium = session.load_collection("S1_GRD_SIGMA0_ASCENDING",spatial_extent=extent,temporal_extent=["2017-05-01", "2019-12-29"], bands=["VH"])

# -------------------------------------
#  functions to load the UDF code:
def get_resource(relative_path):
    return str(Path(relative_path))

def load_udf(relative_path):
    with open(get_resource(relative_path), 'r+') as f:
        return f.read()

def test_download_cube():
    #s1_cube.download("gamma0.tif")
    s1_cube.download("gamma0_cube.nc",format="NetCDF")

def test_download_terrascope():
    """
    Downloads a test netcdf file over a region available in Terrascope. This test dataset will allow us to test the udf basics.
    We do this simply because at time of writing, generating a test dataset in terrascope is better tested, faster and cheaper.

    @return:
    """

    s1_belgium.download("sigma0_cube_terrascope.nc",format="NetCDF")

def test_run_udf_offline():
    from openeo.rest.conversions import datacube_from_file
    udf_cube = datacube_from_file('sigma0_cube_terrascope.nc', fmt='netcdf')
    from BFAST_udf import apply_datacube
    apply_datacube(udf_cube,context={})


def test_run_udf_terrascope():

    # -------------------------------------
    # load the UDF code:
    BFASTMonitor_breaks = load_udf('BFAST_udf.py')

    # apply the UDF:
    S1_breaks = s1_belgium.reduce_temporal_udf(code=BFASTMonitor_breaks, runtime='Python')

    # download the results:
    #print(S1_breaks.to_json())
    S1_breaks.download('BFASTmonitor_breaks_vito_backend.nc', format='NetCDF')
