#! /bin/bash

# g_bc_also_goldtest_db

# create table g_bc_also_goldtest_db as select * from g_faceGold_test_db where label = "bc_also";

bc_labels="
	bc_adeane bc_also bc_amber bc_aurora bc_beatrice bc_bella
	bc_bellanore bc_bracket bc_bruno bc_caramel bc_chestnut 
	bc_cleo bc_clyde bc_coco bc_cross-paw bc_dani-bear 
	bc_diablo bc_fisher bc_flora bc_frank bc_freckles bc_freda 
	bc_freya bc_gary bc_gc bc_glory bc_hoeya bc_jaque 
	bc_kiokh bc_kwatse bc_lenore bc_lillian bc_lil-willy 
	bc_lucky bc_matsui bc_millerd bc_mouse bc_neana bc_no-tail 
	bc_old-girl bc_oso bc_peanut bc_pete bc_pirate 
	bc_pretty-boy bc_river bc_sallie bc_santa bc_shaniqua 
	bc_simoom bc_stella bc_steve bc_teddy-blonde bc_teddy-brown 
	bc_toffee bc_topaz bc_trouble bc_tuna bc_ursa"
bf_labels="
	bf_032 bf_039 bf_045 bf_051 bf_068 bf_083 bf_089 
	bf_093 bf_094 bf_128 bf_130 bf_132 bf_151 bf_153 
	bf_171 bf_201 bf_218 bf_261 bf_263 bf_273 bf_274 
	bf_284 bf_289 bf_293 bf_294 bf_401 bf_402 bf_409 
	bf_410 bf_415 bf_425 bf_435 bf_451 bf_461 bf_469 
	bf_474 bf_477 bf_480 bf_482 bf_489 bf_500 bf_503 
	bf_504 bf_505 bf_510 bf_511 bf_600 bf_602 bf_603 
	bf_604 bf_610 bf_611 bf_613 bf_614 bf_615 bf_634 
	bf_700 bf_708 bf_717 bf_718	bf_719 bf_720 bf_744 
	bf_747 bf_755 bf_775 bf_813 bf_814 bf_818 bf_854 
	bf_856 bf_868 bf_879"

all_labels="$bc_labels $bf_labels"
dataset='test train'
labels='bc_also bc_river bc_lenore'
if [ 1 == 0 ]; then 	
# generate sqlite commands to create train and test table per label
for bear in $all_labels ; do
	for data in $dataset ; do
		main_table="g_faceGold_${data}_db"
		new_table="t_${bear}_gold${data}"
			# --- for creating one new csv for all labels
		echo "DROP TABLE if exists \"${new_table}\" ;"
		echo "create table \"${new_table}\" as select * from ${main_table} where label = \"${bear}\";"
	done
done
fi

if [ 1 == 0 ]; then 	
i=0
echo ".output csv/db_grouped_by_labels.csv"
echo ".header on"
# genate sqlite commands to create one table for all labels.  
# data grouped by label, separated by test and train sets
# useful for looking at nose poses, age, image date distribution in spreadsheet
	for bear in $all_labels ; do
		for data in $dataset ; do
				# --- print label content to screen
			echo ".print"
			echo ".print $bear $data"
			echo "select * from ${main_table} where label = \"${bear}\";"
			if [ $i == 0 ]; then
				i=1
				echo ".header off"
			fi
		done
	done
fi

