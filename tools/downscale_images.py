#! /usr/bin/python3

import sys
import argparse
import xml_utils as u
import datetime
from collections import defaultdict

##------------------------------------------------------------
##  can be called with:
##	  
##    extracts bc embeddings to write to new file
##------------------------------------------------------------
def main (argv) :
	parser = argparse.ArgumentParser(description='Downscale images, writes them to parallel \n\tdirectories and write new xml with updated content.',
		formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=50))
	parser.add_argument ('files', nargs='+')
	parser.add_argument ('-x_max', '--x_max', default=1500,
		help='max width of image, defaults to 1500.')
	parser.add_argument ('-y_max', '--y_max', default=2000,
		help='max heigth of image, defaults to 2000.')
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

	for face_xml in args.files :
		u.downscale_face_file (face_xml)

if __name__ == "__main__":
	main (sys.argv)

