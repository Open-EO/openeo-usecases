# eurac use case with stars

# libs -------------------------------------------------------------------------
library("stars")
library("sf")
library("dplyr")
library("mapview")
library("ggplot2")

# ---------------------------------------------------------------------------- #
# module 1: normalize backscatter ----
# ---------------------------------------------------------------------------- #

# load s1a backscatter 
path_s1a = "/mnt/CEPH_FS_RASDAMAN/VRT/OpenEO_UseCase/T015"
files_s1a = list.files(path = path_s1a, pattern = "VH_VV_eurac.vrt$", full.names = TRUE)
files_s1a = files_s1a[28:49]
time_s1a = gsub(pattern = ".*_([0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9])T.*", 
                replacement = "\\1", x = files_s1a)
time_s1a = as.Date(x = time_s1a, format = "%Y%m%d")

backscatter_prox = read_stars(.x = files_s1a, along = "time", proxy = TRUE)
backscatter_prox = st_set_dimensions(.x = backscatter_prox, which = "time", 
                                     values = time_s1a)

# prepare bbox for subsetting proxy object
# weisskugel area
aoi = st_bbox(c(xmin = 10.570392608642578, 
                ymin = 46.78148963659169, 
                xmax = 10.777416229248047, 
                ymax = 46.85244345762143), 
              crs = 4326)
# south tyrol
# not readable into r... too big... not even 2 timesteps
# aoi = read_sf("/mnt/CEPH_BASEDATA/GIS/REGIONAL/SOUTHTYROL/BOUNDARIES/NUTS3/SouthTyrol_gcs.kml")
# aoi = st_bbox(aoi)

aoi = st_transform(x = st_as_sfc(aoi), crs = st_crs(backscatter_prox))

# subset on proxy
backscatter_prox = backscatter_prox[aoi]

# fetch the data - only reading the subsetted part!
backscatter = st_as_stars(backscatter_prox)

# split into vv and vh
vv = backscatter %>% dplyr::slice(band, 2)
vh = backscatter %>% dplyr::slice(band, 1)

# create reference images vv vh - incorrect: 
# mean of dec/jan/feb -> dry snow conditions
# or select image where variance is the lowest
# or aggregate to temporal maximum = dry condition
vv_ref = stars::st_apply(X = vv, MARGIN = c("x", "y"), FUN = max, na.rm = T) # use mean for use case def
vv_ref = stars::st_apply(X = vv_ref, MARGIN = c("x", "y"), FUN = function(x){
  ifelse(is.finite(x), x, NA) # when using max inf values appear? get rid of them
})
vh_ref = stars::st_apply(X = vh, MARGIN = c("x", "y"), FUN = max, na.rm = T) # use mean for use case def
vh_ref = stars::st_apply(X = vh_ref, MARGIN = c("x", "y"), FUN = function(x){
  ifelse(is.finite(x), x, NA) # when using max inf values appear? get rid of them
})
# plot(vv_ref)
# plot(vh_ref)

# normalize vv and vh with reference images
# since not converted to log -> Differnece
# s1a_vv_ref1 = s1a_vv %>% slice(time, 1)/s1a_vv_ref
vv_ratio = stars::st_apply(X = vv, MARGIN = c("time"), FUN = function(x){
  x-vv_ref[[1]]
})

vh_ratio = stars::st_apply(X = vh, MARGIN = c("time"), FUN = function(x){
  x-vh_ref[[1]]
})

# ---------------------------------------------------------------------------- #
# module 2: create weights layer from lia ----
# ---------------------------------------------------------------------------- #
# load lia 
files_lia = list.files(path = path_s1a, pattern = "LIA_eurac.vrt$", full.names = TRUE)
lia_prox = read_stars(.x = files_lia, proxy = TRUE)

# subset on proxy
lia_prox = lia_prox[aoi]

# fetch the data - only reading the subsetted part!
lia = st_as_stars(lia_prox)

# define constants
theta1 = 20
theta2 = 45
k = 0.5

