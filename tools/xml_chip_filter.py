#! /usr/bin/python3

import sys
import argparse
import xml_utils as u
import datetime
import pdb
from collections import defaultdict

##------------------------------------------------------------
##  xml_chip_nose_filter *.xml dirs
##    given x, y, dist: return noses within dist of x, y /(av nose)
##      default is all noses between eyes
##
##	ex: filter -out file -dist 2345 -pt [x y] <xmls>
##   
##------------------------------------------------------------
def main (argv) :
	parser = argparse.ArgumentParser(description='\nFilter chips with given circle (center & radius). Defaults to average nose and half the distance between the eyes.  Ex: filter -pt [23 45] -dist 40 <files>',
		formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=50))
    # parser.formatter.max_help_position = 50
	parser.add_argument ('files', nargs='+')
	parser.add_argument ('-pt', '--pt', default="",
		help='"x y" for center of circle. Defaults to average of noses.')
	parser.add_argument ('-d', '--distance', default=0,
		help='Radius of circle. Defaults to half distance between eyes.')
	parser.add_argument ('-o', '--output', default="",
		help='Output file basename. Defaults to "part_<date><time>_"')
	parser.add_argument ('--verbosity', type=int, default=1,
		choices=[0, 1, 2], help=argparse.SUPPRESS)
		# help="increase output verbosity"
	args = parser.parse_args()

	verbose = args.verbosity
	center = [0, 0]
	if args.pt :
		pt = (args.pt).split (' ')
		if len (pt) != 2 :
			print("Input error for -pt: needs exactly 2 numbers.  Using default.")
		elif not pt[0].isdigit () or not pt[1].isdigit () :
			print("Input error for -pt: needs to be 2 numbers.  Using default.")
		else :
			center[0] = int (pt[0])
			center[1] = int (pt[1])
	# pdb.set_trace ()
	if not args.output :
		args.output = datetime.datetime.now().strftime("chip_filtered_%Y%m%d_%H%M.xml")

	distance = 0
	if args.distance :
		if not (args.distance).isdigit () :
			print("Input error for --distance: needs to be a number.  Using default.")
		else :
			distance = int (args.distance)
			
	if verbose > 0 :
		print("output  : ", args.output)
		print("center  : ", center)
		print("distance: ", distance)
	xml_files = u.generate_xml_file_list (args.files)
	u.filter_chips (xml_files, center, distance, args.output)

if __name__ == "__main__":
	main (sys.argv)

