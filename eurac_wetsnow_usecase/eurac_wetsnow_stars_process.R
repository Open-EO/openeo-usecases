# eurac use case with stars


# libs -------------------------------------------------------------------------
library("stars")
library("sf")
library("dplyr")
library("mapview")

# s1a backscatter workflow -----------------------------------------------------
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
vv_mean = stars::st_apply(X = vv, MARGIN = c("x", "y"), FUN = mean, na.rm = T)
vh_mean = stars::st_apply(X = vh, MARGIN = c("x", "y"), FUN = mean, na.rm = T)
# plot(vv_mean)
# plot(vh_mean)

# normalize vv and vh with reference images
# since not converted to log -> Differnece
# s1a_vv_ref1 = s1a_vv %>% slice(time, 1)/s1a_vv_mean
vv_ratio = stars::st_apply(X = vv, MARGIN = c("time"), FUN = function(x){
  x-vv_mean$mean
})

vh_ratio = stars::st_apply(X = vh, MARGIN = c("time"), FUN = function(x){
  x-vh_mean$mean
})

# lia workflow -----------------------------------------------------------------
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
  case_when(x > theta1 ~ 1, 
            x < theta2 ~ k, 
            TRUE ~ k*(1+(theta2-x)/(theta2-theta1)))
})
# plot(w)
# hist(w$S1A_IW_GRDH_20141205T171502_015_LIA_eurac.vrt, na.rm =T)
# hist(lia$S1A_IW_GRDH_20141205T171502_015_LIA_eurac.vrt, na.rm =T)

# calculate the combined ratio rc with rat_vv, rat_vh and w --------------------

# Das ist die Bauernversion... schaffe es nicht mit st_apply die Funktion unten
# abzubilden
rc_ls = lapply(X = 1:length(st_get_dimension_values(vh_ratio, "time")), 
               FUN = function(x){
                 message("at: ", x)
                 w*slice(vh_ratio, time, x)+(1-w)*slice(vv_ratio, time, x)
                 }
               )
# Bauernversion in Bauernversion: Wie bekommt man von einer Liste an stars objekten
# ein korrektes stars objekt?
# rc = st_as_stars(rc_ls, dimensions = stars::st_dimensions(rc_ls[[1]])) # for some reason this adds x, y into the attributes
rc = c(rc_ls[[1]],rc_ls[[2]],rc_ls[[3]],rc_ls[[4]],rc_ls[[5]],rc_ls[[6]],rc_ls[[7]],
       rc_ls[[8]],rc_ls[[9]],rc_ls[[10]],rc_ls[[11]],rc_ls[[12]],rc_ls[[13]],rc_ls[[14]], 
       rc_ls[[15]],rc_ls[[16]],rc_ls[[17]],rc_ls[[18]],rc_ls[[19]],rc_ls[[20]],
       rc_ls[[21]],rc_ls[[22]])
rc = stars::st_redimension(rc, new_dims = st_dimensions(rc), along = list(time = names(rc)))
rc = stars::st_set_dimensions(rc, "time", values = time_s1a)


# # calc rc combined vh_ratio, vv_ratio and w with stars
# # merge vh and vv ratio together to a datacube
# vh_vv_ratio = c(vh_ratio, vv_ratio)
# vh_vv_ratio = stars::st_redimension(vh_vv_ratio, new_dims = st_dimensions(vh_vv_ratio), along = list(band = names(vh_vv_ratio)))
# # rename bands further up! so i can use names(vh_vv_ratio) in values = ...
# vh_vv_ratio = stars::st_set_dimensions(vh_vv_ratio, "band", values = c("vh_ratio", "vv_ratio"))
# 
# # here the spatial dimension is lost :(
# rc = st_apply(X = vh_vv_ratio, MARGIN = c("time"), FUN = function(x){
#   #browser()
#   w$S1A_IW_GRDH_20141205T171502_015_LIA_eurac.vrt*x[,,1]+
#     (1-w$S1A_IW_GRDH_20141205T171502_015_LIA_eurac.vrt)*x[,,2]
# })
# str(rc$attr.attr.1)
# dim(rc$attr.attr.1)

