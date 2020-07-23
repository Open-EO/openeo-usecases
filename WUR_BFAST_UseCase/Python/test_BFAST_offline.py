import os
import sys
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import cm
from datetime import datetime
import numpy as np
#
sys.path.append('/home/milutin/rStudioProjects/final-user-workshop/WUR_BFAST_UseCase/Python/')
from BFAST_udf import bfast4openeo

# set the working dir:
os.chdir('/home/milutin/rStudioProjects/final-user-workshop/WUR_BFAST_UseCase/Python/')

# read the multi-band raster
da = xr.open_rasterio('s1_vh_2017_2019_aoi_noNaN.tif')\
    .rename({'band': 'time'})

# deal with the band 9:
# da[8, :, :] = da[7, :, :]


# assign the time stamps:
da.coords['time'] = pd.date_range(start='1/1/2017', end='29/12/2019', freq='12D')

# test the  bfast4openeo function:
breaks = bfast4openeo(da)

# plot ther result:
plt.imshow(breaks.values)
# save the result:
breaks.to_netcdf('offline_bfastPy_output.nc')
# load the results:
breaks = xr.open_dataarray('offline_bfastPy_output.nc')

breaks = breaks.sortby('x')
breaks = breaks.sortby('y')

aoi = breaks.sel(y=slice(9611198, 9611750), x=slice(742740, 743297))
aoi.plot()
# ------------
start_monitor = datetime(2019, 1, 1)
end_monitor = datetime(2019, 12, 31)
# get dates from monitoring period:
dates = pd.date_range(start='1/1/2017', end='29/12/2019', freq='12D')
dates_mon = dates[dates.slice_indexer(start_monitor, end_monitor)]
# convert to the fraction of the year:
frac_of_year = np.array(dates_mon.year + dates_mon.dayofyear / 365.)
# convert aoi values to the fraction of the year:
aoi = aoi.where(aoi != -1, np.nan)

my_unique = np.unique(aoi.where(aoi > 0, -1).values)

for oldValue in my_unique[1:]:
    aoi = aoi.where(aoi != oldValue, frac_of_year[np.int(oldValue)])

cmap1 = cm.get_cmap('inferno', 12)
aoi.plot(cmap=cmap1, vmin=2019, vmax=2019.9999)











