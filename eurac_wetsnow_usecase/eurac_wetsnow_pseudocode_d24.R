# UC4: Snow Monitoring with Sentinel-1 and Sentinel-3
# The implementation of UC4: Snow Monitoring with Sentinel-1 and Sentinel-3 
# creates a wet snow map using Sentinel-1 radar data. In a second step the 
# resulting datacube is merged with the Modis Snow Cover product created by 
# Eurac in order to extract the 4 classes no_snow, wet_snow, dry_snow and snow.
# The crucial part of the calculation relies on thresholding and nested 
# if-else-statements which are expressed through user defined functions  

# Workflow:
# 1 Preprocessing
# - Generate polarization reference images (from two data cubes sentinel 
#   1a vv and vh) from the winter season. 
#   Functions: Select timespan and temporally reduce by mean.
#   Result: Two datacubes with one layer
# - Calculate ratio polarization images for each timestep. 
#   Functions: Subtract each image (s1a vv and vh) from the reference image 
#     (subtract data cube with temporal dimension from 
#     datacube without temporal dimension)
#   Result: Two datacubes with time dimension
# - Create datacube from 3 datacubes: ratio_vv, ratio_vh, lia (s1 incident angle)
#   Result: Datacube with temporal dimension and 3 bands
#
# 2 Wet snow detection using nagler wet snow algorithm
# - calculate weight (w) for the generation of the combined vv-vh ratio (rc).
#   Functions: Nested if-else or case_when statement, on multiple bands, 
#     evaluating against constants, assigning values according to case
#   Result: Add the layer w to the input datacube
# - calculate the combined vv-vh ratio (rc): w * rat_vh + (1 - w) * rat_vv
#   Functions: Band arithmetic, also using constants
#   Result: Add the layer rc to the input datacube
# - Generation of the wet snow map
#   Functions: Nested if-else or case_when statement, on multiple bands, 
#     evaluating against constants, assigning values according to case
#   Result: add wet_snow layer to the datacube
# - Reducing data cube to only keep wet_snow layer
#   Function: drop bands
#   Result: data cube with one band and temporal dimension
#
# 3 Combination of wet snow map with binary snow map derived from modis
# - Combine wet snow map and modis snow map into one data cube
#   Functions: Combine two data cubes with each one band and temporal dimension.
#     Spatial and temporal resolution differ.
# - Classify into dry_snow, wet_snow, no_snow using information of both bands.
#   Functions: Nested if-else or case_when statement, on multiple bands, 
#     assigning values according to case
#   Result: Add the layer snow_class to the input datacube
# - Reducing data cube to only keep snow_class layer
#   Function: drop bands
#   Result: data cube with one band and temporal dimension

# libraries
library(openeo)
library(dplyr)

# connection to openEO Eurac backend 
driver_url = "https://openeo.eurac.edu"
user = "aceo"
password = "aceo_123"

conn = connect(host = driver_url, 
               user = user, 
               password = password, 
               login_type = "basic")

# 1. Preprocessing Sentinel 1 A radar data for wet snow detection ==============
# define timespan
timespan = c("2014-09-01T00:00:00.000Z",   
             "2015-09-01T00:00:00.000Z")

# start an empty process graph
graph = conn %>% process_graph_builder()

# load data cubes
s1a_vv = graph$load_collection(id = graph$data$`s1a_t117_epsg3035_20m_VV`,
                               temporal_extent = timespan)
s1a_vh = graph$load_collection(id = graph$data$`s1a_t117_epsg3035_20m_VH`,
                               temporal_extent = timespan)
s1a_lia = graph$load_collection(id = graph$data$`s1a_t117_epsg3035_20m_LIA`,
                                temporal_extent = timespan)

# create reference image VV
ref_vv = s1a_vv %>% graph$mean_time()

# create reference image VH
ref_vh = s1a_vh %>% graph$mean_time()

# calculate ratio vv to reference
rat_vv = s1a_vv %>% graph$calc_cubes(fun = "subrtact", ref_vv)

# calculate ratio vh to reference
rat_vh = s1a_vh %>% graph$calc_cubes(fun = "subtract", ref_vh)

# prepare datacube as input for nagler wet snow algorithm
datacube = graph$merge_cubes(rat_vv, rat_vh, s1a_lia)

