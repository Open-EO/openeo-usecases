import openeo
from pathlib import Path
# -------------------------------------
# The backend credentials:
DRIVER_URL = "https://openeo.vito.be/openeo/1.0/"
my_user = 'milutin'
my_pass = ''
# connect to the backend:
session = openeo.connect(DRIVER_URL).authenticate_basic(username=my_user, password=my_pass)
# -------------------------------------
#  upload WUR use case data manually (a collection of S1 tiff files) :
s1 = session.load_disk_collection('GTiff', str('/data/users/Public/driesj/openeo/WUR/with_srs/S1A_VH*.tif'), options={'date_regex': '.*S1A_VH_(\d{4})-(\d{2})-(\d{2}).tif'})
s1_cube = s1.filter_bbox(west=-6105178, east=-6097840, north=-388911, south=-396249, crs="EPSG:3857")
# -------------------------------------
#  functions to load the UDF code:
def get_resource(relative_path):
    return str(Path(relative_path))

def load_udf(relative_path):
    with open(get_resource(relative_path), 'r+') as f:
        return f.read()
# -------------------------------------
# load the UDF code:
BFASTMonitor_breaks = load_udf('BFAST_udf.py')

# apply the UDF:
S1_breaks = s1_cube.reduce_dimension(BFASTMonitor_breaks, runtime='Python')

# download the results:
S1_breaks.download('BFASTmonitor_breaks_vito_backend.nc', format='NetCDF')

