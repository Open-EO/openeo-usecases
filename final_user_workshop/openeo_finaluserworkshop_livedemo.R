# openEO r-client - live demonstration and guided tour
# 2020-10-19
# Dainius Masilianus, Peter Zellner, Florian Lahn

# ---------------------------------------------------------------------------- #
# Preparation -----
# ---------------------------------------------------------------------------- #


# information on the openEO r-client 
# - openEO final user workshop code: https://github.com/Open-EO/openeo-usecases/final_user_workshop/

# - github main: https://github.com/Open-EO/openeo-r-client/
# - getting started guide (openeo webpage): https://openeo.org/documentation/1.0/r
# - getting started guide (github): https://github.com/Open-EO/openeo-r-client/blob/master/examples/getting_started.Rmd
# - more examples: https://github.com/Open-EO/openeo-r-client/tree/master/examples
# - openEO use cases (some are using the r-client): https://github.com/Open-EO/openeo-usecases/

# list of available backends
# https://hub.openeo.org

# install 
remotes::install_github(repo="Open-EO/openeo-r-client", dependencies=TRUE)
packageVersion("openeo")

# libs 
library(openeo)

library(stars)
library(sf)
library(mapview)
library(dplyr)
library(jsonlite)

# ---------------------------------------------------------------------------- #
# Backend Discovery ----
# ---------------------------------------------------------------------------- #

# discover vito backend --------------------------------------------------------

# connect to VITO backend 
user = "user"
pw = "user123"
host = "https://openeo.vito.be"
con = connect(host = host, 
              user = user, 
              password = pw)

# note that in the upper right box "Connections" is populated with the availalble
# collections

# discover general information about the backend
terms_of_service()
privacy_policy()

# endpoints 
capabilities()
# backend web services
list_service_types()
# file formats
list_file_formats()

# discover available collections
colls = list_collections()
View(colls)
names(colls)
describe_collection(collection = "TERRASCOPE_S2_TOC_V2")
collection_viewer("TERRASCOPE_S2_TOC_V2")

# discover available processes
processes = list_processes()
View(processes)
names(processes)
describe_process(process = "filter_bbox")
process_viewer("filter_bbox")

# discover your jobs (if there were any submitted)
list_jobs()

# discover GEE backend ---------------------------------------------------------
# to the gee backend we are connecting without logging in. It's enough for 
# the backend discovery.
# Also check the "Connections" tab in RStudio. You can switch between connections
# interactively.
host = "https://earthengine.openeo.org"
con_gee = connect(host = host)

# general info
terms_of_service()
privacy_policy()

# compare collections
colls_gee = list_collections(con_gee)
names(colls)
names(colls_gee)

# compare processes
processes_gee = list_processes(con_gee)
names(processes)
names(processes_gee)

# processes that are available on vito but not on gee
setdiff(names(processes), names(processes_gee))

# processes that are available on gee but not on vito
setdiff(names(processes_gee), names(processes))

# this process is not avialable on gee
describe_process("resample_spatial")

# ---------------------------------------------------------------------------- #
# Data Access ----
# ---------------------------------------------------------------------------- #

# connect to vito backend (reactivate vito as active connection, also via Connections GUI)
host = "https://openeo.vito.be"
con = connect(host = host, 
              user = user, 
              password = pw)

# load the processes from the backend into an object
p = processes()
p

# auto completion will facilitate adressing processes
p$filter_bands()

# define a bounding box
# agricultural fields around Wageningen
# check temporal and spatial data extent for vito terrascope data here: https://viewer.terrascope.be/
bbox = list(west = 5.61,
            east = 5.66,
            south = 51.97,
            north = 51.99)

bbox_sf = st_as_sfc(st_bbox(c(xmin = bbox$west, 
                              xmax = bbox$east, 
                              ymin = bbox$south, 
                              ymax = bbox$north), 
                            crs = st_crs(4326)))
mapview(bbox_sf)

# start a process graph
# load a collection and subset
# - change collections
# - change subset parameters: spatially, temporally, bands
data = p$load_collection(id = "TERRASCOPE_S2_TOC_V2", 
                         spatial_extent = bbox,
                         temporal_extent = list("2018-08-01", 
                                                "2018-09-01"), 
                         bands = list("TOC-B02_10M", 
                                      "TOC-B03_10M", 
                                      "TOC-B04_10M"))


# save
# - change formats to suit datacube needs
# - netcdf for multidimensional cubes
# - GTiff only supports x, y, band
# - json for pixelwise (set the bounding box to a point) timeseries
list_file_formats()
result = p$save_result(data = data, format="NetCDF")

# print process graph as JSON
graph = as(result, "Graph")
graph

# client side graph validation
graph$validate()

# compute the result and check if the graph was valid
# - change format and extension according to "save_result"
compute_result(graph = graph,
               format = "NetCDF",
               output_file = "s2_subset.ncdf")

