#! /usr/bin/python3

import sys
import argparse
import xml_utils as u
import datetime
import pdb
from collections import defaultdict

##------------------------------------------------------------
##  can be called with:
##    xml_diff file1 file2
##------------------------------------------------------------
def main (argv) :
	parser = argparse.ArgumentParser(description='\nDiffs two xml face files.\n\n \t example: xml_diff file1 file2',
		formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=50))
    # parser.formatter.max_help_position = 50
	parser.add_argument ('-filetype', '--filetype', default="faces",
		help='type of xml file: <imgs,chips,faces,pairs> .')
	parser.add_argument ('-v', '--verbosity', type=int, default=1,
		choices=[0, 1, 2, 3], help='2 will generate count per label')
		# choices=[0, 1, 2, 3], help=argparse.SUPPRESS)
		# help="increase output verbosity"
	parser.add_argument ('file', nargs=2)
	args = parser.parse_args()
	# print "ls : ", args.ls
	# print "files: ", args.files

	u.set_verbosity (args.verbosity)
	u.diff_face_files (args.file[0], args.file[1])

if __name__ == "__main__":
	main (sys.argv)

