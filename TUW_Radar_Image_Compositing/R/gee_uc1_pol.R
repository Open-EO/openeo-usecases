library(openeo)
library(tibble)

gee = connect(host = backend_url,user = username,password = password,login_type = "basic")

collections = list_collections()

s2 = collections$`COPERNICUS/S1_GRD`
dims = dimensions(s2)
processes = list_processes()
p = processes()

datacube = p$load_collection(id = s2,
                          spatial_extent = list(west=16.06,south=48.1,east=16.65,north=48.31),
                          temporal_extent = c("2017-03-01","2017-04-01"),
                          bands = c("VV", "VH"))

mean = p$reduce_dimension(data = datacube,dimension = dims$t,reducer = function(x, context) {
  mean(x)})

datacube = p$reduce_dimension(data = mean,dimension = dims$bands,reducer = function(x, context) {
  vh = p$array_element(data = x,label = "VH")
  vv = p$array_element(data = x,label = "VV")
  p$subtract(x=vh, y=vv)})

blue = p$add_dimension(data = datacube,name="bands", type="bands", label="B")

green = p$filter_bands(data=mean, bands = c("VH"))
green = p$rename_labels(data=green, dimension = "bands", target = c("G"), source = c("VH"))

red = p$filter_bands(data=mean, bands = c("VV"))
red = p$rename_labels(data=red, dimension = "bands", target = c("R"), source = c("VV"))

GB = p$merge_cubes(cube1 = green, cube2 = blue)
RGB = p$merge_cubes(cube1 = GB, cube2 = red)

final = p$save_result(data = RGB,format = "GTIFF-THUMB", options = list(red="R",green="G",blue="B"))

compute_result(graph=graph,output_file = "uc1_pol_comp_gee.tif")