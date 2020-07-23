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

eurac = connect(host = euracHost, version="0.4.2", user = user, password = password, login_type = "basic")
#eurac = connect(host = euracHost)

# Build a process graph:
p = processes()

# the spatial and temporal exstends should be adopted:
# s1 = p$load_collection(id = p$data$openEO_WUR_UseCase_NoNaNs,
#                        spatial_extent = list(west = -54.815,
#                                              south = -3.515,
#                                              east =  -54.810,
#                                              north = -3.510),
#                        # add band selection here
#                        temporal_extent = c("2017-01-01T00:00:00Z","2019-12-29T00:00:00Z"),
#                        # select the vh band:
#                        bands = c('VH'))

9611198
742740
9611750
743297



s1 = p$load_collection(id = p$data$openEO_WUR_UseCase_NoNaNs,
                       spatial_extent = list(west = -54.88778740,
                                             south = -3.59408239,
                                             east =  -54.70898726,
                                             north = -3.42179801),
                       # add band selection here
                       temporal_extent = c("2017-01-01T00:00:00Z","2019-12-29T00:00:00Z"),
                       # select the vh band:
                       bands = c('VH'))



# download the input data for the udf (this is just to test the off-line and on-line results):
# job_id = create_job(con = eurac, graph = s1, title = "job2_wur_udf_data", description = "job2_wur_udf_data") # 
# start_job(con = eurac, job = job_id)
# doneData = download_results(job = job_id, folder = ".")


list_udf_runtimes(eurac)
describe_process(con = eurac,"load_collection")

# check the WUR test data at EURAC backend:
list_collections()
collection_viewer("openEO_WUR_UseCase_NoNaNs")
describe_collection(id="openEO_WUR_UseCase_NoNaNs")

# note: please take care of the working directory of your R sesion
udfName = "BFAST_udf.R"
udfCode = readChar(udfName, file.info(udfName)$size)

# send_udf(s1, udfCode, host = "", port = NULL, language = "R", debug = FALSE, download_info = FALSE)

test1 = p$run_udf(data = s1, udf = udfCode, runtime = "R")
graph_test1 = p$save_result(test1, format="GTiff")
# compute_result(graph=graph_test1, format="GTiff", output_file = 'euracBackend_bfast_output_noNAs.tif')


#done = compute_result(graph=result, format="NETCDF", output_file = 'test_udf.ncdf') # this is a synchronous call, not working on udf!
job_id = create_job(con = eurac, graph = graph_test1, title = "job1_wur_udf_rclient_byWUR", description = "job1_wur_udf_rclient_byWUR") # batch call, works on udf!
start_job(con = eurac, job = job_id)
done = download_results(job = job_id, folder = ".")

# load the result and plot:
print(done)
library(sp)
library(raster)
outRast = raster(unlist(done))
# deal with the NaN values
outRast[outRast==-9999] = NA
# plotting
plot(outRast)
# chek metadata
print(outRast)






# compare with the local run output:
onLineRaster = raster("67117f0c-52a5-4be3-ab97-1fcd83bd195a.tiff")
# offLineRaster = raster("offline_bfast_output_v2.tif")
offLineRaster = raster("offline_bfast_output_largeArea.tif")
print(offLineRaster)
print(onLineRaster)

# plloting both outputs
library(viridisLite)
library(viridis) 
par(mfrow=c(1,2))
plot(offLineRaster, 
     xlim = c(onLineRaster@extent@xmin, onLineRaster@extent@xmax), 
     ylim = c(onLineRaster@extent@ymin, onLineRaster@extent@ymax),
     col=inferno(12), zlim=c(2019,2020))
#
plot(onLineRaster,
     col=inferno(12), zlim=c(2019,2020))


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


