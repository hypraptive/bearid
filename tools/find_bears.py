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
	parser = argparse.ArgumentParser(description='\nRun tensorflow model via docker to find bears in images. \n \t example: find_bears -mod tf-md -min 0.9 images',
		formatter_class=RawTextHelpFormatter)
    # parser.formatter.max_help_position = 50
	parser.add_argument ('files', nargs='+')
	parser.add_argument ('-mod', '--model', default='tf-frcnn', 
		help='one of: tf-md, tf-frcnn')
	parser.add_argument ('-min', '--min_score', default="0.9",
		help='sets mininum score for detection.')
	parser.add_argument ('-abs', '--absolute_path', action="store_true",
		default=False, help='write files with absolute path.')
	parser.add_argument ('-out', '--output', 
		help='write output into specified file.')
	parser.add_argument ('-v', '--verbosity', type=int, default=1,
		choices=[0, 1, 2, 3], help='print more messages')
		# choices=[0, 1, 2, 3], help=argparse.SUPPRESS)
		# help="increase output verbosity"
	args = parser.parse_args()

	# print "ls : ", args.ls
	# print "files: ", args.files

	if not args.output :
		if (args.model == 'tf-md') :
			args.output = 'multibears_md'
		else :
			args.output = 'multibears_frcnn'
	u.set_verbosity (args.verbosity)
	print ('\n------------------------------')
	print ('... Using image:', args.model)
	print ('------------------------------')
	docker_cmd = "sudo docker ps -a | awk '/tf-*/ {print $2}'"
	docker_result = os.popen (docker_cmd).read ()
	img_files = u.get_img_files (args.files, args.absolute_path)
	print ('running:', docker_cmd)
	print ('... docker ps:', docker_result)
	print ('... min score:', args.min_score)
	print ('... output   :', args.output)
	print ('... input    :', args.files)
	print ('... # files    :', len (img_files))
	print ('... files    :', img_files)
	# print ('files: ', img_files)

	u.do_find_bears (img_files, args.output, args.min_score, args.model)

if __name__ == "__main__":
	main (sys.argv)

