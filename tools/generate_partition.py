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
	desc = 'Partitions each label into into x and y percents.  \
x and y can be set to 100 and 0, \n\
respectively, to combine multiple XMLs together.\n\n\
Example: ' + prog_name + ' 80 20 images.xml\n \
\t ' + prog_name + ' -grouping_duration 1 -db videos.csv 75 25 chips.xml'

# If -grouping_duration is set, will use date information either\
# from -db file or in the object data. \
# To group by days, use -grouping_duration 24.\n \
	parser = argparse.ArgumentParser(description=desc, formatter_class=RawTextHelpFormatter)
    # parser.formatter.max_help_position = 50
	group = parser.add_mutually_exclusive_group()
	parser.add_argument ('x', type=int, default=80,
		help='Percent of first set.')
	parser.add_argument ('y', type=int, default=20,
		help='Percent of second set.')
	parser.add_argument ('input', nargs='+',
		help='xml files and directories.  All xmls under each specified directory will be included. ')
	filetype_help = 'Type of input file. Should be one of ' + filetypes_str + 'Defaults to "chips".'
	parser.add_argument ('-filetype', '--filetype', default="chips",
		help=filetype_help)
	group.add_argument ('-by_label', '--by_label', action='store_true',
		help='All images a label will be togther in one partition.')
	group.add_argument ('-grouping_duration', '--grouping_duration',
		help='Group images within specified hour duration together before partitioning. Requires date time information from xml or via csv specified with -db.')
	parser.add_argument ('-db', '--db', default="",
		help='csv (\';\' separated) for date/label information.')
	parser.add_argument ('-out', '--output', default="",
		help='Output file basename. Defaults to "part_<date><time>_"')
	parser.add_argument ('-v', '--verbosity', type=int, default=1,
		choices=[0, 1, 2], help=argparse.SUPPRESS)
	u.set_argv (argv)
	args = parser.parse_args()
	verbose = args.verbosity
	# pdb.set_trace ()
	### -------------- validate arguments -------- ###
	split_type = None
	split_arg = None
	if args.by_label is not False :
		print ("splitting by label.")
		split_type = 'label'
		split_arg = None
	elif args.grouping_duration is not None :
		split_type = 'grouping_duration'
		split_arg = args.grouping_duration
	elif args.x + args.y != 100 :
		print("Error: (x + y) needs to be 100")
		return
	filetype = args.filetype
	if filetype not in filetypes :
		print('unrecognized filetype :', filetype, 'should be one of:', filetypes_str)
		return
	if not args.output :
		args.output = datetime.datetime.now().strftime("part_%Y%m%d_%H%M")
	if verbose > 2 :
		print()
		print("x: ", args.x)
		print("y: ", args.y)
		print("sum: ", args.x + args.y)
		if args.grouping_duration :
			msg = "------- images per label grouped in ' + args.grouping_duration + '-hr windows ------"
			print (msg)
		if args.db != None :
			print("db: ", args.db)
		print("output: ", args.output)
		print("input: ", args.input)

	u.set_verbosity (args.verbosity)
	xml_files = u.generate_xml_file_list (args.input)
	# pdb.set_trace ()
	u.generate_partitions (xml_files, args.x, args.output, split_type, split_arg, args.db, filetype)

if __name__ == "__main__":
	main (sys.argv)

