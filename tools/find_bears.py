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
##    find_bears *.xml intputfile
##------------------------------------------------------------
def main (argv) :
	parser = argparse.ArgumentParser(description='\nRun tensorflow model via docker to find bears in images. Takes file which lists all images (e.g. create_imgs_file->xml_to_files.py) \n \t example: ' + argv[0] + ' -mod tf-md -min 0.9 images.txt',
		formatter_class=RawTextHelpFormatter)
    # parser.formatter.max_help_position = 50
	parser.add_argument ('inputfile')
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

	models = ['tf_md', 'tf-frcnn']
	if args.model not in models :
		print ('\nError: unknown model.  Needs to be one of', models, '\n')
		return

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
	# img_files = u.get_img_files (args.files, args.absolute_path)
	print ('running:', docker_cmd)
	print ('... docker ps:', docker_result)
	print ('... min score:', args.min_score)
	print ('... output   :', args.output)
	print ('... input    :', args.inputfile)
	# print ('files: ', img_files)

	# curtime = datetime.datetime.now().strftime("%Y%m%d %H:%M:%S")
	# print ('single detects:', curtime)
	u.do_find_bears (args.inputfile, args.output, args.min_score, args.model)
	# curtime = datetime.datetime.now().strftime("%Y%m%d %H:%M:%S")
	# print ('batch detects:', curtime)
	# u.do_find_bears_batch (args.inputfile, args.output, args.min_score, args.model)
	# curtime = datetime.datetime.now().strftime("%Y%m%d %H:%M:%S")
	# print ('done:', curtime)

if __name__ == "__main__":
	main (sys.argv)

