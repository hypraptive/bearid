#! /usr/bin/python

import sys
import argparse
import xml_utils as u
import datetime
import pdb
from collections import defaultdict

##------------------------------------------------------------
##  can be called with:
##    xml_obj_stats -f *.xml dirs
##------------------------------------------------------------
def main (argv) :
	parser = argparse.ArgumentParser(description='\nPrint combined stats for all input files/directory.\n \t example: xml_obj_stats -l xxx_*_xml outputdir',
		formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=50))
    # parser.formatter.max_help_position = 50
	parser.add_argument ('files', nargs='+')
	parser.add_argument ('-filetype', '--filetype', default="chips",
		help='type of xml file: <chips,faces,pairs> .')
	parser.add_argument ('-write', '--write', default="",
		action="store_true",
		help='write stats into file stats_*_<currentDate> .')
	parser.add_argument ('-l', '--ls', default="",
		action="store_true",
		help='print ordered list of filenames.')
	parser.add_argument ('--verbosity', type=int, default=1,
		choices=[0, 1, 2], help=argparse.SUPPRESS)
		# help="increase output verbosity"
	args = parser.parse_args()
	# print "ls : ", args.ls
	# print "files: ", args.files

	xml_files = u.generate_xml_file_list (args.files)
	u.get_obj_stats (xml_files, args.ls, args.filetype, args.verbosity, args.write)

if __name__ == "__main__":
	main (sys.argv)

