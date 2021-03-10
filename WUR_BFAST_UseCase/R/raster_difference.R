library(sp)
library(raster)
library(rgdal)
#
library(mmand)
#
library(viridisLite)
library(viridis)
library(rasterVis)
library(RColorBrewer)
library(fields)
#
library(raster)
library(ggplot2)
library(reshape2)
library(RStoolbox)
#
onLineRaster = raster("data.tiff")
onLineRaster[onLineRaster==-9999] = NA
#
offLineRaster = raster("offline_bfast_output_largeArea.tif")
offLineRaster <- crop(offLineRaster, onLineRaster@extent)
# plot:
par(mfrow=c(1,2))
plot(onLineRaster, col=inferno(12), zlim=c(2019,2020))
plot(offLineRaster, col=inferno(12), zlim=c(2019,2020))
#
# ----------------------------------
# calculate the difference raster:
diff = onLineRaster - offLineRaster
offLineRaster@data@values - onLineRaster@data@values


offLineRaster3 = shift(offLineRaster, dx=10, dy=10)

diff = onLineRaster - offLineRaster3
diff = diff*365*24*60
minValue(diff)
maxValue(diff)

# plot:
pal <- brewer.pal(n=11, name = "RdYlGn")
#pal <- brewer.pal(n=11, name = "Spectral")

par(mfrow=c(1,2))
plot(onLineRaster, col=inferno(12), zlim=c(2019,2020))
plot(diff, col=pal, zlim=c(minValue(diff),maxValue(diff)), legend = FALSE)

plot(diff, col=pal, zlim=c(-50,50),legend = FALSE)
#
def_breaks = c(round(minValue(diff),2),-20,0,20,round(maxValue(diff),2))
my_breaks = c(round(minValue(diff),2),-20,0,20,round(maxValue(diff),2))
#
image.plot(diff, zlim = c(minValue(diff),maxValue(diff)), 
           legend.only = TRUE, 
           col = pal,
           axis.args = list(at = def_breaks, labels = my_breaks))