# classify lia
w = st_apply(lia, MARGIN = c("x", "y"), FUN = function(x){
  case_when(x < theta1 ~ 1, 
            x > theta2 ~ k, 
            TRUE ~ k*(1+(theta2-x)/(theta2-theta1)))
})
# plot(w)
# hist(w$S1A_IW_GRDH_20141205T171502_015_LIA_eurac.vrt, na.rm =T)
# hist(lia$S1A_IW_GRDH_20141205T171502_015_LIA_eurac.vrt, na.rm =T)

# ---------------------------------------------------------------------------- #
# module 3: create wet snow map based on s1 
# ---------------------------------------------------------------------------- #

# farmerversion ----------------------------------------------------------------
# # Das ist die Bauernversion... schaffe es nicht mit st_apply die Funktion unten
# # abzubilden
# rc_ls = lapply(X = 1:length(st_get_dimension_values(vh_ratio, "time")), 
#                FUN = function(x){
#                  message("at: ", x)
#                  w*slice(vh_ratio, time, x)+(1-w)*slice(vv_ratio, time, x)
#                  }
#                )
# # Bauernversion in Bauernversion: Wie bekommt man von einer Liste an stars objekten
# # ein korrektes stars objekt?
# # rc = st_as_stars(rc_ls, dimensions = stars::st_dimensions(rc_ls[[1]])) # for some reason this adds x, y into the attributes
# rc = c(rc_ls[[1]],rc_ls[[2]],rc_ls[[3]],rc_ls[[4]],rc_ls[[5]],rc_ls[[6]],rc_ls[[7]],
#        rc_ls[[8]],rc_ls[[9]],rc_ls[[10]],rc_ls[[11]],rc_ls[[12]],rc_ls[[13]],rc_ls[[14]], 
#        rc_ls[[15]],rc_ls[[16]],rc_ls[[17]],rc_ls[[18]],rc_ls[[19]],rc_ls[[20]],
#        rc_ls[[21]],rc_ls[[22]])
# rc = stars::st_redimension(rc, new_dims = st_dimensions(rc), along = list(time = names(rc)))
# rc = stars::st_set_dimensions(rc, "time", values = time_s1a)
# farmerversion: end ------------------------------------------------------------

# desired version and tests ----------------------------------------------------
# # calc rc combined vh_ratio, vv_ratio and w with stars
# # merge vh and vv ratio together to a datacube
# vh_vv_ratio = c(vh_ratio, vv_ratio)
# names(vh_vv_ratio) = c("vh_ratio", "vv_ratio")
# vh_vv_ratio = stars::st_redimension(vh_vv_ratio, new_dims = st_dimensions(vh_vv_ratio), along = list(band = names(vh_vv_ratio)))
# 
# # here the spatial dimension is lost :(
# rc = st_apply(X = vh_vv_ratio, MARGIN = c("time"), FUN = function(x){
#   w$S1A_IW_GRDH_20141205T171502_015_LIA_eurac.vrt*x[,,1]+
#     (1-w$S1A_IW_GRDH_20141205T171502_015_LIA_eurac.vrt)*x[,,2]
# })
# 
# rc3 = st_apply(X = vh_vv_ratio, MARGIN = c("time"), FUN = function(x){
#   #browser()
#   x[,,1]+x[,,2]
# })
# 
# rc4 = slice(vh_vv_ratio, "band", 1) +  slice(vh_vv_ratio, "band", 2)
# rc5 = vh_vv_ratio[,,,,1]+vh_vv_ratio[,,,,2]
# 
# rc6 = st_apply(X = vh_vv_ratio, MARGIN = c("x", "y", "time"), FUN = function(x){
#   x[1]+x[2]
# })
# desired version and tests: end -----------------------------------------------

# calculate rc layer -----------------------------------------------------------
# calculate first part of function
rc1 = st_apply(X = vh_ratio, MARGIN = c("time"), FUN = function(x){
  #browser()
  w$S1A_IW_GRDH_20141205T171502_015_LIA_eurac.vrt*x
})

