# files are located here:
# /mnt/CEPH_PRODUCTS/S1_L1C_TEST/S1-PreProc-Test-v2/
# every orbit has its folder:
# - T015/EPSG3035
# - T117/EPSG3035
# Change the path to the according folder by first command line input (path_s1a)
# Change the path to the according output folder by seconc command line input (path_out)
# A file list of the VH files will be created
# In the loop:
# The VH file list is the input.
# To get the according VV file VH is replaced by VV
# A vrt is built using the path to VV and VH
# The vrt is written to the location where this script is called.
# created: 12.11.2019, pzellner

# give input dir as command line argument 1
# path_s1a="/mnt/CEPH_PRODUCTS/S1_L1C_TEST/S1-PreProc-Test-v2/T015/EPSG3035/";
path_s1a="$1"

# give output dir as command line argument 2
# path_out="/mnt/CEPH_FS_RASDAMAN/VRT/OpenEO_UseCase/T015/"
path_out="$2"

# display the paths
echo "input path:  $path_s1a"
echo "output path: $path_out";

#files_vh=(S1A_*_VH_eurac);
#echo $files_vh;

# generate file list
files_vh=${path_s1a}"S1A_*_VH_eurac";
echo $files_vh;

#exit 0

# loop through files and generate .vrt containing vv and vh
for i in ${files_vh[@]}
do
	echo "-----"
	#echo ${i};
	#file_base="${i:0:31}";
	#file_base="${i:64:96}";
	file_base="${i:0:95}";
	#echo $file_base;
	file_vh=${file_base}"_VH_eurac";
	file_vv=${file_base}"_VV_eurac";
	file_out=${file_base}"_VH_VV_eurac";
	file_out=$(basename $file_out)
	#echo $file_out
	#if [ ! "$file_vh" ] || [ ! "$file_vv" ];
	#then
	#	echo "SKIPPING: "${file_vh}" or "${file_vv}" is missing! ";
	#	continue;
	#fi
	echo ${file_vh}" + "${file_vv}" = "${path_out}${file_out};
	gdalbuildvrt -separate -overwrite ${path_out}${file_out}.vrt ${file_vh} ${file_vv} 
done



