#! /usr/bin/python3

import sys
import argparse
import xml_utils as u
import datetime
import pdb
from argparse import RawTextHelpFormatter
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
	parser = argparse.ArgumentParser(description='\n\tCreate new file using search file. Unmatched content will also be written out.\n\n\tUsage: xml_extract_from_xml <search_list_file> <new_sources>  \n\n\tEx: xml_extract_from_xml -o auto_test.xml gold_test.xml allBears_faces.xml', 
		formatter_class=RawTextHelpFormatter)
    # parser.formatter.max_help_position = 50
	parser.add_argument ('search_file', help='file with search content')
	parser.add_argument ('files', nargs='+')
	parser.add_argument ('-filetype', '--filetype', default="chips",
		help='type of xml file: <images,chips,faces,pairs> .')
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
		print("output  : ", args.output)
		print('orig file : ', args.orig_file)
		print('files : ', args.files)
	xml_files = u.generate_xml_file_list (args.files)
	u.set_argv (argv)
	u.set_exec_name  (sys.argv[0])
	u.replicate_file ([args.orig_file], xml_files, args.output, args.filetype)
if __name__ == "__main__":
	main (sys.argv)

