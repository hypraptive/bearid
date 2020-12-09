#! /usr/bin/python3

import sys
import argparse
import xml_utils as u
import datetime
from argparse import RawTextHelpFormatter
from collections import defaultdict

##------------------------------------------------------------
##  convert csv to html to took at images on same date in test
##		and train datasets
##  
##	usage:
##    csv_same_date_html csv_file
##------------------------------------------------------------
def main (argv) :
	parser = argparse.ArgumentParser(description='\nWrite html to display images grouped by day per label',
		formatter_class=RawTextHelpFormatter)

	parser.add_argument ('file')
	parser.add_argument ('-out', '--output', default="same_dates.html",
		help='write files using this base name.')
	parser.add_argument ('-v', '--verbosity', type=int, default=1,
		choices=[0, 1, 2, 3], help='')
		# help="increase output verbosity"
	u.set_argv (argv)
	args = parser.parse_args()
	u.set_verbosity (args.verbosity)
	u.set_argv (argv)
	verbose = 0
	if verbose > 0:
		print("files: ", args.files)

	#TODO : prevent clobbering previous default output
	# if args.output == 'images' :
		# args.output = u.get_new_filename (args.output)
	u.html_same_date_from_csv (args.file, args.output)

if __name__ == "__main__":
	main (sys.argv)

