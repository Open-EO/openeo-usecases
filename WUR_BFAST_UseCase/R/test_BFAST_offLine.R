library(stars)
install.packages("pbapply")

x = read_stars("s1_vh_2017_2019_da_aoi.tif", RasterIO=list(nBufXSize=225, nBufYSize=214, nXSize=20, nYSize=20))
source("BFAST_udf.R")

StarsResult

plot(StarsResult)

write_stars(StarsResult, "offline_bfast_output.tif")