# calculate second part of function
rc2 = st_apply(X = vv_ratio, MARGIN = c("time"), FUN = function(x){
  #browser()
  (1-w$S1A_IW_GRDH_20141205T171502_015_LIA_eurac.vrt)*x
})

# add up the two parts of the function
rc = rc1+rc2
str(rc$attr)
dim(rc$attr)

# classify rc layer into wet snow ----------------------------------------------
# rc (multi time) and lia (mono time to classification)
# use rc data cube as input for st_apply, and lia as a fixed part in the formula.
thr = -2
wet_snow_rc = st_apply(rc, MARGIN = c("time"), FUN = function(x){
  case_when(x < thr ~ 1, # wet snow
            x >= thr ~ 2) # no wet snow
})
# plot(wet_snow_rc %>% slice(time, 1)) # kann das stimmen??? kaum wet snow
lapply(1:22, function(x)(
  table(wet_snow_rc %>% slice(time, x))
))

# create overlay and shadow mask from lia
lia_mask = st_apply(lia, MARGIN = c("x", "y"), FUN = function(x){
  case_when(x >= 75 ~ 0, # shadow
            x < 25 ~ 0, # overlay
            TRUE ~ 1)  # ok
})
# plot(lia_mask)

# apply mask to initial wet snow classification
wet_snow = st_apply(wet_snow_rc, MARGIN = c("time"), FUN = function(x){
  lia_mask$S1A_IW_GRDH_20141205T171502_015_LIA_eurac.vrt * x
})
plot(wet_snow %>% slice(), col = c("black", "blue", "red"))
wet_snow
# ---------------------------------------------------------------------------- #
# module 4: add modis snow cover ----
# ---------------------------------------------------------------------------- #
# make a file list with all modis data in the period where s1 is available
# then get the dates from the current snow map
# extract these dates from the modis file list
# load these dates into a datacube
# resample spatial
# multiply

# make modis file list
# # daily
# pth_mod_2015 = "/mnt/CEPH_PRODUCTS/EURAC_SNOW/MODIS/ST/2015/"
# pth_mod_2016 = "/mnt/CEPH_PRODUCTS/EURAC_SNOW/MODIS/ST/2016/"
# files_mod = list.files(path = c(pth_mod_2015, pth_mod_2016), pattern = ".tif", full.names = TRUE)
# # 15d
# pth_mod = "/mnt/CEPH_PRODUCTS/EURAC_SNOW_COMPOSITE_P_CMF/MODIS/alps/"
# files_mod = list.files(path = pth_mod, pattern = ".tif", full.names = TRUE)

# newest version as on rasdaman
pth_mod = "/mnt/CEPH_PROJECTS/SNOW_3rd_gen/CLOUDREMOVAL/v1.2/05_temporal_complete_max10d"
files_mod = list.files(path = pth_mod, pattern = ".tif", full.names = TRUE)

# get modis dates
files_mod = data.frame(path = files_mod, 
                       #date = gsub(pattern = ".*([[:digit:]]{8})T.*", replacement = "\\1", x = files_mod),
                       date = gsub(pattern = ".*([[:digit:]]{8})_.*", replacement = "\\1", x = files_mod),
                       stringsAsFactors = FALSE)
files_mod$date = as.Date(files_mod$date, "%Y%m%d")

# get available s1 wet snow dates
s1_dates = as.Date(stars::st_get_dimension_values(wet_snow, "time"), "%Y-%m-%d")

# resample temporal - get the matching dates
files_mod = files_mod[files_mod$date %in% s1_dates, ]
length(s1_dates) == nrow(files_mod)
# TODO: get closest dates here in case not matching on day, so that all dates are matched
file.exists(files_mod$path)
# is upon reading there are corrupt files replace them here
# files_mod[files_mod$date == "2016-03-05", "path"] = "/mnt/CEPH_PRODUCTS/EURAC_SNOW_COMPOSITE_P_CMF/MODIS/alps//20160306_MOD_CM-SNWF_05745090-AA.tif"