# load the result into r (stars supports multidimensional cubes)
s2 = stars::read_stars("s2_subset.ncdf")

# check the dimensions
s2
st_dimensions(s2)

# refine the dimension definitions
s2_m = merge(s2) %>% 
  st_set_dimensions(4, values = paste0("band", 1:3)) %>%
  st_set_dimensions(names = c("x", "y", "t", "band"))

# plot the result
plot(s2_m %>% slice(t, 1))
image(s2_m %>% slice(t, 1), rgb = c(3,2,1))

# for larger jobs do batch processing: not supported by all backends
# job_id = create_job(con = con,
#                     graph = graph,
#                     title = "s2_subset",
#                     description = "s2_subset")
# job_id
# start_job(job_id$id, con = con)
# done = download_results(job = job_id, folder = ".")
# done


# ---------------------------------------------------------------------------- #
# Processing ----
# ---------------------------------------------------------------------------- #

# Minimal EVI over time --------------------------------------------------------

# start building a process graph
# load a collection and subset
data = p$load_collection(id = "TERRASCOPE_S2_TOC_V2", 
                         spatial_extent = bbox,
                         temporal_extent = list("2018-08-01", 
                                                "2018-09-01"))

# calculate the EVI
# - change the evi function to ndvi
spectral_reduce = p$reduce_dimension(data = data, dimension = "bands", reducer =  function(x, context) {
  B08 = x[8]
  B04 = x[4]
  B02 = x[2]
  (2.5 * (B08 - B04)) / sum(B08, 6 * B04, -7.5 * B02, 1)
})

# select the minimum EVI along the time dimension
# - change reducer funciton to max
temporal_reduce = p$reduce_dimension(data = spectral_reduce, 
                                     dimension = "t", 
                                     reducer = function(x, context) {p$min(x)}) 

# save the result
result = p$save_result(data = temporal_reduce, format="GTiff")
graph = as(result, "Graph")
graph
graph$validate()

# compute the result and check if the graph was valid
compute_result(graph = graph, format="GTiff", output_file = "s2_evi.tif")

# load result
s2_evi = stars::read_stars("s2_evi.tif")
s2_evi
plot(s2_evi)

# ---------------------------------------------------------------------------- #
# Further examples ----
# ---------------------------------------------------------------------------- #

# These are ideas/snippets of how to alter the process graph above to achieve different goals

# - processing ndvi instead of evi ----
spectral_reduce = p$reduce_dimension(data = data, dimension = "bands", reducer =  function(x, context) {
  B04 = x[4]
  B02 = x[2]
  (B04-B02) / (B04+B02)
})

# - compare calculated ndvi vs ndvi terrascope ----
data = p$load_collection(id = "TERRASCOPE_S2_NDVI_V2", 
                         spatial_extent = bbox,
                         temporal_extent = list("2018-08-01", 
                                                "2018-09-01"))

# - load ndvi pixel timeseries as json ---- 
# one point in the fields
bbox = list(west = 5.61,
            east = 5.61,
            south = 51.97,
            north = 51.97)

# load ndvi data
# see above; maybe extend timeline

# save as json
result = p$save_result(data = data, format="JSON")

# compute the result and check if the graph was valid
compute_result(graph = graph,
               format = "JSON",
               output_file = "s2_pixel.json")

# load json into r
s2_pixel = fromJSON("s2_pixel.json")
names(s2_pixel)
s2_pixel$dims
s2_pixel$coords
s2_pixel$data # many missig values look here to see why: https://viewer.terrascope.be/
ndvi_ts = data.frame(ndvi = s2_pixel$data, 
                     day = as.Date(s2_pixel$coords$t$data), 
                     stringsAsFactors = FALSE)
ndvi_ts$ndvi[ndvi_ts$ndvi == 255] = NA
plot(ndvi_ts$day, ndvi_ts$ndvi)
library(ggplot2)
ggplot(data=ndvi_ts, aes(x=day, y=ndvi, group=1)) +
  geom_line()+
  geom_point()

# - thresholding/masking ndvi ----
# mask based on a threshold
describe_process("mask")
mask = p$apply(data = temporal_reduce, process = function(x, context) {p$lt(x = x, y = 0.1)})

masked = p$mask(data = temporal_reduce, 
                mask = mask, 
                replacement = 0)

# - data fusion
# load ndvi
# load toc
# merge_cubes


# storing user processes on the backend ----------------------------------------
# list_user_processes()
# create_user_process()
# delete_user_process()

# Eurac backend ----------------------------------------------------------------
host = "https://openeo.eurac.edu/"
con_eurac = connect(host = host)
View(con_eurac$api.mapping)

data = p$load_collection(id = "Backscatter_Sentinel1_Track015_Regular_Timeseries_2", 
                         spatial_extent= list(east= 8.36,
                                              north= 47.51,
                                              south= 47.509,
                                              west= 8.359))

