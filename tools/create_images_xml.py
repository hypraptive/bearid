#! /usr/bin/python3

import sys
import argparse
import xml_utils as u
import datetime
import pdb
import os
from argparse import RawTextHelpFormatter
from collections import defaultdict

##------------------------------------------------------------
##  can be called with:
##    find_bears *.xml dirs
##------------------------------------------------------------
def main (argv) :
	parser = argparse.ArgumentParser(description='\nCreate xml from images in specified files and directories.\n \t example: create_images_xml -out imgs.xml abc.jpg bc/images ./bf/images\n',
		formatter_class=RawTextHelpFormatter)
    # parser.formatter.max_help_position = 50
	parser.add_argument ('files', nargs='+')
	parser.add_argument ('-out', '--output', 
		help='write output to specified file. Defaults to imgs.xml')
	parser.add_argument ('-v', '--verbosity', type=int, default=1,
		choices=[0, 1, 2, 3], help='print more messages')
		# choices=[0, 1, 2, 3], help=argparse.SUPPRESS)
		# help="increase output verbosity"
	args = parser.parse_args()

	# print "ls : ", args.ls
	# print "files: ", args.files

	if not args.output :
		args.output = 'imgs.xml'

	u.set_verbosity (args.verbosity)
	u.create_imgs_xml (args.files, args.output)

if __name__ == "__main__":
	main (sys.argv)

