#! /usr/bin/python3

import sys
import argparse
import xml_utils as u
import datetime
import pdb
from argparse import RawTextHelpFormatter
from collections import defaultdict

##------------------------------------------------------------
##  xml_to_files -out files.text *.xml/dirs
##    given xml of objects, write filenames to output file
##      
##  used to extract filelames from xml
##
##	ex: xml_to_files -o filenames.txt gold_test.xml allBears_faces.xml
##   
##------------------------------------------------------------
def main (argv) :
	parser = argparse.ArgumentParser(description='\n\tWrite filenames of objects into output file.\n\tEx: xml_to_files -o filenames.txt txt allBears_faces.xml', 
		formatter_class=RawTextHelpFormatter)
    # parser.formatter.max_help_position = 50
	parser.add_argument ('files', nargs='+')
	parser.add_argument ('-file', '--filetype', default="chips",
		help='type of xml file: <images,chips,faces,pairs> .')
	parser.add_argument ('-filename_type', '--filename_type', default="file",
		help='type of filename: <file,source> .')
	parser.add_argument ('-out', '--output', default="filenames.txt",
		help='Output filename. Defaults to "filenames.txt"')
	parser.add_argument ('--verbosity', type=int, default=1,
		choices=[0, 1, 2], help=argparse.SUPPRESS)
		# help="increase output verbosity"
	args = parser.parse_args()

	verbose = args.verbosity
	# pdb.set_trace ()
	filename_types = ['source', 'file']
	if args.filename_type not in filename_types :
		print ('\nError: filename_type', args.filename_type, 'unrecognized. Need to be one of, ', filename_types, '\n')
		return
	filetypes = ['images', 'chips', 'faces', 'pairs']
	if args.filetype not in filetypes:
		print ('\nError: filetype', args.filetype, 'unrecognized. Need to be one of, ', filetypes, '\n')
		return
	xml_files = u.generate_xml_file_list (args.files)
	if verbose > 0 :
		print("output    : ", args.output)
		print("filetype  : ", args.filetype)
		print('files : ', args.files)
	u.set_argv (argv)
	u.set_exec_name  (sys.argv[0])
	u.xml_to_files  (xml_files, args.output, args.filetype, args.filename_type)

if __name__ == "__main__":
	main (sys.argv)

