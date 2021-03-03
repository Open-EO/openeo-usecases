library(stars)
#
#x = read_stars("s1_vh_2017_2019_aoi.tif", RasterIO=list(nBufXSize=225, nBufYSize=214, nXSize=20, nYSize=20))
#x = read_stars("s1_vh_2017_2019_aoi_noNaN.tif")
x = read_stars("openEO_BFAST_test_S1_VH_2017_2019_da_allData_noNaNs.tif")
source("BFAST_udf.R")
#
StarsResult# @require x:stars

# deal with the NaN values
#StarsResult[StarsResult==-9999] = NA
#
#plot(StarsResult)
# write_stars(StarsResult, "offline_bfast_output_v2.tif")
#write_stars(StarsResult, "offline_bfast_output_largeArea.tif")

# save the output
writeRaster(raster_out_filt, "offline_bfast_output_largeArea_filt_v2", format = "GTiff")

