import os
import xarray as xr
import pandas as pd



# set the working dir:
os.chdir('/home/milutin/rStudioProjects/final-user-workshop/WUR_BFAST_UseCase/Python/')

# read the multi-band raster
da = xr.open_rasterio('s1_vh_2017_2019_aoi.tif')\
    .rename({'band': 'time'})

# assign the time Astamps:
da.coords['time'] = pd.date_range(start='1/1/2017', end='29/12/2019', freq='12D')








