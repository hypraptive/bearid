#! /usr/bin/python3

import sys
import argparse
import xml_utils as u
import datetime
from argparse import RawTextHelpFormatter
from collections import defaultdict

##------------------------------------------------------------
##  used to create 3 new xmls split into 0, 1 and multiple faces
##  
##	usage:
##    xml_group_by_face_count -out glendale xml_files
##------------------------------------------------------------
def main (argv) :
	parser = argparse.ArgumentParser(description='\nWrite xml file for each of zero, one and multi faces.\n\n\tExample: xml_group_by_face_count -out bc2018  bc2018_faces.xml',
		formatter_class=RawTextHelpFormatter)

	parser.add_argument ('files', nargs='+')
	parser.add_argument ('-out', '--output', default="images",
		help='write files using this base name.')
	parser.add_argument ('-v', '--verbosity', type=int, default=1,
		choices=[0, 1, 2, 3], help='')
		# help="increase output verbosity"
	u.set_argv (argv)
	args = parser.parse_args()
	u.set_verbosity (args.verbosity)
	u.set_argv (argv)
	u.set_filetype ('faces')
	verbose = 0
	if verbose > 0:
		print("files: ", args.files)

	#TODO : prevent clobbering previous default output
	# if args.output == 'images' :
		# args.output = u.get_new_filename (args.output)
	u.split_faces_by_count (args.files, args.output)

if __name__ == "__main__":
	main (sys.argv)