# load modis data
modis_prox = read_stars(.x = files_mod$path, along = "time", proxy = TRUE)
modis_prox = st_set_dimensions(.x = modis_prox, which = "time", 
                               values = files_mod$date)
aoi = st_transform(x = aoi, crs = st_crs(modis_prox))

# subset on proxy
modis_prox = modis_prox[aoi]

# fetch the data - only reading the subsetted part!
modis = st_as_stars(modis_prox, along = "time")
# remove quality band
modis = modis %>% slice("band", 1)
plot(modis) # 0 = no data, 1= snow , 2= no snow, 3= cloud 

# resample spatial
modis_res = stars::st_warp(src = modis, dest = wet_snow)
st_crs(modis) = st_crs(wet_snow)
st_crs(wet_snow)
# add modis snow cover info to s1 wet snow map as a band
wet_snow_mod = c(wet_snow, modis_res, along = "band")
plot(wet_snow_mod %>% slice(time, 1))

# apply classification based on two bands
# takes too long

wet_snow_fin = st_apply(X = wet_snow_mod, MARGIN = c("x", "y", "time"), FUN = function(x){
  case_when(x[2] == 2  ~ 1, # no snow 
            x[2] == 1 & x[1] == 1 ~ 2, # wet snow  
            x[2] == 1 & x[1] == 2 ~ 3, # dry snow
            x[2] == 1 & x[1] == 0 ~ 4, # uncl. snow
            TRUE ~ 5)
})

# multiplication would also work here instead case_when
# modis
# 1 snow
# 2 no snow
# s1
# 1 wet snow
# 2 dry snow
# 0 shadow

# save
# stars::write_stars(obj = wet_snow_fin, dsn = "eurac_wetsnow_stars_process.nc", driver = "netCDF") # doesn't give bandnames (dates)
save(wet_snow_fin, file = "/home/pzellner@eurac.edu/git_projects/openeo-usecases/eurac_wetsnow_usecase/eurac_wetsnow_stars_process.rdata")
wet_snow_fin

# ---------------------------------------------------------------------------- #
# analysis of results ----
# ---------------------------------------------------------------------------- #
(load("/home/pzellner@eurac.edu/git_projects/openeo-usecases/eurac_wetsnow_usecase/eurac_wetsnow_stars_process.rdata"))

# plot pixel timeseries --------------------------------------------------------
# get timeseries for pixel in vally, on glacier and non glacier mountain
# define point in valley
px_valley <- data.frame(x = 10.649538, y = 46.839743) # hm 1945 m; Point in the valley floor of Langtauferer Tal on a pasture close to Melago
px_valley = st_as_sf(px_valley, coords = c("x", "y"), crs = 4326)
px_valley = st_transform(px_valley, crs = st_crs(wet_snow_fin))
# define point on glacier
px_glacier <- data.frame(x = 10.757980, y = 46.792620) # hm 2965 m; Point on the glacier Hintereisferner east of the peak Weißkugel
px_glacier = st_as_sf(px_glacier, coords = c("x", "y"), crs = 4326)
px_glacier = st_transform(px_glacier, crs = st_crs(wet_snow_fin))

image(wet_snow_fin, axes = TRUE)
plot(px_valley, add = TRUE)
plot(px_glacier, add = TRUE)

# extract values at the points
# this should do it in stars fashion... but doesn't really work
# (wet_snow_fin[px_glacier])

# wrapper function to use raster::extract
# raster_extract taken from here
# https://www.rdocumentation.org/packages/nngeo/versions/0.3.0/source
raster_extract = function(x, y, fun = NULL, na.rm = FALSE) {
  x = as(x, "Raster")
  y = as(y, "Spatial")
  raster::extract(x = x, y = y, fun = fun, na.rm = na.rm)
}

# extract the values
val_valley = raster_extract(x = wet_snow_fin, y = px_valley)
val_glacier = raster_extract(x = wet_snow_fin, y = px_glacier)

