# create files for vito backend
# subset to spatial extent of uc
# use only a couple of dates
# format has to be geotiff with the date in the name

# 20200909: ToDo
# Loading only 4 timeslices -> Get more when working on vito backend
# Spatially Resampling Modis by Hand... should be done on backend



# libs -------------------------------------------------------------------------
library(dplyr)
library(raster)
library(stars)

# load s1a backscatter ---------------------------------------------------------
path_s1a = "/mnt/CEPH_FS_RASDAMAN/VRT/OpenEO_UseCase/T015"
files_s1a = list.files(path = path_s1a, pattern = "VH_VV_eurac.vrt$", full.names = TRUE)
files_s1a = files_s1a[28:31]
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

aoi = st_transform(x = st_as_sfc(aoi), crs = st_crs(backscatter_prox))

# subset on proxy
backscatter_prox = backscatter_prox[aoi]

# fetch the data - only reading the subsetted part!
backscatter = st_as_stars(backscatter_prox)
#plot(backscatter %>% dplyr::slice(time, 1))

# write to disk as single timesteps
for (i in 1:length(files_s1a)) {
  name_out = gsub(pattern = ".vrt", replacement = ".tif", x = basename(files_s1a[[i]]))
  message(name_out)
  path_out = "/home/pzellner@eurac.edu/openeo_uc_data_vito/"
  stars::write_stars(obj = backscatter %>% dplyr::slice(time, i), 
                     dsn = paste0(path_out, name_out), 
                     driver = "GTiff")
  
}


# load lia ---------------------------------------------------------------------
files_lia = list.files(path = path_s1a, pattern = "LIA_eurac.vrt$", full.names = TRUE)
lia_prox = read_stars(.x = files_lia, proxy = TRUE)
# subset on proxy
lia_prox = lia_prox[aoi]
# fetch the data - only reading the subsetted part!
lia = st_as_stars(lia_prox)
# write to disk
name_out = gsub(pattern = ".vrt", replacement = ".tif", x = basename(files_lia))
path_out = "/home/pzellner@eurac.edu/openeo_uc_data_vito/"
stars::write_stars(obj = lia, 
                   dsn = paste0(path_out, name_out), 
                   driver = "GTiff")

# load modis snow --------------------------------------------------------------
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
s1_dates = as.Date(stars::st_get_dimension_values(backscatter, "time"), "%Y-%m-%d")

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
#modis = modis %>% slice("band", 1)

# write to disk
for (i in 1:nrow(files_mod)) {
  name_out = paste0("ERUAC_MODIS_SNOW_", basename(files_mod$path[[i]]))
  message(name_out)
  path_out = "/home/pzellner@eurac.edu/openeo_uc_data_vito/"
  stars::write_stars(obj = modis %>% dplyr::slice(time, i), 
                     dsn = paste0(path_out, name_out), 
                     driver = "GTiff")
  
}

# check readability
read_stars(paste0(path_out, paste0("ERUAC_MODIS_SNOW_", basename(files_mod$path[[i]]))))
read_stars(paste0(path_out, gsub(pattern = ".vrt", replacement = ".tif", x = basename(files_lia))))
read_stars(paste0(path_out, gsub(pattern = ".vrt", replacement = ".tif", x = basename(files_s1a[[1]]))))

