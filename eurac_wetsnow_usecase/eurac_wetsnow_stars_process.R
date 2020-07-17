# eurac use case with stars


# libs -------------------------------------------------------------------------
library("stars")
library("sf")
library("dplyr")
library("mapview")

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
aoi = st_bbox(c(xmin = 10.570392608642578, 
                ymin = 46.78148963659169, 
                xmax = 10.777416229248047, 
                ymax = 46.85244345762143), 
              crs = 4326)
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

# desired version and tests ------------------------------------------------
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
plot(wet_snow_rc) # kann das stimmen??? kaum wet snow
lapply(1:22, function(x)(
  table(wet_snow_rc %>% slice(time, x))
))

# create overlay and shadow mask from lia
lia_mask = st_apply(lia, MARGIN = c("x", "y"), FUN = function(x){
  case_when(x >= 75 ~ 0, # shadow
            x < 25 ~ 0, # overlay
            TRUE ~ 1)  # ok
})
plot(lia_mask)

# apply mask to initial wet snow classification
wet_snow = st_apply(wet_snow_rc, MARGIN = c("time"), FUN = function(x){
  lia_mask$S1A_IW_GRDH_20141205T171502_015_LIA_eurac.vrt * x
})
plot(wet_snow)

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
pth_mod_2015 = "/mnt/CEPH_PRODUCTS/EURAC_SNOW/MODIS/ST/2015/"
pth_mod_2016 = "/mnt/CEPH_PRODUCTS/EURAC_SNOW/MODIS/ST/2016/"
files_mod = list.files(path = c(pth_mod_2015, pth_mod_2016), pattern = ".tif", full.names = TRUE)

# get modis dates
files_mod = data.frame(path = files_mod, 
                      date = gsub(pattern = ".*([[:digit:]]{8})T.*", replacement = "\\1", x = files_mod), 
                      stringsAsFactors = FALSE)
files_mod$date = as.Date(files_mod$date, "%Y%m%d")

# get available s1 wet snow dates
s1_dates = as.Date(stars::st_get_dimension_values(wet_snow, "time"), "%Y-%m-%d")

# resample temporal - get the matching dates
files_mod = files_mod[files_mod$date %in% s1_dates, ]
length(s1_dates) == nrow(files_mod)
# get closest dates here, so that all dates are matched

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

#-> is there a composite product?

# resample spatial

# add modis snow cover info to s1 wet snow map


# further ideas ----
# visualize as gif
# add dem
# make 3d gif with underlying dem to see where the snow gets wet and when

