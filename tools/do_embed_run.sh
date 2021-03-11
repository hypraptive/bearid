#! /bin/bash


echo "arg coount: $#"

if [[ $# -ne 5 ]]; then
    echo ""
    echo "Generate chips, train embed and run test by specifying eye loc and padding."
    echo ""
    echo "  Usage:"
    echo "      do_bearembed <padding> <eye_percent> <dir_prefix> <tet_xml>+ <train_xml>"
    echo "  Example:"
    echo "      do_bearembed -.24 36 polarg polar_gold_faces_20.xml polar_gold_faces_80.xml"
    echo "		   will generate polarg_eyes36pad-.24/chips_polar_gold_faces_20_eyes36pad-.24.xml"
    echo "		        and      polarg_eyes36pad-.24/chips_polar_gold_faces_80_eyes36pad-.24.xml"
    echo ""
    exit
fi


run_cmd=""
function do_cmd {
	echo $@
	$@
}

function echo_stderr {
	echo "$@" >&2
}

eyes=$1
padding=$2
prefix=$3
test_xml=$4
train_xml=$5
options=e${eyes}_p${padding}
run_name=${prefix}_${options}
gc_out=out/gc_${run_name}.out
dat=bearembed_${run_name}
run_dir=${run_name}
test_base=${test_xml%%.*}
test_file=${run_name}/chips_${test_base}_${options}.xml
train_base=${train_xml%%.*}
train_file=${run_name}/chips_${train_base}_${options}.xml
dat_file=bearembed_${run_name}.dat
train_out=out/be_train_${run_name}.out
test_out=out/be_test_${run_name}.out
files_txt=${run_dir}/files.txt
html_file=chips_${run_dir}.html
pair_file=${prefix}_pairs_${options}.xml

# cmd="/home/mary/tools/gen_chips.sh $@ > $gc_out"

echo "... generating chips... "
cmd="/home/mary/tools/bearchip --root /data/ZooBears/ --chipdir ${run_dir} --output ${test_file} --padding ${padding} --eyes .62 .${eyes} .38 .${eyes} $test_xml"
echo $cmd
$cmd
cmd="/home/mary/tools/bearchip --root /data/ZooBears/ --chipdir ${run_dir} --output ${train_file} --padding ${padding} --eyes .62 .${eyes} .38 .${eyes} $train_xml"
echo $cmd
$cmd
echo "... Extracting chips filenames"
cmd="/home/mary/tools/xml_to_files.py --out $files_txt $train_file"
$cmd

echo "... Writing html file"
cmd="/home/mary/tools/html_from_list.py --out $html_file $files_txt"
$cmd


cmd="/bin/rm rand_sync rand_sync_"
echo "$cmd"
$cmd
cmd="/home/mary/tools/bearembed --output ${dat_file} --train ${train_file} > ${train_out}"
echo "$cmd"
$cmd

echo_stderr " "
cmd="cp andeang_pairs_230.xml ${pair_file}"
echo_stderr $cmd
echo_stderr " "
cmd="vi ${pair_file} ${test_file}"
echo_stderr $cmd
echo_stderr " "
cmd="/home/mary/tools/bearembed --bn --test ${dat_file} --pair ${pair_file} > ${test_out}"
echo_stderr $cmd

exit







echo "... Using padding of $padding"
echo "... Using eyes set to $eyes %"
features=eyes${eyes}pad${padding}
dirname=${dir_prefix}_${features}

for (( i = 4; i <= $#; i++ )) 
do
	facefile=${!i}
	echo "facefile = $facefile "
	facefile_name=${facefile%%.*}
	xml_file=${dirname}/chips_${facefile_name}_${features}.xml 
	files_txt=${dirname}/files.txt
	html_file=chips_${dirname}.html

	echo "... Generating chips"
	cmd="/home/mary/tools/bearchip --root /data/ZooBears/ --chipdir $dirname --output ${xml_file} --padding ${padding} --eyes .62 .${eyes} .38 .${eyes} $facefile"
	do_cmd $cmd
done



