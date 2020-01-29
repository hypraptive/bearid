#! /usr/bin/python3

import sys
import argparse
import xml_utils as u
import datetime
import pdb
from collections import defaultdict

##------------------------------------------------------------
##  xml_validate_chips *.xml/dirs
##    given list of chips, write new file with non-existent
##		chips removed.
##
##	Ex: xml_validate_chips folds/*.xml
##   
##------------------------------------------------------------
def main (argv) :
	parser = argparse.ArgumentParser(description='\Generate new file with non-existent chips removed.  Ex: xml_validate_chips -o valid_chips folds/*.xml', 
		formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=50))
    # parser.formatter.max_help_position = 50
	parser.add_argument ('xml_file')
	parser.add_argument ('-o', '--output', default="",
		help='Output file postfix. Defaults to "valid_chips_<date><time>_"')
	parser.add_argument ('--verbosity', type=int, default=1,
		choices=[0, 1, 2], help=argparse.SUPPRESS)
		# help="increase output verbosity"
	args = parser.parse_args()

	verbose = args.verbosity
	# pdb.set_trace ()
	if not args.output :
		args.output = datetime.datetime.now().strftime("valid_chips_%Y%m%d_%H%M.xml")
	if verbose > 0 :
		print('input   : ', args.xml_file)
		print("output  : ", args.output)
	u.set_argv (argv)
	u.set_exec_name  ('xml_validate_chips')
	u.validate_file (args.xml_file, args.output)

if __name__ == "__main__":
	main (sys.argv)

