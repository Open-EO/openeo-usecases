# check count of s1a

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

# check if all vh, vv, lia are there
lapply(files_ls, function(x){
  x %>% dplyr::group_by(polar) %>% dplyr::summarise(cnt = n())
})

# plot that all bands are there for every track
files_all = bind_rows(files_ls)
ggplot(data = files_all, aes(x = polar, fill = track)) +
  geom_bar()

# count of images per track
ggplot(data = files_all, aes(x = track, fill = track)) +
  geom_bar()

# min max date
files_all %>% group_by(track) %>% summarise(min_date = min(date), 
                                            max_date = max(date))

# timeseries occurnecies
files_all$yr = format(files_all$date, "%Y")
ggplot(data = files_all %>% filter(polar == "VV"), aes(x = date, y = 1, color = yr)) +
  geom_point() +
  scale_y_discrete() +
  facet_grid(track ~ .)
  
