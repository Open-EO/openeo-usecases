# @require x:stars
library(bfast)
# set_fast_options()

# Define the pixel-wise function
SpatialBFM = function(pixels)
{
  lsts = ts(pixels, c(1981, 7), frequency=24)
  bfastmonitor(lsts, 2010)$breakpoint
}
StarsResult = st_apply(x, c("x", "y"), SpatialBFM, PROGRESS=TRUE)
StarsResult