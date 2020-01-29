#! /usr/bin/python

import sys
import argparse
import xml_utils as u
import datetime
import pdb
from collections import defaultdict

##------------------------------------------------------------
##  xml_extract_list face_list_source *.xml/dirs
##    given list of images, return same list of images with 
##		new data from argument list.
##      
##      Use in replicating a test set previous used for training
##
##	ex: xml_extract_list -o auto_test.xml gold_test.xml  allBears_faces.xml
##   
##------------------------------------------------------------
def main (argv) :
	parser = argparse.ArgumentParser(description='\nReplicates list of images using new face data in argumentlist.  Ex: xml_extract_list -o auto_test.xml gold_test.xml allBears_faces.xml', 
		formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=50))
    # parser.formatter.max_help_position = 50
	parser.add_argument ('orig_file', help='file to replicate')
	parser.add_argument ('files', nargs='+')
	parser.add_argument ('-o', '--output', default="",
		help='Output filename. Defaults to "copy_<date><time>_"')
	parser.add_argument ('--verbosity', type=int, default=1,
		choices=[0, 1, 2], help=argparse.SUPPRESS)
		# help="increase output verbosity"
	args = parser.parse_args()

	verbose = args.verbosity
	# pdb.set_trace ()
	if not args.output :
		args.output = datetime.datetime.now().strftime("copy_%Y%m%d_%H%M.xml")
	if verbose > 0 :
		print "output  : ", args.output
		print 'orig file : ', args.orig_file
		print 'files : ', args.files
	xml_files = u.generate_xml_file_list (args.files)
	u.set_argv (argv)
	u.set_exec_name  ('extract_list')
	u.replicate_file ([args.orig_file], xml_files, args.output)

if __name__ == "__main__":
	main (sys.argv)

