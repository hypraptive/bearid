#! /bin/bash

if [[ $# -ne 1 ]]; then
	echo ""
	echo "Look for images (jpg,jpeg,png), CR2 (raw) and mov files"
	echo ""
	echo "	Usage:"
	echo "		$0 <dir>"
	echo "	Example:"
	echo "		$0 images_2019"
	echo ""
	exit
fi

err_file='/tmp/errs_xml'
dir_files='/tmp/dir_files'
imgs='/tmp/img_files'
raws='/tmp/raw_files'
movs='/tmp/mov_files'
unknowns='/tmp/unknown_files'

if [ 1 == 1 ]; then
	find $1 -type f > $dir_files
	grep -E -i 'jpg|jpeg|png' $dir_files > $imgs
	grep -E -i 'CR2' $dir_files > $raws
	grep -E -i 'mov' $dir_files > $movs
	grep -E -v -i 'jpg|jpeg|png|CR2|mov' $dir_files > $unknowns
	imgs_cnt=`wc -l $imgs | awk '{ print \$1'}`
	raws_cnt=`wc -l $raws | awk '{ print \$1'}`
	movs_cnt=`wc -l $movs | awk '{ print \$1'}`
	unks_cnt=`wc -l $unknowns | awk '{ print \$1'}`
	echo ""
	echo "$1 has:"
	echo -e "\timages        :$imgs_cnt"
	echo -e "\traw images    :$raws_cnt"
	echo -e "\tvideos        :$movs_cnt"
	echo -e "\tunknons       :$unks_cnt"
fi

exit