# 2. Wet snow detection using Nagler algorithm =================================
# nagler algorithm input description 
# rat_vv, rat_vh  -> vv and vh backscatter ratio of the image versus the
#                    reference transformed to a logarithmic scale (dB).
# lia             -> local incidence angle in degrees
# k,theta1,theta2 -> Tuning parameters used for the computation of the 
#                    combined vv-vh ratio image Rc. The values in (Nagler et
#                    al.,2016) are k=0.5, theta1=20, theta2=45
# thr             -> Threshold in dB. In (Nagler et. al, 2016) THR=-2

# 2.1 calculate weight (w) for the combined vv-vh ratio (rc) -------------------
# filter lia band
lia_band = datacube %>% filter_band("s1a_lia")

# define the udf r script
udf_script = quote({
  theta1 = 20
  theta2 = 45
  k = 0.5
  w = st_apply(data, MARGIN = "band", FUN = function(x){
    case_when(x > theta1 ~ 1, 
              x < theta2 ~ k, 
              TRUE ~ k*(1+(theta2-x)/(theta2-theta1)))
  })
  return(w)
})

# run the udf on the subsetted lia band
port = 5555
host = "http://euracrudfhost"
w = lia_band %>% graph$apply() %>% 
  graph$run_udf(code = script_udf, host = host, port = port)

# 2.2 calculate the combined vv-vh ratio (rc): w*rat_vh+(1-w)*rat_vv -----------
rc = datacube %>% 
  band_arithmetics(data = graph, formula = function(x){x[4]*x[2]+(1-x[4])*x[1]})

# 2.3 generation of the wet snow map -------------------------------------------
# keep only rc and lia bands in datacube
datacube = datacube %>% filter_bands(bands = c("rc", "lia"))

# classify based on bands rc and lia into:
# 1 = wet snow, 2 = no wet snow, 3 = shadow, 4 = overlay
udf_script = quote({
  thr = -2
  wet_snow = st_apply(data, MARGIN = "band", FUN = function(x){
    case_when(x["rc"] < thr ~ 1, 
              x["rc"] >= thr ~ 2, 
              x["lia"] < 25 ~ 3, 
              x["lia"] >= 75 ~ 4)
  })
  return(wet_snow)
})

wet_snow = datacube %>% graph$reduce("band") %>% 
  graph$run_udf(code = script_udf, host = host, port = port)

# 3. Combine the wet snow map with modis snow cover product ====================
# Identify the portion of snow which is wet snow
# modis_snow: 1 = snow, 0 = no_snow
# data_cube_wet_snow: 1 = wet_snow, 2 = no_wet_snow, 3 = shadow, 4 = overlay

# load modis snow cover product produced by Eurac Research
modis_snow = graph$load_collection(id = graph$data$`modis_snowcover_product`,
                                   temporal_extent = timespan)

# resample modis snow cover datacube to s1a wet snow datacube
modis_snow = graph$resample_cube_spatial(source = "modis_snow", 
                                         target = "datacube_wet_snow", 
                                         fun = "near")
modis_snow = graph$resample_cube_temporal(source = "modis_snow", 
                                         target = "datacube_wet_snow", 
                                         fun = "max")

# merge sentinel 1 wet snow and modis snow cover
datacube_snow = graph$merge_cubes(datacube_wet_snow, modis_snow)

# classify into no_snow = 0, wet_snow = 1, dry_snow = 2, snow = 3
udf_script = quote({
  snow_class = st_apply(data, MARGIN = "band", FUN = function(x){
    case_when(x["modis_snow"] == 0 ~ 0, 
              x["modis_snow"] == 1 & x["wet_snow"] == 1 ~ 1, 
              x["modis_snow"] == 1 & x["wet_snow"] == 2 ~ 2, 
              x["modis_snow"] == 1 & x["wet_snow"] %in% c(3,4) ~ 3)
  })
  return(snow_class)
})

snow_class = datacube_snow %>% graph$reduce("band") %>% 
  graph$run_udf(code = script_udf, host = host, port = port)

# set final node of the graph
graph$save_result(data = datacube_snow, format = "GeoTiff") %>% 
  graph$setFinalNode()

# export snow class map as geotiff
job_id = conn %>% create_job(graph=graph, 
                             title="wet_snow_map", 
                             description="wet_snow_map",
                             format="GeoTiff")

conn %>% start_job(job_id)
result_obj = conn %>% list_results(job_id)
conn %>% download_results(job = job_id)




