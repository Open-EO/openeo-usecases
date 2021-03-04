if (!require(devtools)) {
  install.packages("devtools",dependencies=TRUE)
  library(devtools)
}
install.packages("remotes")

remotes::install_github(repo="Open-EO/openeo-r-client@develop",dependencies=TRUE)


library(openeo)



# enter valid credentials
euracHost = "https://openeo.eurac.edu"
#
user = ""
password = ""

api_versions(url=euracHost)


eurac = connect(host = euracHost, user = user, password = password, login_type = "basic")

#eurac = connect(host = euracHost, version="1.0.0", user = user, password = password, login_type = "basic")
# eurac = connect(host = euracHost)
# 
# # the spatial and temporal exstends should be adopted:
# 
# 9611198
# 742740
# 9611750
# 743297
# 
# 
# s1 = p$load_collection(id = p$data$openEO_WUR_Usecase,
#                        spatial_extent = list(west = -54.88778740,
#                                              south = -3.59408239,
#                                              east =  -54.70898726,
#                                              north = -3.42179801),
#                        # add band selection here
#                        temporal_extent = c("2017-01-01T00:00:00Z","2019-12-29T00:00:00Z"),
#                        # select the vh band:
#                        bands = c('VH'))


# Build a process graph:
p = processes()

s1 = p$load_collection(id = "openEO_WUR_Usecase",
                       spatial_extent = list(west = -54.815,
                                             south = -3.515,
                                             east =  -54.810,
                                             north = -3.510),
                       # add band selection here
                       temporal_extent = c("2017-01-01T00:00:00Z","2019-12-29T00:00:00Z"),
                       # select the vh band:
                       bands = c('VH'))


# note: please take care of the working directory of your R session
udfName = "BFAST_udf.R"
udfCode = readChar(udfName, file.info(udfName)$size)

# ingest udf into the process graph
test1 = p$run_udf(data = s1, udf = udfCode, runtime = "R")
# save results
graph_test1 = p$save_result(test1, format="GTiff")



# create a bach job from the graph:
job_id = create_job(con = eurac, graph = graph_test1, title = "job_final_review_demo", description = "job_final_review_demo") # batch call, works on udf!
# get the JSON text of the process graph:
graph_info = create_user_process( graph_test1,id=job_id$id, submit = FALSE, con = eurac )
graph_json = jsonlite::toJSON(graph_info$process_graph)
print(graph_json)
# start the job:
start_job(con = eurac, job = job_id)
done = download_results(job = job_id, folder = ".")


# --------------------
# some helpful calls
list_udf_runtimes(eurac)
describe_process(con = eurac,"load_collection")

# check the WUR test data at EURAC backend:
list_collections()
collection_viewer("openEO_WUR_Usecase")

# compute_result(graph=graph_test1, format="GTiff", output_file = 'euracBackend_bfast_output_noNAs.tif')
#done = compute_result(graph=result, format="NETCDF", output_file = 'test_udf.ncdf') # this is a synchronous call, not working on udf!
# --------------------


# -------------------------------------------------------------------
# the code below is for cheeking local and eurac output from bfast:
# -------------------------------------------------------------------
# load the result and plot:
print(done)
library(sp)
library(raster)
library(rgdal)
outRast = raster(unlist(done)[1])
# deal with the NaN values
outRast[outRast==-9999] = NA
# plotting
plot(outRast)
# chek metadata
print(outRast)


# compare with the local run output:
#onLineRaster = raster("67117f0c-52a5-4be3-ab97-1fcd83bd195a.tiff")
#onLineRaster = raster("c591e025-3022-4e84-959d-22bdbabf23df.tiff")
onLineRaster = raster("data.tiff")
onLineRaster[onLineRaster==-9999] = NA
#offLineRaster = raster("offline_bfast_output_v2.tif")
offLineRaster = raster("offline_bfast_output_largeArea.tif")

# convert to bw ratser:
offLineRaster_bw = offLineRaster
offLineRaster_bw[is.na(offLineRaster[])] <- 0
offLineRaster_bw[!is.na(offLineRaster[])] = 1

plot(offLineRaster_bw)
plot(offLineRaster, col=inferno(12), zlim=c(2019,2020))


library(mmand)
kernel1 = shapeKernel(c(9,9), type = "box", binary = TRUE, normalised = False)
offLineRaster_bw_filt_mat <- opening(as.matrix(offLineRaster_bw), kernel1)
offLineRaster_bw_filt = offLineRaster
values(offLineRaster_bw_filt) = offLineRaster_bw_filt_mat

# plot the orig. bw and filtered:
par(mfrow=c(1,2))
plot(offLineRaster_bw)
plot(offLineRaster_bw_filt)

# multiply the original with the bw mask and save locally:
offLineRaster_filt = offLineRaster*offLineRaster_bw_filt
writeRaster(offLineRaster_filt, "offline_bfast_output_largeArea_filt", format = "GTiff")

# plot the orig. and filtered:
par(mfrow=c(1,2))
plot(offLineRaster, col=inferno(12), zlim=c(2019,2020))
plot(offLineRaster_filt, col=inferno(12), zlim=c(2019,2020))

# 





# crop raster:
# use row and column numbers:
offLineRaster2 <- crop(offLineRaster, onLineRaster@extent)



library(viridisLite)
library(viridis) 
par(mfrow=c(1,2))
plot(onLineRaster,
     col=inferno(12), zlim=c(2019,2020))
plot(offLineRaster2,
     col=inferno(12), zlim=c(2019,2020))




# ---------------------------------------------------------------
# some extra code to play around with the visualization
# ---------------------------------------------------------------
print(offLineRaster3)
print(onLineRaster)

plot(offLineRaster2)


library(raster)
library(ggplot2)
library(reshape2)
library(RStoolbox)
p = ggR(onLineRaster, sat = 1, alpha = .5) 
p + ggR(offLineRaster3, sat = 1, hue = .5, alpha = 0.5, ggLayer=TRUE) 

# plloting both outputs
library(viridisLite)
library(viridis) 
par(mfrow=c(1,2))
plot(offLineRaster3, 
     xlim = c(onLineRaster@extent@xmin, onLineRaster@extent@xmax), 
     ylim = c(onLineRaster@extent@ymin, onLineRaster@extent@ymax),
     col=inferno(12), zlim=c(2019,2020))
#




# compare the with the data downloaded from the backend:
euracInput = raster(unlist(doneData))
# deal with the NaN values
euracInput[euracInput==-9999] = NA
# read locan input data:
offLineInput = raster("s1_vh_2017_2019_aoi_noNaN.tif")
offLineInput[offLineInput==-9999] = NA


# plot
par(mfrow=c(1,2))
plot(offLineInput, 
     xlim = c(euracInput@extent@xmin, euracInput@extent@xmax), 
     ylim = c(euracInput@extent@ymin, euracInput@extent@ymax),
     col=inferno(12), zlim=c(2019,2020))
#
plot(euracInput,
     col=inferno(12), zlim=c(2019,2020))


