# libraries --------------------------------------------------------------------
# devtools::install_github(repo="Open-EO/openeo-r-client",ref="develop",dependencies=TRUE)
library(openeo)
library(dplyr)
as.data.frame(installed.packages()) %>% 
  filter(grepl(pattern = "openeo", x = Package, ignore.case = T))


# connection to openEO Eurac backend -------------------------------------------
driver_url = "https://openeo.eurac.edu"
user = "aceo" #  "guest"
password = "aceo_123"  #  "guest_123"
api_versions(url=driver_url)

conn = connect(host = driver_url, 
               user = user, 
               password = password, 
               login_type = "basic")

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

# part1: normalize backscatter data by temporal mean ---------------------------
# filter bands (polarization)
vv = p$filter_bands(data = s1a, bands = "VV")

# mean
#vv_mean = p$reduce(data = vv, dimension = "temporal", reducer = p$mean)
vv_mean = p$reduce(data = vv, dimension = "temporal", reducer = function(x) {
  p$mean(data = x)
})

conn %>% describe_process("reduce")

# save result
result = p$save_result(data = vv, format = "NETCDF")
result = p$save_result(data = vv_mean, format = "NETCDF")

# look at process graph
graph = as(result,"Graph")
graph$validate()

# compute result on backend
done = compute_result(graph = graph, format="NETCDF", output_file = "test_usecase_wetsnow_r_pz.ncdf")

# get resultl back to r
# get json back
fin = fromJSON(done)

# get raster back
library(raster)
fin = raster::stack(done)
names(fin)
fin
plot(fin)
plot(fin[[9]])
summary(fin[[9]])
mapview::mapview(fin[[9]])
rat_fin = fin$test_udf_rclient_pz.1 / fin$test_udf_rclient_pz.2
plot(rat_fin)



