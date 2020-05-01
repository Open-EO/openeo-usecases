import os
import sys
import xarray as xr
import pandas as pd
#
sys.path.append('/home/milutin/rStudioProjects/final-user-workshop/WUR_BFAST_UseCase/Python/')
from BFAST_udf import bfast4openeo

# set the working dir:
os.chdir('/home/milutin/rStudioProjects/final-user-workshop/WUR_BFAST_UseCase/Python/')

# read the multi-band raster
da = xr.open_rasterio('s1_vh_2017_2019_aoi.tif')\
    .rename({'band': 'time'})

# deal with the band 9:
da[8,:,:] = da[7,:,:]


# assign the time stamps:
da.coords['time'] = pd.date_range(start='1/1/2017', end='29/12/2019', freq='12D')

# test the  bfast4openeo function:
breaks = bfast4openeo(da)


# run the "BFAST_udf.py" script "offline":
# import sys
# import subprocess
# subprocess.call([sys.executable, 'BFAST_udf.py', da])






