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
	parser.add_argument ('-av', '--average', action='store_true', 
		help='for embed2, use average for each label instead of each embedding. Mutually exclusive with --top_match')
	parser.add_argument ('-top', '--top_match', 
		help='find closest n matches and use simple majority for matching. Defaults to 1.  Used mutually exclusively with --average.')
	parser.add_argument ('-db', '--db',
		help='db of images info.')
	parser.add_argument ('-out', '--output', default="e_dist.csv",
		help='specify csv output file.')
	parser.add_argument ('-stats', '--stats', action='store_true', 
		help='Write matching stats for each label.')
	parser.add_argument ('-v', '--verbosity', type=int, default=1,
		choices=[0, 1, 2, 3], help='')
		# help="increase output verbosity"
	u.set_argv (argv)
	args = parser.parse_args()
	u.set_verbosity (args.verbosity)
	u.set_argv (argv)
	u.set_filetype ('embeds')
	if args.verbosity > 0:
		print("input files: ", args.embed1, args.embed2)
	if args.average and args.top_match :
		print ('options --average and --top_match are mutually exclusive.\n')
		return
	if os.path.exists (args.output) :
		u.current_datetime ()
		csv_filename = 'e_dist_' + u.current_datetime () + '.csv'
		print ('CSV file exists, writing to ' +  csv_filename)
		args.output = csv_filename
	if args.average :
		top_match = 0
	elif args.top_match :
		top_match = args.top_match
	else :
		top_match = 1  # default value

	u.gen_embed_dist_csv ([args.embed1], [args.embed2], args.output, args.db, int (top_match), args.stats)

if __name__ == "__main__":
	main (sys.argv)

