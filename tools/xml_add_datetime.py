#! /usr/bin/python3

import sys
import argparse
import xml_utils as u
import pdb
import datetime
from argparse import RawTextHelpFormatter
from collections import defaultdict

##------------------------------------------------------------
##  takes chip or image xml and add creation datetime from exif data.
##	  
##    writes out to new file with same base name
##------------------------------------------------------------
def main (argv) :
	filetypes = ['images', 'chips', 'faces', 'video_chips']
	filetype_mesg = 'Input file type, should be one of ' + '|'.join (filetypes)
	parser = argparse.ArgumentParser(description='add dateTime string of original source.\nExample: xml_add_datetime -vdb video_info.csv chips.xml\n',
		formatter_class=RawTextHelpFormatter)
	parser.add_argument ('files', nargs='+')
	parser.add_argument ('-filetype', '--filetype', default="chips",
		help=filetype_mesg)
	parser.add_argument ('-root', '--root', default='/video/bears/videoFrames/britishColumbia/',
		help='path to start of media hierarchy.\nDefaults to /video/bears/videoFrames/britishColumbia/')
	parser.add_argument ('-out', '--outfile',
		help='file to write resulting xml.  Defaults to first input xml with _datetime.')
	parser.add_argument ('-vdb', '--vdb',
		help='CSV of videos  (\';\' separated) for date/label information.')
	parser.add_argument ('-v', '--verbosity', type=int, default=1,
		choices=[0, 1, 2, 3], help='')
		# help="increase output verbosity"
	u.set_argv (argv)
	args = parser.parse_args()
	u.set_verbosity (args.verbosity)
	u.set_argv (argv)
	u.set_filetype (args.filetype)
	verbose = 0
	if verbose > 0:
		print("files: ", args.files)

	filetype = args.filetype
	if filetype not in filetypes :
		print('unrecognized filetype :', filetype, 'should be one of:', ', '.join (filetypes))
		return
	if filetype == 'video_chips' and args.vdb is None :
		print ('\n  Video database is required for video chips.  Use -vdb to specify video datbase.\n')
		return
	if args.vdb and filetype != 'video_chips' :
		print ('Warning: type is not viedo_chips, vdb', args.vdb, 'will be ignored')
		
	xml_files = u.generate_xml_file_list (args.files)
	outfile = args.outfile
	if outfile is None :
		outfile = u.make_new_name (xml_files[0], '_datetime')
	print ('args:', xml_files, args.vdb, args.root, outfile)
	u.add_object_datetime (xml_files, args.filetype, outfile, args.root, args.vdb)

if __name__ == "__main__":
	main (sys.argv)