if [ 1 == 1 ]; then 	
	common_table_all='g_common_all'
	echo -n "drop table if exists $common_table_all ;"
	echo "create table $common_table_all (IMAGE TEXT, LABEL TEXT, DATE TEXT, TEST_TRAIN TEXT);"
	# for bear in bc_beatrice bc_bella ; do
	for bear in $all_labels ; do
		main_table="g_faceGold_${data}_db"
		common_table="t_${bear}_common"
		common_table_test="t_${bear}_common_test"
		common_table_train="t_${bear}_common_train"
		common_table_sorted="t_${bear}_common_sorted"
		train_db="t_${bear}_goldtrain"
		test_db="t_${bear}_goldtest"
		test_dates="t_test_dates_${bear}"
		train_dates="t_train_dates_${bear}"

		echo -n "drop table if exists \'$common_table\' ;"
		echo "create table $common_table (IMAGE TEXT, LABEL TEXT, DATE TEXT, TEST_TRAIN TEXT);"
		echo -n "drop table if exists $test_dates;"
	    echo "create table $test_dates as select distinct date from $test_db;"
		echo -n "drop table if exists $common_table_train;"
	  	echo "create table $common_table_train as select train.image, train.label, train.date, 'train' from $train_db as train join $test_dates as test where train.date = test.date order by train.date;"
		echo -n "drop table if exists $train_dates;"
		echo "create table $train_dates as select distinct date from $common_table_train;"

		echo -n "drop table if exists $common_table_test;"
	  	echo "create table $common_table_test as select test.image, test.label, test.date, 'test' from $test_db as test join $train_dates as train where train.date = test.date order by train.date;"

	    echo "insert into $common_table select * from $common_table_test ;"
	    echo "insert into $common_table select * from $common_table_train ;"

	    # echo "insert into $common_table select test.image, test.label, test.date, 'test' from $test_db as test join $train_db as train where test.date = train.date order by test.date;"
		echo -n "drop table if exists $common_table_sorted ;"
	  	echo "create table $common_table_sorted as select * from $common_table order by date;"
	    echo "insert into $common_table_all select * from $common_table_sorted ;"
		# clean up temp tables
		echo -n "drop table if exists $common_table ;"
		echo -n "drop table if exists $common_table_train;"
		echo -n "drop table if exists $common_table_test;"
		echo -n "drop table if exists $common_table_sorted ;"
		echo -n "drop table if exists $test_dates;"
		echo "drop table if exists $train_dates;"
	done
	csv_file='csv/db_common_dates_by_labels.csv'
	echo ".output $csv_file"
	echo ".header off"
	echo "select * from $common_table_all ;"
	echo ".output"
	echo ".print ... csv table written to $csv_file"
fi

exit

creating csv of all images taken on same day as dates of test set:
for each label
	  % create table bc_beatrice_leak (IMAGE TEXT, LABEL TEXT, DATE TEXT, TEST_TRAIN TEXT);
	- create table AA t_bc_amber_goldtest (done)
	- create table BB (uniq dates in AA) uniq dates of amber train images
	  % create table test_date_bc_beatrice as select distinct date from t_bc_beatrice_goldtest;
	- create table CC (amber_train join BB) amber train images w/ same test dates
	  % insert into bc_beatrice_leak select train.image, train.label, train.date, 'train' from t_bc_beatrice_goldtrain as train join test_date_bc_beatrice as test where train.date = test.date order by train.date;
	- create table DD (uniq dates in CC) uniq dates of joined train images
	  % create table train_date_bc_beatrice as select distinct date from bc_beatrice_leak;
	- add to table EE (DD join AA - removes test dates w/ no train dates)
	  % insert into bc_beatrice_leak select test.image, test.label, test.date, 'test' from t_bc_beatrice_goldtest as test join train_date_bc_beatrice as train where test.date = train.date order by test.date;
	- create new table sorted by date
	  select * bc_beatrice_leak_sort order by date
	  
create table data_leak_check (IMAGE TEXT, LABEL TEXT, DATE TEXT, TEST_TRAIN TEXT);
.output csv/data_leak_check.csv
for each label
	- .print label
	- select * bc_beatrice_leak_sort
	- .print



generate html:

if len (line) == 1 :
    print_label
	label = line[0]
else :
	print '<img src="/home/data/bears'
	print line[0]
	print '"'
	if line[3] == 'train' :
		border_color = 'green'
	else :
		border_color = 'red'
  	print 'width"200" height="300" style="border:5px solid ' + border_color + ';"' alt=" + label + '" >'


# need sting to look like: 
 <img src="/home/data/bears/imageSourceSmall/britishColumbia/melanie_20170828/bc_beatrice/IMG_5056.JPG"
    width"200" height="300" style="border:5px solid green;" alt="beatrice" >

	



