#!/bin/bash
# get lia file for orbit
# this is only createing a vrt from one lia file
# adjust path_s1a and file_lia to use on other files

# define where to search the lia file
# path_s1a="/mnt/CEPH_PRODUCTS/S1_L1C_TEST/S1-PreProc-Test-v2/T015/EPSG3035/";
path_s1a="$1";

# define the output path
# path_out="/mnt/CEPH_FS_RASDAMAN/VRT/OpenEO_UseCase/T015/"
path_out="$2";

echo "----"
echo "path_s1a: $path_s1a";
echo "path_out: $path_out";

# get one lia file
#file_lia="S1A_IW_GRDH_20141111T171503_015_LIA_eurac";
#echo $file_lia;
# generate file list
files_lia=${path_s1a}"S1A_*_LIA_eurac";
#echo $files_lia;

#echo  ${files_vh[1]};
array_lia=($files_lia);
file_lia=${array_lia[1]};
file_lia=`basename $file_lia`;
echo "this is file_lia: $file_lia";

echo "creating: $path_out$file_lia";
gdalbuildvrt -separate -overwrite ${path_out}${file_lia}.vrt ${path_s1a}${file_lia}




