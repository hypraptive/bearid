#! /usr/bin/python3

import sys
import argparse
import xml_utils as u
import datetime
from argparse import RawTextHelpFormatter
from collections import defaultdict

##------------------------------------------------------------
##  can be called with:
##	  
##    write bc and bf face images to separate files
##------------------------------------------------------------
def main (argv) :
	parser = argparse.ArgumentParser(description='write faces from different locale to different xmls.',
		formatter_class=RawTextHelpFormatter)
	parser.add_argument ('files', nargs='+')
	parser.add_argument ('-out', '--output', default=None,
		help='Output file basename. Defaults to <filetype>')
	parser.add_argument ('-filetype', '--filetype', default="chips",
		help='type of xml file: <chips,faces,embeds> .')
	parser.add_argument ('-v', '--verbosity', type=int, default=1,
		choices=[0, 1, 2, 3], help='')
		# help="increase output verbosity"
	u.set_argv (argv)
	args = parser.parse_args()
	u.set_verbosity (args.verbosity)
	filetypes = ['chips', 'faces', 'embeds']
	filetype = args.filetype
	if filetype not in filetypes :
		print('unrecognized filetype :', filetype, 'should be one of:', filetypes)
		return
	u.set_filetype (filetype)
	verbose = 0
	if verbose > 0:
		print("files: ", args.files)
	if args.output is None:
		args.output = filetype
	u.split_objects_by_locales (args.files, args.output, args.filetype)

if __name__ == "__main__":
	main (sys.argv)