#-------------------------------------------------------------------------#  1. set run to echo to verify generated commands without executing
#  2. enable validation of xml files
#  3. ensure that extensions are correct
#  4. set dataset values
#
#  -----------#  assumptions:
#  -----------#   data_set : faceGold_train, faceGold_test
#   faceGold_test.xml 
#   faceGold_testresize.xml 
#   faceGold_testresize_chips.xml 
#   faceGold_testresize_svm.xml 
#   faceGold_train.xml 
#   faceGold_trainresize.xml 
#   faceGold_trainresize_chips.xml 
#   faceGold_trainresize_svm.xml 
#
#   chip file: ${base}resize_faces_chips.xml
#   svm  file: ${base}resize_faces_chips_embeds_svm.xml
#
#  ex rename cmds  : rename -n 's/train_resize/trainresize/' *train_resize*.xml`
#  ex rename cmds  : rename -n 's/chips_embeds_svm/svm/' *svm*xml
#
#   ??  how is xml_svm different from svm ??  
#-------------------------------------------------------------------------conv=~/tools/csv_fr_xml.py
run='echo'
run=
xml_gold=".xml"	# main ext
xml_resize='resize.xml'
xml_chips='resize_faces_chips.xml'
xml_chips='resize_chips.xml'
xml_svm='resize_faces_chips_embeds_svm.xml'
xml_svm='resize_chips_embeds_svm.xml'
xml_svm='resize_svm.xml'

csv_gold=".csv"
csv_resize='resize.csv'
csv_chips='resize_chips.csv'
csv_svm='resize_svm.csv'

gold=''
resize='resize'
chips='resize_chips'
svm='resize_svm'

dataset='test train'
dataset='faceGold_test faceGold_train'

#---------------------------
# check existence of xml file 
#---------------------------
if [ 1 == 1 ]; then
for i in $dataset ; do
	for j in "" $resize $chips $svm; do
		xml=${i}${j}.xml
		echo -n "checking for $xml ... "
		if [ ! -f $xml ]; then
			echo "Failed."
			echo "   Unable to locate $xml" 
		else
			echo "OK."
		fi
	done
done
fi

if [ ! -d sql ]; then
	mkdir sql
fi
if [ ! -d csv ]; then
	mkdir csv
fi

prepend_file () {
	echo $2 > gen_csv_hdr_temp
	cat $1 >> gen_csv_hdr_temp
	mv gen_csv_hdr_temp $1
	# sed '1 s/^/$2\n/' $1
}
#-------- fields of csv tables -----------------# test.csv, train.csv
gold_label="IMAGE;LABEL;DATE;YEAR;MONTH;DAY;SIZE;PHOTO_SOURCE;FACE_SIZE"
# train_resize.csv
resize_label="IMAGE;LABEL;SIZE_RESIZED;ORIG_IMAGE;FACE_SIZE_RESIZED"
# test_resize_chips.csv
chips_label="IMAGE;LABEL;SIZE;ORIG_IMAGE;NOSE_XY;NOSE_X;NOSE_Y"
# test_db.csv
db_label="IMAGE;LABEL;NOSE_X;NOSE_Y;DATE;SIZE_RESIZED;SIZE_ORIG;PHOTO_SOURCE"
# test_resize_svm.csv
svm_label="IMAGE;PREDICT;TRUTH_LABEL;MATCH"

#--------------------------------------------------------------------
# create csv from xml content, add headers  ------------------
#--------------------------------------------------------------------
if [ 1 == 1 ]; then
echo ""
echo "--------------------------------------------------"
echo "... Creating csv from xml content and add headers"
echo "--------------------------------------------------"
for i in $dataset; do
<<COMMENT
COMMENT
	#------- {test,train}.xml -> {test,train}.csv
	csv_file=csv/${i}${gold}.csv 
	xml_file=${i}${xml_gold} 
    dependendies='$csv_file $xml_file'
	echo "... $conv -file faces -out ${csv_file} $xml_file > ${csv_file}.out"
	$run $conv -file faces -out ${csv_file} $xml_file > ${csv_file}.out
	$run prepend_file $csv_file $gold_label
	#------- {test,train}resize.xml -> {test,train}resize.csv
	csv_file=csv/${i}${resize}.csv 
	xml_file=${i}${xml_resize} 
	if [ ! -f $xml_file ]; then
		echo "Error: file $xml_file missing."
		exit
	fi
	echo "... $conv -file derived_faces -out ${csv_file} $xml_file > ${csv_file}.out"
	$run $conv -file derived_faces -out ${csv_file} $xml_file > ${csv_file}.out
	$run prepend_file $csv_file $resize_label
	#------- {test,train}resize_chips.xml -> {test,train}resize_chips.csv
	csv_file=csv/${i}${chips}.csv
	xml_file=${i}${xml_chips} 
	if [ ! -f $xml_file ]; then
		echo "Error: file $xml_file missing."
		exit
	fi
	echo "... $conv -file chips -out ${csv_file} $xml_file > ${csv_file}.out"
	$run $conv -file chips -out ${csv_file} $xml_file > ${csv_file}.out
	$run prepend_file $csv_file $chips_label
	#------- {test,train}resize_svm.xml ->  {test,train}resize_svm.csv
	csv_file=csv/${i}${svm}.csv 
	xml_file=${i}${xml_svm} 
	if [ ! -f $xml_file ]; then
		echo "Error: file $xml_file missing."
		exit
	fi
	echo "... $conv -file svm -out ${csv_file} $xml_file > ${csv_file}.out"
	$run $conv -file svm -out ${csv_file} $xml_file > ${csv_file}.out
	$run prepend_file $csv_file $svm_label
