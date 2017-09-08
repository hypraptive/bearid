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
	parser = argparse.ArgumentParser(description='Partitions data.',
		formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=50))
    # parser.formatter.max_help_position = 50
	parser.add_argument ('x', default=80,
		help='Percent of first set.')
	parser.add_argument ('y', default=20,
		help='Percent of second set.')
	parser.add_argument ('input', nargs='+')
	parser.add_argument ('-o', '--output', default="",
		help='Output file basename. Defaults to "part_<date><time>_"')
	parser.add_argument ('--verbosity', type=int, default=1,
		choices=[0, 1, 2], help=argparse.SUPPRESS)
	args = parser.parse_args()
	verbose = 0
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
	
	xml_files = u.generate_xml_file_list (args.input)
	u.generate_partitions (xml_files, args.x, args.y, args.output)


if __name__ == "__main__":
	main (sys.argv)

