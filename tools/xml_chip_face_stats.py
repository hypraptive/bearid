#! /usr/bin/python

import sys
import argparse
import xml_utils as u
import datetime
import pdb
from collections import defaultdict

##------------------------------------------------------------
##  xml_chip_face_stats *.xml dirs
##    average point of all noses, eye1_x, eye1_y, eye2_x, eye2_y, eye_dist
##
##   
##------------------------------------------------------------
def main (argv) :
	parser = argparse.ArgumentParser(description='\nGet stats for all parts of chips. ',
		formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=50))
    # parser.formatter.max_help_position = 50
	parser.add_argument ('files', nargs='+')
		# help="increase output verbosity"
	args = parser.parse_args()

	xml_files = u.generate_xml_file_list (args.files)
	u.chip_face_stats (xml_files)

if __name__ == "__main__":
	main (sys.argv)

