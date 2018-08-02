#! /usr/bin/python

import sys
import argparse
import xml_utils as u
import datetime
from collections import defaultdict
# from ordereddefaultdict import OrderedDefaultdict


##------------------------------------------------------------
##  can be called with:
##    partition_files 80 20 -out xxx *.xml dirs
##    generate_folds 5 -out yyy *.xml dirs
##------------------------------------------------------------
def main (argv) :
	parser = argparse.ArgumentParser(description='Partitions chips into x and y, defaults to 80,20.  If shuffle is set to 0, the partition will be per label.  ',
		formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=50))
    # parser.formatter.max_help_position = 50
	parser.add_argument ('x', default=80,
		help='Percent of first set.')
	parser.add_argument ('y', default=20,
		help='Percent of second set.')
	parser.add_argument ('input', nargs='+')
	parser.add_argument ('-shuffle', '--shuffle', default="",
		action="store_true",
		help='Shuffles labels before partition. Defaults to False')
	parser.add_argument ('-minimum', '--minimum', default=0,
		help='Minimum images per label. Defaults to 0.')
	parser.add_argument ('-filetype', '--filetype', default="chips",
		help='Type of file to partition. <faces|chips>.Defaults to "chips".')
	parser.add_argument ('-o', '--output', default="",
		help='Output file basename. Defaults to "part_<date><time>_"')
	parser.add_argument ('--verbosity', type=int, default=1,
		choices=[0, 1, 2], help=argparse.SUPPRESS)
	args = parser.parse_args()
	verbose = args.verbosity
	if verbose > 0 :
		print "x: ", args.x
		print "y: ", args.y
		print "sum: ", int (args.y) + int (args.x)
		print "output: ", args.output
		print "input: ", args.input

	if int(args.x) + int(args.y) != 100 :
		print "error: (x + y) needs to be 100"
		return
	if not args.output :
		args.output = datetime.datetime.now().strftime("part_%Y%m%d_%H%M")
		if verbose > 0 :
			print "new output: ", args.output
	
	filetype = args.filetype
	if (filetype != "chips") and (filetype != "faces") :
		print 'unrecognized filetype :', filetype, ', setting filetype to "chips".'
		filetype = "chips"

	xml_files = u.generate_xml_file_list (args.input)
	u.generate_partitions (xml_files, args.x, args.y, args.output, args.shuffle, int(args.minimum), filetype)


if __name__ == "__main__":
	main (sys.argv)

