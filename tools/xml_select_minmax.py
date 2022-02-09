#! /usr/bin/python3

import sys
import argparse
import xml_utils as u
import os
from argparse import RawTextHelpFormatter

##----------------------------------------------------------
##  for each label that has more than the mininum count, select the 
##  largest subset less than the maxinum count. 
##   writes out to a new xml file.
##----------------------------------------------------------
def main (argv) :
	parser = argparse.ArgumentParser(description='Select a subset if label count falls between min and max.',
		formatter_class=RawTextHelpFormatter)
	parser.add_argument ('image_db')
	parser.add_argument ('min', default=0)
	parser.add_argument ('max', default=0)
	parser.add_argument ('files', nargs='+')
	parser.add_argument ('-o', '-out', '--output')
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
	output_file = 'selected_' + u.current_datetime () + '.xml'
	if args.output : # user specified
		if not os.path.exists (args.output) :
			output_file = args.output
		else :
			print ('output file exists, writing to', output_file)
	u.select_labels_minmax (args.files, args.image_db, args.min, args.max, output_file, filetype)

if __name__ == "__main__":
	main (sys.argv)

