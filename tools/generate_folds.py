#! /usr/bin/python

import sys
import argparse
import xml_utils as u
import datetime
from collections import defaultdict

##------------------------------------------------------------
##  can be called with:
##    generate_folds 5 -out yyy *.xml dirs
##------------------------------------------------------------
def main (argv) :
	parser = argparse.ArgumentParser(description='Partitions data.',
		formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=50))
    # parser.formatter.max_help_position = 50
	parser.add_argument ('n', default=5,
		help='Number of paritions to create. ')
	parser.add_argument ('files', nargs='+')
	parser.add_argument ('-o', '--output', default="",
		help='Output file basename.')
	parser.add_argument ('-m', '--mode', type=int, default=0,
		choices=[0, 1, 2], help='Mode for split chips.  0: shuffle all, then split. 1: split each label evenly. 2: split by label - i.e. each label is only in one fold.')
	parser.add_argument ('-v', '--verbosity', type=int, default=1,
		choices=[0, 1, 2, 3], help='')
		# help="increase output verbosity"
	args = parser.parse_args()
	u.set_verbosity (args.verbosity)
	u.set_argv (argv)
	u.set_filetype ('chips')
	verbose = 0
	if verbose > 0:
		print "n: ", args.n
		print "output: ", args.output
		print "files: ", args.files

	if not args.output :
		args.output = datetime.datetime.now().strftime("%Y%m%d_%H%M")
		if verbose > 0:
			print "new output: ", args.output
	xml_files = u.generate_xml_file_list (args.files)
	u.do_generate_folds (xml_files, args.n, args.output, args.mode)


if __name__ == "__main__":
	main (sys.argv)

