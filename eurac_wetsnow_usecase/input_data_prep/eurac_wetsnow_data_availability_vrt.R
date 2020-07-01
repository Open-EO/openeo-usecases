# check availability s1a

# libs -------------------------------------------------------------------------
library(dplyr)
library(raster)
library(stars)


# get files s1a ----------------------------------------------------------------
path_s1a="/mnt/CEPH_PRODUCTS/S1_L1C_TEST/S1-PreProc-Test-v2/T015/EPSG3035"
files_vh = list.files(path = path_s1a, pattern = "VH_eurac$", full.names = TRUE)
files_vv = list.files(path = path_s1a, pattern = "VV_eurac$", full.names = TRUE)
files_lia = list.files(path = path_s1a, pattern = "LIA_eurac$", full.names = TRUE)

# get timeseries from filenames ------------------------------------------------
enrich_date = function(file_ls){
  df = data.frame(path = file_ls, 
                  date = gsub(pattern = ".*\\_([2][0][0-9][0-9][0-9][0-9][0-9][0-9])T.*", 
                         replacement = "\\1", 
                         x = file_ls), stringsAsFactors = FALSE)
  df$date = as.Date(df$date, "%Y%m%d")
  df$year = lubridate::year(df$date)
  df$month = lubridate::month(df$date)
  return(df)
}

files_vv = enrich_date(files_vv) %>% dplyr::filter(month %in% c(11:12, 1:4)) %>% dplyr::arrange(date)
files_vh = enrich_date(files_vh) %>% dplyr::filter(month %in% c(11:12, 1:4)) %>% dplyr::arrange(date) 
files_lia = enrich_date(files_lia) %>% dplyr::filter(month %in% c(11:12, 1:4))  %>% dplyr::arrange(date)

# define seasons


# make a stars proxy object ----------------------------------------------------
vv_prox = read_stars(files_vv$path, 
                     along = "time", 
                     proxy = TRUE)
vv_prox = stars::st_set_dimensions(.x = vv_prox, which = "time", 
                                   values = files_vv$date)
st_get_dimension_values(vv_prox, "time")
#plot(vv_prox)

# create a bbox for testing availability of data throughout winter ------------- 
bb = st_as_sfc(st_bbox(c(xmin = 10.570, 
                         ymin = 46.781, 
                         xmax = 10.777, 
                         ymax = 46.852), crs = 4326))
bb = st_transform(bb, crs = st_crs(vv_prox))
mapview::mapview(bb)

# subset the stars proxy and plot ----------------------------------------------
vv_prox_sub = vv_prox[bb]
st_dimensions(vv_prox_sub)
class(vv_prox_sub) # still no data here!!
plot(vv_prox_sub, reset = FALSE) # plot reads the data, at resolution that is relevant
plot(bb, add = TRUE, lwd = .5, border = 'red')

# number of pixels to process with this bbox
ncell(vv_prox_sub)
length(stars::st_get_dimension_values(.x=vv_prox_sub, which = "x"))*
  length(stars::st_get_dimension_values(.x=vv_prox_sub, which = "y"))

