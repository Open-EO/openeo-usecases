# check count of s1a - raw data and vrts for rasdaman
library(dplyr)
library(ggplot2)

# get raw file list ------------------------------------------------------------
# get list of directories
path_base = "/mnt/CEPH_PRODUCTS/S1_L1C_TEST/S1-PreProc-Test-v2"
tracks = list.dirs(path = path_base, full.names = TRUE, recursive = FALSE)
tracks = paste0(tracks, "/", "EPSG3035")

lapply(X = tracks, FUN = dir.exists)

# get list of files per directory
files_ls = lapply(tracks, function(x){
  stopifnot(dir.exists(x))
  tmp = data.frame(path = list.files(path = x, pattern = "eurac$"))
  out = data.frame(path = tmp$path, 
                   track = gsub(pattern = ".*_([0-9]{3})_.*", 
                                replacement = "\\1", 
                                x = tmp$path),
                   polar = gsub(pattern = ".*_(VV|VH|LIA)_.*", 
                                replacement = "\\1", 
                                x = tmp$path), 
                   date = as.Date(gsub(pattern = ".*_(20[0-9][0-9][0-9]{4})T.*", 
                                       replacement = "\\1", 
                                       x = tmp$path), 
                                  format = "%Y%m%d"), 
                   stringsAsFactors = FALSE)
  
})


# get vrt file list ------------------------------------------------------------
path_base_vrt = "/mnt/CEPH_FS_RASDAMAN/VRT/OpenEO_UseCase"
tracks_vrt = list.dirs(path = path_base_vrt, full.names = TRUE, recursive = FALSE)
lapply(X = tracks_vrt, FUN = dir.exists)

files_ls_vrt = lapply(tracks_vrt, function(x){
  stopifnot(dir.exists(x))
  tmp = data.frame(path = list.files(path = x, pattern = "eurac.vrt"))
  out = data.frame(path = tmp$path, 
                   track = gsub(pattern = ".*_([0-9]{3})_.*", 
                                replacement = "\\1", 
                                x = tmp$path),
                   polar = gsub(pattern = ".*_(VH_VV|LIA)_.*", 
                                replacement = "\\1", 
                                x = tmp$path), 
                   date = as.Date(gsub(pattern = ".*_(20[0-9][0-9][0-9]{4})T.*", 
                                       replacement = "\\1", 
                                       x = tmp$path), 
                                  format = "%Y%m%d"), 
                   stringsAsFactors = FALSE)
  
})


# analysis raw -----------------------------------------------------------------
# check if all vh, vv, lia are there
lapply(files_ls, function(x){
  x %>% dplyr::group_by(polar) %>% dplyr::summarise(cnt = n())
})

# plot that all bands are there for every track
files_all = bind_rows(files_ls)
ggplot(data = files_all, aes(x = polar, fill = track)) +
  geom_bar() + 
  ggtitle(paste0("count of ", path_base))

# count of images per track - counting all polarisations vv, vh, lia
ggplot(data = files_all, aes(x = track, fill = track)) +
  geom_bar()+ 
  ggtitle(paste0("count of ", path_base))

# count of images per track - only for vv
ggplot(data = files_all %>% dplyr::filter(polar == "VV"), aes(x = track, fill = track)) +
  geom_bar()+ 
  ggtitle(paste0("count of vv", path_base))

# min max date
files_all %>% group_by(track) %>% summarise(min_date = min(date), 
                                            max_date = max(date))

# timeseries occurnecies
files_all$yr = format(files_all$date, "%Y")
ggplot(data = files_all %>% filter(polar == "VV"), aes(x = date, y = 1, color = yr)) +
  geom_point() +
  scale_y_discrete() +
  facet_grid(track ~ .)+ 
  ggtitle(paste0("timeseries of ", path_base))

  
# analysis vrt -----------------------------------------------------------------
# check that there is always 1 lia file
lapply(files_ls_vrt, function(x){
  #x %>% dplyr::group_by(polar) %>% dplyr::summarise(cnt = n())
  x %>% dplyr::filter(polar == "LIA") %>% nrow()
})

files_all_vrt = bind_rows(files_ls_vrt)
files_all_vrt = files_all_vrt %>% dplyr::filter(polar != "LIA") # remove the 1 LIA file

# plot that all bands are there for every track
ggplot(data = files_all_vrt, aes(x = polar, fill = track)) +
  geom_bar() + 
  ggtitle(paste0("count of ", path_base_vrt))

# count of images per track - counting all polarisations vv, vh, lia
ggplot(data = files_all_vrt, aes(x = track, fill = track)) +
  geom_bar()+ 
  ggtitle(paste0("count of ", path_base_vrt))

# count of images per track - only for vv
ggplot(data = files_all_vrt %>% dplyr::filter(polar == "VH_VV"), aes(x = track, fill = track)) +
  geom_bar()+ 
  ggtitle(paste0("count of vh_vv", path_base_vrt))

# min max date
files_all_vrt %>% group_by(track) %>% summarise(min_date = min(date), 
                                                max_date = max(date))

# timeseries occurnecies
files_all_vrt$yr = format(files_all_vrt$date, "%Y")
ggplot(data = files_all_vrt %>% filter(polar == "VH_VV"), aes(x = date, y = 1, color = yr)) +
  geom_point() +
  scale_y_discrete() +
  facet_grid(track ~ .)+ 
  ggtitle(paste0("timeseries of ", path_base_vrt))

# analysis combined ------------------------------------------------------------
nrow(files_all_vrt)
nrow(files_all %>% dplyr::filter(polar == "VV"))

table(files_all_vrt$track)
table(files_all[files_all$polar == "VV", "track"])

# check that counts are corresponding for track and date
anti_join(files_all_vrt,
          files_all %>% dplyr::filter(polar == "VV"), 
          by = c("track", "date"))
anti_join(files_all %>% dplyr::filter(polar == "VV"), 
          files_all_vrt,
          by = c("track", "date"))

