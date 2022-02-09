#! /usr/bin/python3

import sys
import argparse
import xml_utils as u
import datetime
import pdb
from argparse import RawTextHelpFormatter
from collections import defaultdict

##------------------------------------------------------------
##  can be called with:
##    xml_obj_stats -f *.xml dirs
##------------------------------------------------------------
def main (argv) :
	parser = argparse.ArgumentParser(description='\nPrint combined stats for all input files/directory.\n\texample: xml_obj_stats  xxx_*_xml outputdir',
		formatter_class=RawTextHelpFormatter)
    # parser.formatter.max_help_position = 50
	parser.add_argument ('files', nargs='+')
	parser.add_argument ('-filetype', '--filetype', default="chips",
		help='type of xml file: <images,chips,faces,pairs,embeds> .')
	parser.add_argument ('-db', '--db', 
		help='file with image exif and details.')
	parser.add_argument ('-write', '--write', default="",
		action="store_true",
		help='write stats into file stats_*_<currentDate> .')
	parser.add_argument ('-p', '--print_all_labels', default=False,
		action="store_true",
		help='print ordered list of filenames.')
	parser.add_argument ('-l', '--ls', default="",
		action="store_true",
		help='print ordered list of filenames.')
	parser.add_argument ('-v', '--verbosity', type=int, default=1,
		choices=[0, 1, 2, 3], help='2 will generate count per label')
		# choices=[0, 1, 2, 3], help=argparse.SUPPRESS)
		# help="increase output verbosity"
	args = parser.parse_args()
	# print "ls : ", args.ls
	# print "files: ", args.files
	filetypes = ['chips', 'faces', 'pairs', 'images', 'embeds']
	filetype = args.filetype
	if filetype not in filetypes :
		print('unrecognized filetype :', filetype, 'should be one of:', filetypes)
		return

	u.set_verbosity (args.verbosity)
	xml_files = u.generate_xml_file_list (args.files)
	u.get_obj_stats (xml_files, args.db, args.ls, args.filetype, args.verbosity, args.write, args.print_all_labels)

if __name__ == "__main__":
	main (sys.argv)

