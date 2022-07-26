#! /usr/bin/python3

import sys
import pdb
import os
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
	prog_name = os.path.basename(__file__)
	filetypes = ['chips', 'faces', 'video_chips']
	filetypes_str = u.filetypes_to_str (filetypes)
	# pdb.set_trace ()
	desc = 'Creates subsets based on specified criteria.\n\nExample: ' + prog_name + ' -years 2018 2022 -file video_chips vchips.xml\n\t ' + prog_name + ' -image_percent 5 vchips.xml\n\t ' + prog_name + ' -label_minmax 60 125 chips.xml'
	parser = argparse.ArgumentParser(description=desc, formatter_class=RawTextHelpFormatter)
    # parser.formatter.max_help_position = 50
	group = parser.add_mutually_exclusive_group()
	parser.add_argument ('input', nargs='+')
	# do this in xml_split since no x y are required
	group.add_argument ('-pattern', '--pattern', 
		help='partition using specified patterns in file to match anywhere in image path')
	group.add_argument ('-years', '--years', nargs=2, type=int,
		help='partition by each year specified in argument, inclusive.  Requires date information (in chip or in csv')
	group.add_argument ('-list', '--list',
		help='partition using specified list in file to match name.')
	group.add_argument ('-label_minmax', '--label_minmax', nargs=2, type=int,
		help='Extract labels which have at least the mininum count of images. Labels with image counts great than the max will be capped at max count. 0 can be used specify no value, e.g. -label_minmax 50 0 to set mininum to 50 and no upper limit.')
	# group.add_argument ('-label_video_minmax', '--label_video_minmax', nargs=2, type=int,
		# help='Extract labels which have at least the mininum count of images. Labels with image counts great than the max will be capped at max count. 0 can be used specify no value, e.g. -label_video_minmax 50 0 to set mininum to 50 and no upper limit.')
	group.add_argument ('-video_image_percent', '--video_image_percent',
		type=int,
		help='Specifies percent of images to extract per videoa.  Requires date time information either in object of via -db option.')
	group.add_argument ('-video_image_count', '--video_image_count',
		type=int,
		help='Specifies number of images to extract per videoa.  Requires date time information either in object of via -db option.')
	group.add_argument ('-labels', '--labels', nargs='+', 
		help='Extract images with listed labels')
	# parser.add_argument ('-grouping_duration', '--grouping_duration', nargs=1, type=int,
		# help='Specifies the number of hours to use for grouping.  Requires date time information either in object of via -db option.')
	parser.add_argument ('-ppath', '--parent_path', default='/data/bears/',
		help='path to strip when matching filenames.')
	parser.add_argument ('-db', '--db',
		help='csv (\';\' separated) for date/label information.')
	filetype_help = 'Type of input file(s). Should be one of ' + filetypes_str + 'Defaults to "chips".'
	parser.add_argument ('-filetype', '--filetype', default="chips",
		help=filetype_help)
	parser.add_argument ('-out', '--output', default="",
		help='Output file basename. Defaults to "subset_<date><time>_"')
	parser.add_argument ('-v', '--verbosity', type=int, default=1,
		choices=[0, 1, 2], help=argparse.SUPPRESS)
	u.set_argv (argv)
	args = parser.parse_args()
	verbose = args.verbosity
	args1 = vars(args)
	### -------------- validate arguments -------- ###
	extract_type = None
	extract_arg = None
	if args.pattern :
		extract_type = 'pattern'
		extract_arg = args.pattern
		outfile = datetime.datetime.now().strftime("x_pattern_%Y%m%d_%H%M.xml")
	elif args.list is not None:
		extract_type = 'list'
		extract_arg = args.list
		outfile = datetime.datetime.now().strftime("x_list_%Y%m%d_%H%M.xml")
	elif args.years is not None:
		extract_type = 'years'
		extract_arg = args.years
		outfile = datetime.datetime.now().strftime("x_years_%Y%m%d_%H%M.xml")
	elif args.label_minmax :
		extract_type = 'label_minmax'
		extract_arg = args.label_minmax
		outfile = datetime.datetime.now().strftime("x_labelminmax_%Y%m%d_%H%M.xml")
	elif args.label_video_minmax :
		extract_type = 'label_video_minmax'
		extract_arg = args.label_video_minmax
		outfile = datetime.datetime.now().strftime("x_videominmax_%Y%m%d_%H%M.xml")
	elif args.video_image_percent :
		extract_type = 'video_image_percent'
		extract_arg = args.video_image_percent
		outfile = datetime.datetime.now().strftime("x_videosubset_%Y%m%d_%H%M.xml")
	elif args.video_image_count :
		extract_type = 'video_image_count'
		extract_arg = args.video_image_count
		outfile = datetime.datetime.now().strftime("x_videocap_%Y%m%d_%H%M.xml")
	elif args.labels :
		extract_type = 'labels'
		extract_arg = args.labels
		outfile = datetime.datetime.now().strftime("x_labels_%Y%m%d_%H%M.xml")
	filetypes = ['chips', 'faces', 'video_chips']
	filetype = args.filetype
	if filetype not in filetypes :
		print('unrecognized filetype :', filetype, 'should be one of:', filetypes)
		return
	if extract_type is None :
		print ('No action requested.  Please specify an extract option.\n')
		return
	if not args.output :
		args.output = outfile
	if verbose > 2 :
		print()
		print ('extract type:', extract_type)
		print ('extract arg:', extract_arg)
		if args.group_date_db != None :
			print("group date db: ", args.group_date_db)
		print("output: ", args.output)
		print("input: ", args.input)

	u.set_verbosity (args.verbosity)
	xml_files = u.generate_xml_file_list (args.input)
	# pdb.set_trace ()
	u.extract_subsets (xml_files, args.output, extract_type, extract_arg, args.db, args.parent_path, filetype)


if __name__ == "__main__":
	main (sys.argv)

