#! /usr/bin/python3

import sys
import argparse
import xml_utils as u
import datetime
import os
from argparse import RawTextHelpFormatter
from collections import defaultdict

##------------------------------------------------------------
##  generate csv of distances between all permutations of two
##  embedding files.
##  
##	usage:
##    csv_embed_distances.py -out e_dist.csv e_test.xml e_train.xml 
##------------------------------------------------------------
def main (argv) :
	parser = argparse.ArgumentParser(description='\nGenerate CSV of distances for all permutations of two input embedding files.\n\n \tExample: ' + os.path.basename (argv[0]) + ' -out e_dist.csv  embed1.xml embed2.xml',
		formatter_class=RawTextHelpFormatter)
	parser.add_argument ('embed1')
	parser.add_argument ('embed2')
	parser.add_argument ('-out', '--output', default="e_dist.csv",
		help='specify csv output file.')
	parser.add_argument ('-v', '--verbosity', type=int, default=1,
		choices=[0, 1, 2, 3], help='')
		# help="increase output verbosity"
	u.set_argv (argv)
	args = parser.parse_args()
	u.set_verbosity (args.verbosity)
	u.set_argv (argv)
	u.set_filetype ('embeds')
	verbose = 0
	if verbose > 0:
		print("files: ", args.files)
	if os.path.exists (args.output) :
		u.current_datetime ()
		csv_filename = 'e_dist_' + u.current_datetime () + '.csv'
		print ('CSV file exists, writing to ' +  csv_filename)
		args.output = csv_filename
	u.gen_embed_dist_csv ([args.embed1], [args.embed2], args.output)

if __name__ == "__main__":
	main (sys.argv)

