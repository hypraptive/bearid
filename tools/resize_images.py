#! /usr/bin/python3

import sys
import argparse
import xml_utils as u
import datetime
from argparse import RawTextHelpFormatter
from collections import defaultdict

##------------------------------------------------------------
##  can be called with:
##	  
##    resize_images -
##------------------------------------------------------------
def main (argv) :
	parser = argparse.ArgumentParser(description='Downscale face images, cropping to maintain face close to mininum size.\n\tCreates new images to parallel directories and generates new xml with updated content.\n\n\tExample:\n\tresize_images.py -x_max 640 -y_max 480 faces.xml',
		formatter_class=RawTextHelpFormatter)
	parser.add_argument ('files', nargs='+')
	parser.add_argument ('-x_max', '--x_max', default=1500,
		help='max width of image, defaults to 1500.')
	parser.add_argument ('-y_max', '--y_max', default=2000,
		help='max heigth of image, defaults to 2000.')
	parser.add_argument ('-min_face', '--min_face', default=200,
		help='max heigth of image, defaults to 2000.')
	parser.add_argument ('-v', '--verbosity', type=int, default=1,
		choices=[0, 1, 2, 3], help='')
		# help="increase output verbosity"
	u.set_argv (argv)
	args = parser.parse_args()
	u.set_verbosity (args.verbosity)
	u.set_argv (argv)
	u.set_filetype ('faces')
	verbose = 0
	if verbose > 0:
		print("files: ", args.files)

	for face_xml in args.files :
		u.resize_face_file (face_xml, args.x_max, args.y_max, args.min_face)

if __name__ == "__main__":
	main (sys.argv)

