# @require x:stars
library(bfast)
library(abind)
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
StarsResult