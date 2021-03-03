# Eurac Wet Snow Use Case - Eurac Backend

# libraries --------------------------------------------------------------------
#devtools::install_github(repo="Open-EO/openeo-r-client",ref="develop",dependencies=TRUE)
library(openeo)
library(dplyr)
as.data.frame(installed.packages()) %>% 
  filter(grepl(pattern = "openeo", x = Package, ignore.case = T))


# connection to openEO Eurac backend -------------------------------------------
driver_url = "https://openeo.eurac.edu"
user = "guest" #  "guest"
password = "guest_123"  #  "guest_123"
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
describe_collection("Backscatter_Sentinel1_Track015_Regular_Timeseries_Tiled_1000")
describe_collection("LIA_Sentinel1_Track015_Ingested")
describe_collection("EURAC_SNOW_CLOUDREMOVAL_MODIS_ALPS_LAEA")

# process graph ----------------------------------------------------------------
# define an spatial extent
# weisskugel
aoi = list("west" = 10.570392608642578,
           "south" = 46.78148963659169,
           "east" = 10.777416229248047,
           "north" = 46.85244345762143)

# define an temporal extent
timespan = c("2015-11-06T00:00:00.000Z",   
             "2016-09-25T00:00:00.000Z")
timespan = c("2015-01-28T00:00:00.000Z",   
             "2016-01-28T00:00:00.000Z")

# get processes available on backend
p = processes()

# load data cube, filter temporally and spatially ------------------------------
s1a = p$load_collection(id = "Backscatter_Sentinel1_Track015_Regular_Timeseries_Tiled_1000", 
                        temporal_extent = timespan, 
                        spatial_extent = aoi , bands = c("VV", "VH")) 
                        # bands = "VV") #c("VV", "VH")

# part1: normalize backscatter data by temporal mean ---------------------------
# filter bands (polarization)
vv = p$filter_bands(data = s1a, bands = "VV")
vh = p$filter_bands(data = s1a, bands = "VH")

# apply temporal min to each polarization
vv_min = p$reduce_dimension(data = vv, dimension = "temporal", reducer = function(x, context) {p$min(x)})
vh_min = p$reduce_dimension(data = vh, dimension = "temporal", reducer = function(x, context) {p$min(x)})

int_result = p$save_result(data = vv_min, format = "json")
graph = as(int_result, "Graph")
graph
graph$validate()

(resultfile = compute_result(graph = graph, format="json", output_file = "int_result.json"))
job_id = create_job(con = conn,
                    graph = graph,
                    title = "intres",
                    description = "itnres")
job_id
start_job(job_id$id, con = conn)
done = download_results(job = job_id, folder = ".")
done

# merge cubes for intermediate result: -> how to enter the overlap resolver?
int_result = p$merge_cubes(cube2 = vv_min, cube1 = vh_min, overlap_resolver = function(x, context) {p$mean(x)})
int_result = p$merge_cubes(cube1 = vh_min, cube2 = vv_min, overlap_resolver = function(x, context) {p$min(x)})
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
