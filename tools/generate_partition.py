#! /usr/bin/python3

import sys
import pdb
import argparse
import xml_utils as u
import datetime
from collections import defaultdict
from argparse import RawTextHelpFormatter
# from ordereddefaultdict import OrderedDefaultdict


##------------------------------------------------------------
##  can be called with:
##    partition_files 80 20 -out xxx *.xml dirs
##    generate_folds 5 -out yyy *.xml dirs
##------------------------------------------------------------
def main (argv) :
	parser = argparse.ArgumentParser(description='Partitions objects into x and y percents.\nIf shuffle is set to False, each label will be split as specified.\nIf -group is set, will use db argument to partition after grouped by date.\nx and y can be set to 100 and 0, respectively, for no partitioning (to combine multiple XMLs.)\n\nExample: generate_partition -shuffle False -file faces 80 20 images.xml\n\t generate_partition -group all.csv 75 25 chips.xml',
		formatter_class=RawTextHelpFormatter)
    # parser.formatter.max_help_position = 50
	parser.add_argument ('x', default=80,
		help='Percent of first set.')
	parser.add_argument ('y', default=20,
		help='Percent of second set.')
	parser.add_argument ('input', nargs='+')
	parser.add_argument ('-shuffle', '--shuffle', default=True,
		help='Determines whether all objects are mixed before partition. If set to False, each label wil be split as specified.  Defaults to True.')
	parser.add_argument ('--test_count_minimum', default=0,
		help='Minimum test images per label, overrides partition percentage. Defaults to 0.')
	parser.add_argument ('-image_count_minimum', '--image_count_minimum', default=0,
		help='Minimum number of images per label. Defaults to 0.')
	parser.add_argument ('-image_size_minimum', '--image_size_minimum', default=0,
		help='Minimum size of image. Defaults to 0.')
	parser.add_argument ('-filetype', '--filetype', default="chips",
		help='Type of file to partition. <faces|chips>. Defaults to "chips".')
	parser.add_argument ('-group', '--group_date_db',
		help='Group images with same date and label together before partitioning using csv (\';\' separated) for date/label information.')
	parser.add_argument ('-out', '--output', default="",
		help='Output file basename. Defaults to "part_<date><time>_"')
	parser.add_argument ('-v', '--verbosity', type=int, default=1,
		choices=[0, 1, 2], help=argparse.SUPPRESS)
	u.set_argv (argv)
	args = parser.parse_args()
	verbose = args.verbosity
	### --------------
	#  TODO check & WARN that if shuffle is set, will ignore 
	#    image_count_minimum, test_count_minimum
	### --------------

	### -------------- validate arguments -------- ###
	try:
		x = int (args.x)
	except ValueError:
		print ('Error: number expected for x, got:', args.x)
		return
	try:
		y = int (args.y)
	except ValueError:
		print ('Error: number expected for y, got:', args.y)
		return
	if x + y != 100 :
		print("Error: (x + y) needs to be 100")
		return
	filetypes = ['chips', 'faces']
	filetype = args.filetype
	if filetype not in filetypes :
		print('unrecognized filetype :', filetype, 'should be one of:', filetypes)
		return

	if not args.output :
		args.output = datetime.datetime.now().strftime("part_%Y%m%d_%H%M")
	do_grouping = False
	if args.group_date_db != None :
		do_grouping = True
	if verbose > 2 :
		print()
		print("x: ", x)
		print("y: ", y)
		print("sum: ", x + y)
		if do_grouping :
			print ("------- partitioning grouped by date ------")
			print("group date db: ", args.group_date_db)
		print("output: ", args.output)
		print("input: ", args.input)

	xml_files = u.generate_xml_file_list (args.input)
	u.generate_partitions (xml_files, x, y, args.output, args.shuffle, int(args.image_count_minimum), int(args.test_count_minimum), int (args.image_size_minimum), filetype, do_grouping, args.group_date_db)


if __name__ == "__main__":
	main (sys.argv)

