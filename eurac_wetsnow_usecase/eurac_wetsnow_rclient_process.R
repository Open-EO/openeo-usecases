# test r-udf with r-client and eurac backend

# libraries --------------------------------------------------------------------
#devtools::install_github(repo="Open-EO/openeo-r-client",ref="develop",dependencies=TRUE)
library(openeo)
library(dplyr)
as.data.frame(installed.packages()) %>% 
  filter(grepl(pattern = "openeo", x = Package, ignore.case = T))


# connection to openEO Eurac backend -------------------------------------------
driver_url = "https://openeo.eurac.edu"
user = "aceo" #  "guest"
password = "aceo_123"  #  "guest_123"
api_versions(url=driver_url)

# httr::set_config(httr::config(ssl_verifypeer = 0L))
# httr::set_config(httr::config(ssl_verifyhost= 0L))
# driver_url = "https://10.8.244.137:8443"
# user = "guest"
# password = "guest_123"

conn = connect(host = driver_url, 
               user = user, 
               password = password, 
               login_type = "basic")



# get some descriptions of eurac backend ---------------------------------------
api_versions(url=driver_url)
list_udf_runtimes(conn)$R

#conn %>% openeo::list_collections()
conn %>% describe_collection("Backscatter_Sentinel1_Track015")
conn %>% describe_collection("LIA_Sentinel1_Track015")

#conn %>% list_processes()
conn %>% describe_process("filter_bands")
conn %>% describe_process("reduce")

process_viewer()
collection_viewer()

# process graph ----------------------------------------------------------------
# define an spatial extent
# weisskugel
aoi = list("west" = 10.570392608642578,
           "south" = 46.78148963659169,
           "east" = 10.777416229248047,
           "north" = 46.85244345762143)

# define an temporal extent
timespan = c("2014-11-01T00:00:00.000Z",   
             "2015-05-01T00:00:00.000Z")

# get processes available on backend
p = processes()

# load data cube, filter temporally and spatially ------------------------------
s1a = p$load_collection(id = p$data$Backscatter_Sentinel1_Track015, 
                        temporal_extent = timespan, 
                        spatial_extent = aoi , bands = c("VV", "VH")) 
                        # bands = "VV") #c("VV", "VH")

# part1: normalize backscatter data by temporal mean ---------------------------
# filter bands (polarization)
vv = p$filter_bands(data = s1a, bands = "VV")
vh = p$filter_bands(data = s1a, bands = "VH")

# apply temporal mean to each polarization 
# vv_mean = p$min_time(data = vv)
# vh_mean = p$min_time(data = vh)

# try to replicate reduce/temporal/mean??? -> hot to enter the reducer?
vv_mean = p$reduce(data = vv, dimension = "temporal", reducer = p$mean)# reducer = function(x){mean(x)})
vh_mean = p$reduce(data = vh, dimension = "temporal", reducer = p$mean)# reducer = function(x){mean(x)})


# merge cubes for intermediate result: -> how to enter the overlap resolver?
int_result = p$merge_cubes(cube2 = vv_mean, cube1 = vh_mean, overlap_resolver = p$mean)

# save result
result = p$save_result(data = vv_mean, format = "GTIFF")


# look at process graph
graph = as(result,"Graph")
graph$validate()
validate_process_graph(graph = graph)

# compute result on backend
done = compute_result(graph = graph, format="GTIFF", output_file = "test_usecase_wetsnow_r_pz.GTIFF")


# get resultl back to r
fin = fromJSON(done)
library(raster)
fin = raster::stack(done)
names(fin)
fin
plot(fin[[9]])
summary(fin[[9]])
mapview::mapview(fin[[9]])
rat_fin = fin$test_udf_rclient_pz.1 / fin$test_udf_rclient_pz.2
plot(rat_fin)


# udf doesnt work
