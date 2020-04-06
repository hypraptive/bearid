#! /usr/bin/python3


import sys
import os
import argparse
# import xml_utils as u
# import datetime
import pdb
import subprocess
# from collections import defaultdict

##------------------------------------------------------------
##  can be called like this:
##
##   bearid <image_file>
##   bearid <image_dir>
##
##------------------------------------------------------------

##------------------------------------------------------------
#   How this program works:
#

# create file xml; NOTE: use -r to recursively search for images files
# img = imglab -c also.xml /home/data/bears/imageSource/britishColumbia/melanie_20170828/bc_also

# get faces for those images images
# bearface = bearface ~/dev/bearid-models/bearface_network.dat also.xml

# create chips of faces
# bearchip = bearchip also_faces.xml

# create embeddings for the faces
# bearembed = bearembed --embed ~/dev/bearid-models/bearembed_network.dat --anet also_faces_chips.xml

# classify NOTE: input dat files are hard coded
# bearsvm = bearsvm --infer also_faces_chips_embeds.xml

def main (argv) :
	cmds = []
	outfiles = []
	printfiles = []
	# imgs_xml = "imgs.xml"
	# faces_xml = "imgs_faces.xml"
	# chips_xml = "imgs_faces_chips_xml"
	# embeds_xml = "imgs_faces_chips_embed.xml"
	outdir = './'
	outdir = './result/'
	imgs_xml = outdir + "imgs.xml"
	faces_xml = outdir + "imgs_faces.xml"
	chips_xml = outdir + "imgs_faces_chips.xml"
	embeds_xml = outdir + "imgs_faces_chips_embeds.xml"
	imglab = "/usr/local/bin/imglab"

	#--------------------------------------------------
	#  list all required files here.
	#--------------------------------------------------
	files_dep = []   # list of files required to exist
	files_dep.append (imglab)
	bearface = "/home/mary/tools/bearface"
	files_dep.append (bearface)
	bearchip = "/home/mary/tools/bearchip"
	files_dep.append (bearchip)
	bearembed = "/home/mary/tools/bearembed"
	files_dep.append (bearembed)
	bearsvm = "/home/mary/tools/bearsvm"
	files_dep.append (bearsvm)
	bearface_network = "/home/ed/dev/bearid-models/bearface_network.dat"
	files_dep.append (bearface_network)
	bearembed_network = "/home/ed/dev/bearid-models/bearembed_network.dat"
	files_dep.append (bearembed_network)
	bearsvm_network = "/home/mary/tmp/dh_gold_diff/bearsvm_network.dat"
	files_dep.append (bearsvm_network)
	bearsvm_ids = "/home/mary/tmp/dh_gold_diff/bearsvm_network_ids.dat"
	files_dep.append (bearsvm_ids)
	#--------------------------------------------------
	# validate that all those files exist
	#--------------------------------------------------
	print ('\n... validating files... ')
	for f in files_dep :
		if os.path.exists (f) :
			print ('\tfile OK        : ', f )
		else :
			print ('\tfile NOT found : ', f )
	if not os.path.exists (outdir) :
		print ('... creating ', outdir)
		os.mkdir (outdir)
	else :
		print ('... ', outdir, ' already exists.')

	#--------------------------------------------------
	# commands should look something like:
	# imglab -c imgs.xml <img/dir/file>
	# bearface ~/dev/bearid-models/bearface_network.dat imgs.xml
	# bearchip imgs_faces.xml
	# bearembed --embed ~/dev/bearid-models/bearembed_network.dat --anet imgs_faces_chips_xml
	# bearsvm --infer imgs_faces_chips_embed.xml
	#--------------------------------------------------

	echo = 'echo '
	echo = '' 
	run = 'test'
	run = 'bearid'
	args = ''
	for a in sys.argv[1:] :
		args += ' '
		args += a
	if run == 'bearid' :
		cmds.append (echo + imglab + " -c " + imgs_xml + " " + args)
		outfiles.append ("imglab.out")
		cmds.append (echo + bearface + " " + bearface_network + " " + imgs_xml)
		outfiles.append ("bearface.out")
		cmds.append (echo + bearchip + " " + faces_xml)
		outfiles.append ("bearchip.out")
		cmds.append (echo + bearembed + " --embed " + bearembed_network + " --anet " + chips_xml)
		outfiles.append ("bearembed.out")
		cmds.append (echo + bearsvm + " --infer " + bearsvm_network + " " + embeds_xml)
		outfiles.append ("bearsvm.out")
		printfiles.append ("bearsvm.out")
	elif run == 'test' :
		cmds.append (echo + imglab + " -c " + imgs_xml + " " + args)
		outfiles.append ("imglab.out")
		cmds.append (echo + bearface + " " + bearface_network + " " + imgs_xml)
		outfiles.append ("bearface.out")
		cmds.append (echo + bearchip + " " + faces_xml)
		outfiles.append ("bearchip.out")
		chips_xml = "test_output/chips_validate.xml"
		embeds_xml = "test_output/chips_validate_embeds.xml"
		cmds.append (echo + bearembed + " --test " + bearembed_network + " --anet " + chips_xml)
		outfiles.append ("bearembed.out")
		cmds.append (echo + bearsvm + " --test " + bearsvm_network + " " + embeds_xml)
		outfiles.append ("bearsvm.out")
		printfiles.append ("bearsvm.out")

	# for cmd in cmds :
	i = 0
	cmdlen = len (cmds)
	while i < cmdlen :
		cmd = cmds[i]
		outfile = outfiles[i]
		# print ('--------------------------------------------------')
		outf = open (outfile, 'w')
		print ('\nrunning: ', cmd)
		process = subprocess.Popen(cmd.split(), stdout=outf, stderr=subprocess.PIPE)
		stdout, stderr = process.communicate()
		if process.returncode != 0 :
			print ('return code : ', process.returncode)
		# print ('--------------------------------------------------')
		i += 1

	i = 0
	while i < len (printfiles) :
		print ('printing content of: ', printfiles[i])
		with open (printfiles[i], 'r') as fin :
			print (fin.read())
		i += 1

#		process = subprocess.Popen(cmd.split(),
#			stdout=subprocess.PIPE, 
#			stderr=subprocess.PIPE)
#			print ('stdout      : ', stdout.decode ('utf-8'))
#			print ('stderr      : ', stderr.decode ('utf-8'))

	# parser = argparse.ArgumentParser(description='\nPrint combined stats for all input files/directory.\n \t example: xml_obj_stats -l xxx_*_xml outputdir',
	# 	formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=50))
    # parser.formatter.max_help_position = 50
	# parser.add_argument ('files', nargs='+')
	# parser.add_argument ('-filetype', '--filetype', default="chips",
		# help='type of xml file: <chips,faces,pairs> .')
	# parser.add_argument ('-write', '--write', default="",
	# 	action="store_true",
	# 	help='write stats into file stats_*_<currentDate> .')
	# parser.add_argument ('-l', '--ls', default="",
	# 	action="store_true",
	# 	help='print ordered list of filenames.')
	# parser.add_argument ('-v', '--verbosity', type=int, default=1,
	# 	choices=[0, 1, 2, 3], help=argparse.SUPPRESS)
		# help="increase output verbosity"
	# args = parser.parse_args()
	# print "ls : ", args.ls
	# print "files: ", args.files

	# u.set_verbosity (args.verbosity)
	# xml_files = u.generate_xml_file_list (args.files)
	# u.get_obj_stats (xml_files, args.ls, args.filetype, args.verbosity, args.write)

if __name__ == "__main__":
	main (sys.argv)
##------------------------------------------------------------
#
#
#
##------------------------------------------------------------


