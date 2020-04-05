#! /usr/bin/python3

import sys
import argparse
import xml_utils as u
import datetime
from collections import defaultdict

##------------------------------------------------------------
##  can be called with:
##    plot_embeddings *.xml dirs
##------------------------------------------------------------
def main (argv) :
	parser = argparse.ArgumentParser(description='Plot dimension-reduced embeddings.',
		formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=50))
	parser.add_argument ('files', nargs='+')
	parser.add_argument ('-v', '--verbosity', type=int, default=1,
		choices=[0, 1, 2, 3], help='')
		# help="increase output verbosity"
	u.set_argv (argv)
	args = parser.parse_args()
	u.set_verbosity (args.verbosity)
	u.set_argv (argv)
	u.set_filetype ('embeddings')
	verbose = 0
	if verbose > 0:
		print("files: ", args.files)

	xml_files = u.generate_xml_file_list (args.files)
	u.plot_embeddings (xml_files)

if __name__ == "__main__":
	main (sys.argv)