<<COMMENT
COMMENT
done
fi

add_to_file () {
	echo $2 >> $1
	# echo $2
}

#--------------------------------------------------------------------
# generate import table commands --------------
#--------------------------------------------------------------------
if [ 1 == 1 ]; then
echo ""
echo "-----------------------------------------------"
echo "...Generating import table commands" 
echo "-----------------------------------------------"
import_file='sql/import_csv.sql'
$run touch $import_file
	# echo $1 > sql/import_csv.sql
$run add_to_file $import_file '.mode csv'
$run add_to_file $import_file ".separator ';'"
for i in $dataset; do
	for j in "" $resize $chips $svm; do
		echo "... add_to_file $import_file \"drop table if exists ${i}${j};\""
		$run add_to_file $import_file "drop table if exists ${i}${j};"
		echo "... add_to_file $import_file \".import csv/${i}${j}.csv ${i}${j}\""
		$run add_to_file $import_file ".import csv/${i}${j}.csv ${i}${j}"
	done
done
echo ""
fi

#--------------------------------------------------------------------# generate sql to build uniq svm,chips ----------------------# i.e combine multiple faces of one image together
# select e.col1, e.col2 from easdfdsf e
#--------------------------------------------------------------------if [ 1 == 1 ]; then
echo "...Generating sql commands to build uniq svm and chips"
gen_uniq_file="sql/gen_uniq_imgs.sql"
rm -f $gen_uniq_file
echo "...Generating $gen_uniq_file"
touch $gen_uniq_file
add_to_file $gen_uniq_file "-- This file is generated, any modifications will be overwritten"
for i in $dataset; do 
	add_to_file $gen_uniq_file "-- create table of combined duplicates"
	add_to_file $gen_uniq_file "drop table if exists t_${i}_svm_dups;"
	add_to_file $gen_uniq_file "create table t_${i}_svm_dups (IMAGE TEXT, PREDICT TEXT, TRUTH_LABEL TEXT, MATCH TEXT, PREDICTS TEXT, MATCHES TEXT, DUP_COUNT INTEGER);"
	add_to_file $gen_uniq_file "insert into t_${i}_svm_dups select *, group_concat (PREDICT, ' '), group_concat (MATCH, ' '), count(*) c from ${i}resize_svm group by IMAGE having c > 1;"
	add_to_file $gen_uniq_file "drop table if exists t_${i}_svm_singles;"
	add_to_file $gen_uniq_file "create table t_${i}_svm_singles as select *, count(*) c from ${i}resize_svm group by IMAGE having c == 1;"
	add_to_file $gen_uniq_file "drop table if exists g_${i}_svm;"
	add_to_file $gen_uniq_file "create table g_${i}_svm (IMAGE TEXT, PREDICT TEXT, TRUTH_LABEL TEXT, MATCH TEXT);"
	add_to_file $gen_uniq_file "insert into g_${i}_svm select IMAGE, PREDICTS, TRUTH_LABEL, MATCHES from t_${i}_svm_dups;"
	add_to_file $gen_uniq_file "insert into g_${i}_svm select IMAGE, PREDICT, TRUTH_LABEL, MATCH from t_${i}_svm_singles;"
	add_to_file $gen_uniq_file "drop table t_${i}_svm_dups;"
	add_to_file $gen_uniq_file "drop table t_${i}_svm_singles;"
	add_to_file $gen_uniq_file "drop table if exists ${i}resize_chips_orig;"
	add_to_file $gen_uniq_file "alter table ${i}resize_chips rename to ${i}resize_chips_orig;"
	# '*' surrounded by spaces expands to all files in dir.
	add_to_file $gen_uniq_file "create table ${i}resize_chips as select ${i}resize_chips_orig.* from ${i}resize_chips_orig where image like '%chip_0%';"
	# add_to_file $gen_uniq_file "where image like '%chip_0%';"

