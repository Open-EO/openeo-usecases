library(openeo)
library(tibble)

gee = connect(host = backend_url,user = username,password = password,login_type = "basic")

collections = list_collections()

s1 = collections$`COPERNICUS/S1_GRD`
dims = dimensions(s1)
processes = list_processes()
p = processes()

march = p$load_collection(id = s1,
                          spatial_extent = list(west=16.06,south=48.1,east=16.65,north=48.31),
                          temporal_extent = c("2017-03-01","2017-04-01"),
                          bands = c("VV"))

april = p$load_collection(id = s1,
                          spatial_extent = list(west=16.06,south=48.1,east=16.65,north=48.31),
                          temporal_extent = c("2017-04-01","2017-05-01"),
                          bands = c("VV"))
may = p$load_collection(id = s1,
                          spatial_extent = list(west=16.06,south=48.1,east=16.65,north=48.31),
                          temporal_extent = c("2017-05-01","2017-06-01"),
                          bands = c("VV"))

mean_march = p$reduce_dimension(data = march,dimension = dims$t,reducer = function(x, context) {
  mean(x)})
mean_april = p$reduce_dimension(data = april,dimension = dims$t,reducer = function(x, context) {
  mean(x)})
mean_may = p$reduce_dimension(data = may,dimension = dims$t,reducer = function(x, context) {
  mean(x)})

R_band = p$rename_labels(data = mean_march, dimension = "bands", target = c("R"), source = array())
G_band = p$rename_labels(data = mean_april, dimension = "bands", target = c("G"), source = array())
B_band = p$rename_labels(data = mean_may, dimension = "bands", target = c("B"), source = array())

RG = p$merge_cubes(cube1 = R_band, cube2 = G_band)
RGB = p$merge_cubes(cube1 = RG, cube2 = B_band)

final = p$save_result(data = RGB,format = "GTIFF-THUMB")

compute_result(graph=graph,output_file = "uc1_temp_comp_gee.tif")