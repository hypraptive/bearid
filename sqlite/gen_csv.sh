#! /bin/bash

conv=~/tools/csv_fr_xml.py
run='echo'
run=
xml_gold=".xml"
xml_resize='resize.xml'
xml_chips='resize_faces_chips.xml'
xml_svm='resize_faces_chips_embeds_svm.xml'

csv_gold=".csv"
csv_resize='resize.csv'
csv_chips='resize_chips.csv'
csv_svm='resize_svm.csv'

gold=''
resize='resize'
chips='resize_chips'
svm='resize_svm'


# check existence of xml file 
if [ 1 == 0 ]; then
for i in test train; do
	for j in "" $resize $chips $svm; do
		xml=${i}${j}.xml
		echo "checking for $xml ... "
		if [ ! -f $xml ]; then
			echo "   Unable to locate $xml" 
		fi
	done
done
fi

prepend_file () {
	echo $2 > gen_csv_hdr_temp
	cat $1 >> gen_csv_hdr_temp
	mv gen_csv_hdr_temp $1
	# sed '1 s/^/$2\n/' $1
}
#-------- fields of csv tables -------------------
# test.csv, train.csv
gold_label="IMAGE;LABEL;DATE;YEAR;MONTH;DAY;SIZE;PHOTO_SOURCE;FACE_SIZE"
# train_resize.csv
resize_label="IMAGE;LABEL;SIZE_RESIZED;ORIG_IMAGE;FACE_SIZE_RESIZED"
# test_resize_chips.csv
chips_label="IMAGE;LABEL;SIZE;ORIG_IMAGE;NOSE_XY;NOSE_X;NOSE_Y"
# test_db.csv
db_label="IMAGE;LABEL;NOSE_X;NOSE_Y;DATE;SIZE_RESIZED;SIZE_ORIG;PHOTO_SOURCE"
# test_resize_svm.csv
svm_label="IMAGE;PREDICT;TRUTH_LABEL;MATCH"

# create csv from xml content, add headers  --------------------
if [ 1 == 0 ]; then
for i in test train; do
<<COMMENT
COMMENT
	#------- {test,train}.xml -> {test,train}.csv
	csv_file=csv/${i}${gold}.csv 
	xml_file=xml/${i}${xml_gold} 
	ls $xml_file
	$run $conv -file faces -out ${csv_file} $xml_file > ${csv_file}.out
	prepend_file $csv_file $gold_label
	#------- {test,train}resize.xml -> {test,train}resize.csv
	csv_file=csv/${i}${resize}.csv 
	xml_file=xml/${i}${xml_resize} 
	ls $xml_file
	$run $conv -file derived_faces -out ${csv_file} $xml_file > ${csv_file}.out
	prepend_file $csv_file $resize_label
	#------- {test,train}resize_chips.xml -> {test,train}resize_chips.csv
	csv_file=csv/${i}${chips}.csv
	xml_file=xml/${i}${xml_chips} 
	ls $xml_file
	$run $conv -file chips -out ${csv_file} $xml_file > ${csv_file}.out
	prepend_file $csv_file $chips_label
	#------- {test,train}resize_svm.xml ->  {test,train}resize_svm.csv
	csv_file=csv/${i}${svm}.csv 
	xml_file=xml/${i}${xml_svm} 
	ls $xml_file
	$run $conv -file svm -out ${csv_file} $xml_file > ${csv_file}.out
	prepend_file $csv_file $svm_label
<<COMMENT
COMMENT
done
fi

add_to_file () {
	echo $2 >> $1
	# echo $2
}

# generate import table commands ----------------
if [ 1 == 0 ]; then
import_file='sql/import_csv.sql'
touch $import_file
	# echo $1 > sql/import_csv.sql
add_to_file $import_file '.mode csv'
add_to_file $import_file ".separator ';'"
for i in train test; do
	for j in "" $resize $chips $svm; do
		add_to_file $import_file "drop table if exists ${i}${j};"
		add_to_file $import_file ".import csv/${i}${j}.csv ${i}${j}"
	done
done
fi

# generate sql to build uniq svm,chips ------------------------
# i.e combine multiple faces of one image together
# select e.col1, e.col2 from easdfdsf e
if [ 1 == 0 ]; then
gen_uniq_file="sql/gen_uniq_imgs.sql"
rm -f $gen_uniq_file
echo "generating $gen_uniq_file"
touch $gen_uniq_file
add_to_file $gen_uniq_file "-- This file is generated, any modifications will be overwritten"
for i in test train; do 
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

# generate sql for final test,train tables --------------------------

if [ 1 == 1 ]; then
gen_db_file="sql/gen_db.sql"
rm -f $gen_db_file
touch $gen_db_file
add_to_file $gen_db_file "-- This file is generated, any modifications will be overwritten\n"
for i in test train; do 
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