# make a dataset with the timeseries of valley and glacier and the according dates
dates = stars::st_get_dimension_values(wet_snow_fin, "time")
ts_valley_glacier = data.frame(valley = c(val_valley), glacier = c(val_glacier),  date = dates)

# plot the time series
ts_valley_glacier = tidyr::gather(ts_valley_glacier, location, value, valley:glacier)
ts_plot = ggplot(data = ts_valley_glacier, aes(x = date, y = factor(value), group = location)) +
  geom_point() +
  geom_line() +
  scale_y_discrete(labels = c("1" = "no_snow", "2" = "wet_snow", "3" = "dry_snow")) +
  scale_x_date(date_breaks = "months" , date_labels = "%b-%y") +
  labs(y="snow_class") +
  facet_grid(location ~ .)

ggsave(filename = "eurac_wetsnow_pixel_ts.png", 
       plot = ts_plot, 
       device = "png", 
       path = "/home/pzellner@eurac.edu/git_projects/openeo-usecases/eurac_wetsnow_usecase/images/")

# plot selected time steps of raster time series -------------------------------
wet_snow_fin_4ts = wet_snow_fin %>% slice(time, c(1, 7, 13, 20))
wet_snow_fin_4ts = cut(wet_snow_fin_4ts, breaks = c(0, 1, 2, 3, 4, 5), 
                       labels = c("no_snow", "wet_snow", "dry_snow", "uncl_snow", "NA"))

classfication_plot = ggplot() +
  geom_stars(data = wet_snow_fin_4ts, alpha = 0.8) + #, downsample = c(10, 10, 1)) +
  facet_wrap("time") +
  scale_fill_manual(values =  c("darkolivegreen1", "lightblue", "blue", "darkblue", "white")) + 
  coord_equal() +
  labs(fill = "classes") +
  theme_map() +
  theme(legend.position = "bottom") +
  theme(legend.key.width = unit(2, "cm"))

ggsave(filename = "eurac_wetsnow_raster_ts.png", 
       plot = classfication_plot, 
       device = "png", 
       path = "/home/pzellner@eurac.edu/git_projects/openeo-usecases/eurac_wetsnow_usecase/images/")


# plot area of interest --------------------------------------------------------
library(tmap)
library(tmaptools)

# bbox
bbox = st_bbox(wet_snow_fin) 
sf_bbox <- st_as_sfc(bbox)
sf_bbox_latlon <- st_transform(sf_bbox, crs = 4326)

# both points together
# get from px_valley, px_glacier
points <- tibble::tribble(
  ~x, ~y, ~label,
  10.649538, 46.839743, "Valley",
  10.757980, y = 46.792620, "Glacier"
)
sf_points <- st_as_sf(points, coords = c("x", "y"), crs = 4326)
sf_points <- st_transform(sf_points, crs = 3035)

tmap_mode("plot")

basemap <- read_osm(sf_bbox_latlon, type = "stamen-terrain", zoom = 12, ext = 3)

tm1 <- 
  tm_shape(basemap)+
  tm_rgb()+
  tm_shape(sf_bbox)+
  tm_borders(lty = "solid", col = "orange", lwd = 2)+
  
  tm_shape(sf_points)+
  tm_symbols(col = "label", title.col = "")+
  tm_legend(frame = T, text.size = 1.5, position = c("left", "bottom"))+
  tm_add_legend(labels="Study region", col="white", border.col="orange")+
  
  tm_scale_bar(text.size = 1)+
  tm_credits("Map tiles by Stamen Design, under CC BY 3.0. Data by OpenStreetMap, under ODbL.",
             bg.color = "white")

tm1
tmap_save(tm1, "/home/pzellner@eurac.edu/git_projects/openeo-usecases/eurac_wetsnow_usecase/images/eurac_wetsnow_aoi.png", 
          width = 8, height = 4, units = "in")



# further ideas ----
# plot with background map and transparency
# visualize as gif
# add dem
# make 3d gif with underlying dem to see where the snow gets wet and when

