#! /usr/bin/python3

import sys
import argparse
import xml_utils as u
import datetime
from argparse import RawTextHelpFormatter
from collections import defaultdict

##------------------------------------------------------------
##  takes chip or image xml and add creation datetime from exif data.
##	  
##    writes out to new file with same base name
##------------------------------------------------------------
def main (argv) :
	parser = argparse.ArgumentParser(description='add dateTime string to original images.',
		formatter_class=RawTextHelpFormatter)
	parser.add_argument ('files', nargs='+')
	parser.add_argument ('-filetype', '--filetype', default="chips",
		help='Type of input file <images|faces|chips>. Defaults to "chips".')
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

	filetypes = ['images', 'chips', 'faces']
	filetype = args.filetype
	if filetype not in filetypes :
		print('unrecognized filetype :', filetype, 'should be one of:', filetypes)
		return
	u.add_images_datetime (args.files, filetype)

if __name__ == "__main__":
	main (sys.argv)

