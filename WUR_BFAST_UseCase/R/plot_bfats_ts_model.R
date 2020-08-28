library(stars)
library(raster)
library(bfast)
#
#x_brick = brick("s1_vh_2017_2019_aoi.tif")
x_brick = brick("openEO_BFAST_test_S1_VH_2017_2019_da_allData_noNaNs.tif")
#
#out_raster = raster("offline_bfast_output_v2.tif")
out_raster = raster("offline_bfast_output_largeArea.tif")

plot(out_raster)
df1 = click()
#
ts1 = c(extract(x_brick, df1))
lsts = ts(ts1, c(2017, 1), frequency=30.666667)
plot(lsts)
#
model1 = bfastmonitor(lsts, 2018, formula=response~trend+harmon, order= 1, history="all")
plot(model1)


