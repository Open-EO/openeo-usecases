# Eurac Wet Snow Use Case - VITO Backend

# libraries --------------------------------------------------------------------
#devtools::install_github(repo="Open-EO/openeo-r-client",ref="develop",dependencies=TRUE)
library(openeo)
library(dplyr)
as.data.frame(installed.packages()) %>% 
  filter(grepl(pattern = "openeo", x = Package, ignore.case = T))


# connection to openEO vito backend -------------------------------------------
# driver_url = "https://openeo.eurac.edu"
# user = "guest" #  "guest"
# password = "guest_123"  #  "guest_123"

user = "user"
password = "user123"
driver_url = "https://openeo.vito.be"

conn = connect(host = driver_url, 
               user = user, 
               password = password, 
               login_type = "basic")



# get some descriptions of eurac backend ---------------------------------------
describe_collection("S1_GRD_SIGMA0_ASCENDING")
#describe_collection("EURAC_SNOW_CLOUDREMOVAL_MODIS_ALPS_LAEA") # snow mask is missing

# process graph ----------------------------------------------------------------
# define an spatial extent
# weisskugel
aoi = list("west" = 10.570392608642578,
           "south" = 46.78148963659169,
           "east" = 10.777416229248047,
           "north" = 46.85244345762143)
# canazei
aoi = list("west" = 11.495501519821119,
           "south" = 46.33970892265867,
           "east" = 12.04481792607112,
           "north" = 46.51293492736491)


# define an temporal extent
# timespan = c("2015-11-06T00:00:00.000Z",   
#              "2016-09-25T00:00:00.000Z")
timespan = c("2018-01-01T00:00:00.000Z",   
             "2019-01-01T00:00:00.000Z")

# get processes available on backend
p = processes()

# load data cube, filter temporally and spatially ------------------------------
s1a = p$load_collection(id = "S1_GRD_SIGMA0_ASCENDING", 
                        temporal_extent = timespan, 
                        spatial_extent = aoi , bands = c("VV", "VH", "angle")) 

# part1: normalize backscatter data by temporal mean ---------------------------
# filter bands (polarization)
vv = p$filter_bands(data = s1a, bands = "VV")
vh = p$filter_bands(data = s1a, bands = "VH")
lia = p$filer_bands(data = s1a, bands = "angle")

# apply temporal min to each polarization
vv_min = p$reduce_dimension(data = vv, dimension = "temporal", reducer = function(x, context) {p$min(x)})
vh_min = p$reduce_dimension(data = vh, dimension = "temporal", reducer = function(x, context) {p$min(x)})

list_file_formats()
int_result = p$save_result(data = vv_min, format = "GTiff")
graph = as(int_result, "Graph")
graph
graph$validate()

(resultfile = compute_result(graph = graph, format="GTiff", output_file = "int_result.GTiff"))
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