done

fi

#--------------------------------------------------------------------
# generate sql for final test,train tables ------------------------
#--------------------------------------------------------------------
if [ 1 == 1 ]; then
echo "Generating sql commands to build final test,train tables"
gen_db_file="sql/gen_db.sql"
rm -f $gen_db_file
touch $gen_db_file
add_to_file $gen_db_file "-- This file is generated, any modifications will be overwritten\n"
for i in $dataset; do 
	# --- combine faceresize with chips
	add_to_file $gen_db_file "-- combine faceresize with chips to get:"
	add_to_file $gen_db_file "-- IMAGE, LABEL, ORIG_IMAGE, SIZE_RESIZED, FACE_SIZE_RESIZED, "
	add_to_file $gen_db_file "-- NOSE_X, NOSE_Y"
	add_to_file $gen_db_file "DROP TABLE if exists t_${i}_faceresize_chips;"
	add_to_file $gen_db_file "CREATE TABLE t_${i}_faceresize_chips AS "
	add_to_file $gen_db_file "SELECT ${i}resize.IMAGE, ${i}resize.LABEL, ${i}resize.ORIG_IMAGE, ${i}resize.SIZE_RESIZED, face_size_resized, NOSE_X, NOSE_Y"
	add_to_file $gen_db_file "FROM ${i}resize LEFT JOIN ${i}resize_chips"
	add_to_file $gen_db_file "ON ${i}resize.IMAGE = ${i}resize_chips.ORIG_IMAGE;"
	# --- combine (faceresize & chips) with orig face
	add_to_file $gen_db_file "-- combine (faceresize & chips) with orig face to get:"
	add_to_file $gen_db_file "-- IMAGE, LABEL, NOSE_X, NOSE_Y, DATE, YEAR, MONTH, SIZE, SIZE_RESIZED, "
	add_to_file $gen_db_file "-- PHOTO_SOURCE, FACE_SIZE, FACE_SIZE_RESIZED"
	add_to_file $gen_db_file "DROP TABLE if exists t_${i}_faces_chips;"
	add_to_file $gen_db_file "CREATE TABLE t_${i}_faces_chips AS "
	add_to_file $gen_db_file "SELECT t_${i}_faceresize_chips.IMAGE, t_${i}_faceresize_chips.LABEL, NOSE_X, NOSE_Y, DATE, YEAR, MONTH, t_${i}_faceresize_chips.SIZE_RESIZED, ${i}.SIZE, PHOTO_SOURCE, FACE_SIZE, FACE_SIZE_RESIZED"
	add_to_file $gen_db_file "FROM t_${i}_faceresize_chips LEFT JOIN ${i}"
	add_to_file $gen_db_file "ON t_${i}_faceresize_chips.ORIG_IMAGE = ${i}.IMAGE;"
	add_to_file $gen_db_file ""
	# --- combine (face & faceresize & chips) with svm 
	add_to_file $gen_db_file "-- combine (face & faceresize & chips) with svm to get:"
	add_to_file $gen_db_file "-- IMAGE, LABEL, NOSE_X, NOSE_Y, DATE, YEAR, MONTH, SIZE, SIZE_RESIZED, "
	add_to_file $gen_db_file "-- PHOTO_SOURCE, FACE_SIZE, FACE_SIZE_RESIZED, LABEL_RESULT, MATCH"
	add_to_file $gen_db_file "drop table if exists g_${i}_db;"
	add_to_file $gen_db_file "create table g_${i}_db as"
	add_to_file $gen_db_file "select t_${i}_faces_chips.IMAGE, LABEL, NOSE_X, NOSE_Y, DATE, YEAR, MONTH, SIZE_RESIZED, SIZE, PHOTO_SOURCE, FACE_SIZE, FACE_SIZE_RESIZED,"
	add_to_file $gen_db_file "g_${i}_svm.PREDICT, g_${i}_svm.MATCH"
	add_to_file $gen_db_file "from t_${i}_faces_chips LEFT JOIN g_${i}_svm"
	add_to_file $gen_db_file "on t_${i}_faces_chips.IMAGE = g_${i}_svm.IMAGE;"
	add_to_file $gen_db_file ""
	add_to_file $gen_db_file "-- drop  table t_${i}_faceresize_chips;"
	add_to_file $gen_db_file "-- drop table t_${i}_faces_chips;"
done

fi
