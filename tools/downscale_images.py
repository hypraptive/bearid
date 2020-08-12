#! /usr/bin/python3

import sys
import argparse
from argparse import RawTextHelpFormatter
import xml_utils as u
import datetime
from collections import defaultdict

##------------------------------------------------------------
##  can be called with:
##	  
##    extracts bc embeddings to write to new file
##------------------------------------------------------------
def main (argv) :
	parser = argparse.ArgumentParser(description='    Downscale images and writes them to parallel directories.\n    Also write new xml with updated content.\n\n    Example: \n\tdownscale_images -xy 640 480 -replace imageSource imageSourceTiny x.xml',
		formatter_class=RawTextHelpFormatter)
	grp = parser.add_mutually_exclusive_group ()
	parser.add_argument ('files', nargs='+')
	grp.add_argument ('-xy', '--xy_max', nargs=2, 
		help='max x and y of image.')
	grp.add_argument ('-max', '--max_area', default=30000,
		help='max size of image.')
	parser.add_argument ('-replace', '--replace_path', nargs=2, 
		default=['', './'] , help='replace old with new.')
	parser.add_argument ('-v', '--verbosity', type=int, default=1,
		choices=[0, 1, 2, 3], help='')
		# help="increase output verbosity"
	u.set_argv (argv)
	args = parser.parse_args()
	u.set_verbosity (args.verbosity)
	u.set_filetype ('faces')
	verbose = 0
	if verbose > 0:
		print("files: ", args.files)
	if args.xy_max :
		args.max_area = int (args.xy_max[0]) * int (args.xy_max[1])
	# print ('max_area: ', args.max_area)
	# print ('replace_path: ', args.replace_path)
	# print ('replace_path: ', args.replace_path[0], args.replace_path[1])
	for face_xml in args.files :
		u.downscale_face_file (face_xml, args.max_area, args.replace_path)

if __name__ == "__main__":
	main (sys.argv)