# create wet snow map from backscatter and lia ---------------------------------
# rc (multi time) and lia (mono time to classification)
# use rc data cube as input for st_apply, and lia as a fixed part in the formula.
thr = -2
wet_snow = st_apply(rc, MARGIN = c("time"), FUN = function(x){
  case_when(x >= thr ~ 1, 
            x < thr ~ 2)
  # case_when(lia >= 75 ~ 4,
  #           lia < 25 ~ 3,
  #           x[1] >= thr ~ 2,
  #           x[1] < thr ~ 1)
})
plot(wet_snow) # kann das stimmen??? kaum wet snow
plot(vh_mean)
# nochmal checken dass vv und vh richtig assigned sind am anfang
# zeitraum bis in sommer vergrößern
# in mit stars konzept lösen... evtl stackoverflow fragen stellen
lapply(1:22, function(x)(
  table(wet_snow %>% slice(time, x))
))


# mask with lia

# how to make sure that the time dimension stays 
wet_snow = st_apply(rc, MARGIN = c("x", "y", "time"), FUN = function(x){
  case_when(x[2] >= 75 ~ 4,
            x[2] < 25 ~ 3,
            x[1] >= thr ~ 2,
            x[1] < thr ~ 1)})

wet_snow1


# classify wet snow
thr = -2
inp = c(tst, lia)
names(inp)
inp = stars::st_redimension(inp, new_dims = st_dimensions(inp), along = list(band = names(inp)))
stars::st_dimensions(inp)
stars::st_get_dimension_values(inp, which = "band")
inp = stars::st_set_dimensions(inp, "band", values = c("rc", "lia"))
inp %>% slice(band, 1)
inp %>% slice(band, 2)

inp

wet_snow_rc = st_apply(tst, MARGIN = c("x", "y"), FUN = function(x){
  case_when(x < thr ~ 1,
            x >= thr ~ 2)
})
plot(wet_snow_rc)
table(as.vector(wet_snow_rc$S1A_IW_GRDH_20141205T171502_015_LIA_eurac.vrt))#, na.rm = TRUE)
table(as.vector(tst$S1A_IW_GRDH_20141205T171502_015_LIA_eurac.vrt < thr))
table(as.vector(tst$S1A_IW_GRDH_20141205T171502_015_LIA_eurac.vrt >= thr))

wet_snow_lia = st_apply(lia, MARGIN = c("x", "y"), FUN = function(x){
  case_when(x < 25 ~ 3, 
            x >= 75 ~ 4)
})
plot(wet_snow_lia)
table(as.vector(wet_snow_lia$S1A_IW_GRDH_20141205T171502_015_LIA_eurac.vrt))
table(as.vector(lia$S1A_IW_GRDH_20141205T171502_015_LIA_eurac.vrt < 25))
table(as.vector(lia$S1A_IW_GRDH_20141205T171502_015_LIA_eurac.vrt >= 75))

# case_when: when the first condition is evaluated to TRUE the value will be assigned, 
# the masking conditions have to come first. They let some values throuhg. 
# Then the next conditions handle all values that are left.
# Actually it would be smarter to mask the rc data cube with the lia and then do 
# the classification based on the remaining rc values
wet_snow = st_apply(inp, MARGIN = c("x", "y"), FUN = function(x){
  case_when(x[2] >= 75 ~ 4,
            x[2] < 25 ~ 3,
            x[1] >= thr ~ 2,
            x[1] < thr ~ 1)
})
plot(wet_snow)
table(wet_snow$S1A_IW_GRDH_20141205T171502_015_LIA_eurac.vrt.S1A_IW_GRDH_20141205T171502_015_LIA_eurac.vrt.1)

# modis snow cover workflow ----------------------------------------------------
# load modis snow cover data


# combine wet snow map and modis -----------------------------------------------
