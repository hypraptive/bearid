#! /usr/bin/python3

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
	parser = argparse.ArgumentParser(description='Create file with matched and unmatched chip pairs.', 
		formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=50))
    # parser.formatter.max_help_position = 50
	parser.add_argument ('-m', '--matched', default=0,
		help='Number of matched pairs. 0 for all.')
	parser.add_argument ('-u', '--unmatched', default=0,
		help='Number of unmatched pairs. 0 for all.')
	parser.add_argument ('-t', '--triplets', default=0,
		help='Number of triplets of un/matched sets. Overides --unmatched and --matched.')
	parser.add_argument ('chipfile', nargs='+')
	parser.add_argument ('-out', '--output', default="",
		help='Output file basename. Defaults to "part_<date><time>_"')
	parser.add_argument ('-v', '--verbosity', type=int, default=1,
		choices=[0, 1, 2, 3], help=argparse.SUPPRESS)
	u.set_argv (argv)
	args = parser.parse_args()
	u.set_verbosity (args.verbosity)
	u.set_filetype ('pairs')
	verbose = args.verbosity
	if not args.output :
		args.output = datetime.datetime.now().strftime("pairs_%Y%m%d_%H%M.xml")
	if verbose > 0 :
		print("matched   : ", args.matched)
		print("unmatched : ", args.unmatched)
		print("triplets  : ", args.triplets)
		print("output    : ", args.output)
		print("chipfile  : ", args.chipfile)

	'''
	filetype = args.filetype
	if (filetype != "chips") and (filetype != "faces") :
		print 'unrecognized filetype :', filetype, ', setting filetype to "chips".'
		filetype = "chips"
	'''
	if (args.triplets > 0) and ((args.matched > 0) or (args.unmatched > 0)) :
		print('triplets argument will override matched and unmatched arguments')
	xml_files = u.generate_xml_file_list (args.chipfile)
	u.generate_chip_pairs (xml_files, int (args.matched), int (args.unmatched), int (args.triplets), args.output)


if __name__ == "__main__":
	main (sys.argv)

