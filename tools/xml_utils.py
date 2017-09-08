#! /usr/bin/python

import sys
import xml.etree.cElementTree as ET
import pdb
import random
import logging
import xml.dom.minidom
import argparse
import xml_explore as xe
import os
from xml.dom import minidom
from copy import deepcopy
from collections import namedtuple
from collections import defaultdict
from os import walk

##------------------------------------------------------------
##  add indentations to xml content for readability
##------------------------------------------------------------
def prettify(elem) :
    # pdb.set_trace ()
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = xml.dom.minidom.parseString(rough_string)
    pretty_print = '\n'.join(
        [line for line in reparsed.toprettyxml(indent=' '*2).split('\n') 
        if line.strip()])
    return pretty_print

##------------------------------------------------------------
##  add indentations
##------------------------------------------------------------
def indent(elem, level=0):
    i = "\n" + level*"  "
    j = "\n" + (level-1)*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subelem in elem:
            indent(subelem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = j
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = j
    return elem     

##------------------------------------------------------------
##  load xml into dictionary of <string><element_list>
##  ex:  d["b-032"] = ["<Element 'chip' at 0x123,..,<Element 'chip' at 0x43]
##       d["b-747"] = ["<Element 'chip' at 0x987,..,<Element 'chip' at 0x65]
##------------------------------------------------------------
def load_chips (root, d_chips) :
	## print "loading chips"
 
	chipfiles = []
	for chip in root.findall ('./chips/chip'):    
		label_list = chip.findall ('label')
		if len (label_list) > 1 :
			print "too many labels: ", label_list
			continue
		label = label_list[0].text
		chipfile = chip.attrib.get ('file')
		chipfiles.append (chipfile)
		## print "   ", label, ": ", label
		## print "   ", chipfile, ": ", chipfile
		d_chips[label].append(chip)
	# pdb.set_trace ()
	return chipfiles

##------------------------------------------------------------
##  print dictionary 
##------------------------------------------------------------
def print_dict (chips_d) :
	for key, value in chips_d.items():
		print(key)
		print(value)

##------------------------------------------------------------
##  ^^^^^^^^^^ START COMMENT ^^^^^^^^^^^^^^^^^^^^^^
##  ^^^^^^^^^^ END COMMENT ^^^^^^^^^^^^^^^^^^^^^^


##------------------------------------------------------------
##  partition list into x and y percent
##------------------------------------------------------------
def generate_partitions (files, x, y, output, mixed=True) :
	# print "partitioning chips into: ", x, " ", y
	chips_d = defaultdict(list)
	load_chips_from_files (files, chips_d)
	chunks = partition_chips (chips_d, x, y, mixed)
	file_x = output + "_" + str(x) + ".xml"
	file_y = output + "_" + str(y) + ".xml"
	generate_partition_files (chunks, file_x, file_y)

##------------------------------------------------------------
##  partition list into x and y percent
##------------------------------------------------------------
def partition_chips (chips_d, x, y, mixed=True) :
	# print "partitioning chips into: ", x, " ", y
	chunks = []
	if (mixed == True) :  ## concat all labels, then split
		all_chips=[]
		for label, chips in chips_d.items():
			all_chips.extend (chips)
		random.shuffle (all_chips)
		partition = int(round(len(all_chips) * float (x) / float (100)))
		# print "partition value : ", partition
		chunks.append (all_chips[:partition])
		chunks.append (all_chips[partition:])
		print "\nmixed partition of ", x, ", len : ", len (chunks[0])
		print "mixed partition of ", y, ", len : ", len (chunks[1])
		print "mixed total of ", len (chunks[0]) + len (chunks[1])
		# print "chips count: ", len (all_chips)
	else :				## split per label, then combine into chunks
		chunks_x = []
		chunks_y = []
		chip_cnt = 0
		for label, chips in chips_d.items():
			random.shuffle (chips)
			chip_cnt += len (chips)
			partition = int(round(len(chips) * float (x) / float (100)))
			chunks_x.extend (chips[:partition])
			chunks_y.extend (chips[partition:])
		chunks.append (chunks_x)
		chunks.append (chunks_y)
		print "individual partition of ", x, ", len : ", len (chunks_x)
		print "individual partition of ", y, ", len : ", len (chunks_y)
		print "individual total of ", len (chunks_y)
		print "chips count: ", chip_cnt
	# pdb.set_trace ()
	return chunks

##------------------------------------------------------------
##  split defaultdict<string><list> into n equal random parts
##  returns chunks (list of n lists)
##  By default, all labels are combined, shuffled, then split.  
##	  If mixed is False, shuffle each label, split, then added to chunks
##    
##------------------------------------------------------------
def split_chips (chips_d, n, mixed=True) :
	if (mixed == True) :  ## concat all labels, then split
		chunks=[]
		all_chips=[]
		for label, chips in chips_d.items():
			all_chips.extend (chips)
		random.shuffle (all_chips)
		chunk_size = len(all_chips) / float (n)
		print "\nchunk size : ", chunk_size
		print "chips count: ", len (all_chips)
		for i in range (n):
			start = int(round(chunk_size * i))
			end = int(round(chunk_size * (i+1)))
			# print "start : ", start
			# print "end : ", end
			chunks.append (all_chips[start:end])
	else :				## split per label, then combine into chunks
		chunks = [[] for i in range(n)]
		for label, chips in chips_d.items():
			random.shuffle (chips)
			chunk_size = len(chips) / float (n)
			for i in range (n):
				start = int(round(chunk_size * i))
				end = int(round(chunk_size * (i+1)))
				chunks[i].extend (chips[start:end])
	# pdb.set_trace ()
	return chunks

##------------------------------------------------------------
##  create n sets of trees of train & validate content
##  then write xml files
##------------------------------------------------------------
def generate_folds_files (train_list, validate_list, filename) :
	n = len (train_list)
	# write 2 files for each fold

	print "\nGenerated", n, "sets of folds files: "
	for i in range(n) :
		t_root, t_chips = create_new_tree_w_chips ()
		for j in range (len (train_list[i])) :
			chip = train_list[i][j]
			t_chips.append (chip)
		v_root, v_chips = create_new_tree_w_chips ()
		for j in range (len (validate_list[i])) :
			chip = validate_list[i][j]
			v_chips.append (chip)
		tree_train = ET.ElementTree (t_root)
		tree_validate = ET.ElementTree (v_root)
		t_name = filename + "_train_" + str(i) + ".xml"
		v_name = filename + "_validate_" + str(i) + ".xml"
		tree_train.write (t_name)
		tree_validate.write (v_name)
		print "\t", t_name, "\n\t", v_name
	print ""

##------------------------------------------------------------
##  create each tree for x and y partition
##  then write xml files
##------------------------------------------------------------
def generate_partition_files (chunks, file_x, file_y) :
	list_x = chunks[0]
	list_y = chunks[1]

	root_x, chips_x = create_new_tree_w_chips ()
	for i in range(len(list_x)):
		chips_x.append (list_x[i])
	root_y, chips_y = create_new_tree_w_chips ()
	for i in range(len(list_y)):
		chips_y.append (list_y[i])

	indent (root_x)
	indent (root_y)
	tree_x = ET.ElementTree (root_x)
	tree_y = ET.ElementTree (root_y)
	tree_x.write (file_x)
	tree_y.write (file_y)
	print "\nGenerated partition files: \n\t", file_x, "\n\t", file_y

##------------------------------------------------------------
##  create n sets of train & validate files
##  split list into n chunks
##  foreach i in n: chunks[n] is in validate, the rest in train
##  returns list of train content and list of validate content
##     to be consumed by generate_folds_files
##------------------------------------------------------------
def generate_folds_content (chips_d, n_folds) :
	n = int (n_folds)
	validate_list = []
	train_list = [[] for i in range(n)]
	chunks = split_chips (chips_d, n)
	for i in range (n):
		validate_list.append (chunks[i])
		# pdb.set_trace()
		for j in range (n):
			if (j == i):
				continue
			train_list[i].extend (chunks[j])
	return train_list, validate_list

##------------------------------------------------------------
##  generate file heading, returns root element and chips element
##------------------------------------------------------------
def create_new_tree_w_chips () :
	r = ET.Element ('dataset')
	r_c = ET.SubElement (r, 'comment').text = "generated by bearID v1.0"
	r_chips = ET.SubElement (r, 'chips')
	return r, r_chips

##------------------------------------------------------------
##   create copy of xml file of particular label
##------------------------------------------------------------
def write_file_with_label (xml_file_in, xml_file_out, key):
	tree_i = ET.parse (xml_file)
	root_i = tree.getroot()  

	for chip in root_i.findall ('./chips/chip'):    
		label_list = chip.findall ('label')
		if len (label_list) > 1 :
			print "too many labels: ", label_list
			continue
		label = label_list[0].text
		if label != key :
			root.remove (chip)
	tree_i.write (xml_file_out)

##------------------------------------------------------------
##   return flattened list of all xml files
##------------------------------------------------------------
def generate_xml_file_list (inputfiles):
	f = []
	for i in inputfiles :
		if os.path.isdir (i) :
			files =  get_xml_files (i)
			f.extend (files)
		else :
			f.append (i)
	return f

##------------------------------------------------------------
##  load chips from list of files into chips_d 
##    if filename is directory, load all its xml files
##------------------------------------------------------------
def load_chips_from_files (filenames, chips_d):
	chipfiles = []
	# print "in load_chips_from_files"
	# pdb.set_trace ()
	## load all chips into chips_d
	print "\nLoading chips for files: "
	for file in filenames:
		print "\t", file
		root, tree = xe.load_file (file)
		chipfiles.extend (load_chips (root, chips_d))
	# pdb.set_trace()
	return chipfiles

##------------------------------------------------------------
##  return label stats in file
##------------------------------------------------------------
def get_chip_stats (filenames, print_files=False):
	chips_d = defaultdict(list)
	chipfiles = load_chips_from_files (filenames, chips_d)
	# pdb.set_trace ()
	count = 0
	print ""
	for key, value in sorted(chips_d.items()):
		print key, " : ", len (value)
		count += len (value)
	print "-----------------------------"
	print "total   : ", count
	# pdb.set_trace()
	if print_files :
		chipfiles.sort () 
		for chipfile in chipfiles:
			print "\t", chipfile
	print ""

##------------------------------------------------------------
##  return xml files in directory
##------------------------------------------------------------
def get_xml_files (dir) :
	xml_files = []
	for dirname, dirs, files in os.walk (dir):
		# print "files: ", files
		for file in files:
			if (file.endswith ('.xml')):
				xml_files.append (os.path.join(dirname, file))
				# print "file: ", file
			# pdb.set_trace ()
	return xml_files

##------------------------------------------------------------
##   main code
##------------------------------------------------------------
def do_generate_folds (input_files, n_folds, output_file) :
	chips_d = defaultdict(list)
	load_chips_from_files (input_files, chips_d)
	## print "printing chips dictionary ... "
	## print_dict (chips_d)
	train_list, validate_list = generate_folds_content (chips_d, n_folds)
	generate_folds_files (train_list, validate_list, output_file)

##------------------------------------------------------------
##  can be called with:
##    partition_files 80 20 -out xxx *.xml dirs
##    generate_folds 5 -out yyy *.xml dirs
##------------------------------------------------------------
def main (argv) :
    parser = argparse.ArgumentParser(description='Generate data for training.',
        formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=50))
    # parser.formatter.max_help_position = 50
    parser.add_argument ('--partition', default=80,
        help='Parition data in two. Defaults to 80.')
    parser.add_argument ('--folds', default=5,
        help='Generate n sets of train/validate files. Defaults to 5.')
    parser.add_argument ('--output', default="",
        help='Output file basename.')
    parser.add_argument ('--verbosity', type=int, default=1,
        choices=[0, 1, 2], help="increase output verbosity")


if __name__ == "__main__":
	main (sys.argv)


## test split/partition.  use count with remainders
## import datetime
## datetime.datetime.now().strftime("%Y%m%d_%H%M")
## split x y (x+y=100)
## split n
## generate_partition_files 80 20 [xml_file_or_dir]+
## generate_folds_files 5 [xml_file_or_dir]+



