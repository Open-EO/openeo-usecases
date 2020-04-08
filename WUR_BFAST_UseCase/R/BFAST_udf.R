# @require x:stars
library(bfast)
# set_fast_options()

# Define the pixel-wise function
SpatialBFM = function(pixels)
{
  lsts = ts(pixels, c(2017, 1), frequency=40)
  bfastmonitor(lsts, 2019, formula=response~trend)$breakpoint
}
StarsResult = st_apply(x, c("x", "y"), SpatialBFM, PROGRESS=TRUE)
StarsResult