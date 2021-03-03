# @require x:stars
library(bfast)
library(abind)
library(mmand)
library(raster)
# set_fast_options()
# this works because band is a empty dimension
x = adrop(x)

# Define the pixel-wise function
SpatialBFM = function(pixels)
{
  lsts = ts(pixels, c(2017, 1), frequency=30.666667)
  bfastmonitor(lsts, 2019, formula=response~trend)$breakpoint
}
# either use adrop() to drop the band dimension... or include here to reduce.
#StarsResult = st_apply(x, c("x", "y", "band"), SpatialBFM, PROGRESS=TRUE)
StarsResult = st_apply(x, c("x", "y"), SpatialBFM, PROGRESS=TRUE)
# deal with NA-a:
#StarsResult[is.na(StarsResult)] = -9999
#
StarsResult

# convert to raster:
raster_out <- as(StarsResult, "Raster")

# convert to bw ratser:
raster_out_bw <- raster_out
raster_out_bw[is.na(raster_out[])] <- 0
raster_out_bw[!is.na(raster_out[])] = 1

# filter out small pixel clusters using the morphological opening: 
my_kernel = shapeKernel(c(9,9), type = "box", binary = TRUE, normalised = False)
raster_out_bw_filt_mat <- opening(as.matrix(raster_out_bw), my_kernel)
# assign the filtered values to new raster
raster_out_bw_filt = raster_out
values(raster_out_bw_filt) = raster_out_bw_filt_mat

# multiply the original output with the bw mask and save locally:
raster_out_filt = raster_out*raster_out_bw_filt
# the final output raster:
raster_out_filt




