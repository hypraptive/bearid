#! /usr/bin/python3

import sys
from lxml import etree as ET
import xml.etree.cElementTree as ET
import pdb
import random
import logging
import xml.dom.minidom
import argparse
import os
import datetime
import requests
import csv
import sqlite3
from xml.dom import minidom
from copy import deepcopy
from collections import namedtuple
from collections import defaultdict
from os import walk
import numpy as np
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from mpl_toolkits.mplot3d import Axes3D
from sklearn.manifold import TSNE
from PIL import Image
from pathlib import Path


g_x = 0
g_y = 1
g_unused = 2
g_small_img = 3
g_verbosity = 0
g_filetype = ''
g_stats_few = []
g_stats_many = []
g_argv = ''
g_exec_name = 'bearID v0.1'
g_box_attrs = {'height', 'left', 'top', 'width'} 
g_shape_parts_head = {'htop', 'head_top', 'top'}
g_shape_parts_face = {'lear', 'leye', 'nose', 'rear', 'reye'}
g_shape_parts_find = {'lear', 'leye', 'nose', 'rear', 'reye', 'htop', 'head_top'}
g_shape_parts = {'lear', 'leye', 'nose', 'rear', 'reye', 'head_top'}
all_labels = []
bc_labels=[
	'bc_adeane', 'bc_also', 'bc_amber', 'bc_aurora', 'bc_beatrice', 'bc_bella',
	'bc_bellanore', 'bc_bracket', 'bc_bruno', 'bc_caramel', 'bc_chestnut', 
	'bc_cleo', 'bc_clyde', 'bc_coco', 'bc_cross-paw', 'bc_dani-bear', 
	'bc_diablo', 'bc_fisher', 'bc_flora', 'bc_frank', 'bc_freckles', 'bc_freda', 
	'bc_freya', 'bc_gary', 'bc_gc', 'bc_glory', 'bc_hoeya', 'bc_jaque', 
	'bc_kiokh', 'bc_kwatse', 'bc_lenore', 'bc_lillian', 'bc_lil-willy', 
	'bc_lucky', 'bc_matsui', 'bc_millerd', 'bc_mouse', 'bc_neana', 'bc_no-tail', 
	'bc_old-girl', 'bc_oso', 'bc_peanut', 'bc_pete', 'bc_pirate', 
	'bc_pretty-boy', 'bc_river', 'bc_sallie', 'bc_santa', 'bc_shaniqua', 
	'bc_simoom', 'bc_stella', 'bc_steve', 'bc_teddy-blonde', 'bc_teddy-brown', 
	'bc_toffee', 'bc_topaz', 'bc_trouble', 'bc_tuna', 'bc_ursa']
bf_labels = [
	'bf_032', 'bf_039', 'bf_045', 'bf_051', 'bf_068', 'bf_083', 'bf_089', 
	'bf_093', 'bf_094', 'bf_128', 'bf_130', 'bf_132', 'bf_151', 'bf_153', 
	'bf_171', 'bf_201', 'bf_218', 'bf_261', 'bf_263', 'bf_273', 'bf_274', 
	'bf_284', 'bf_289', 'bf_293', 'bf_294', 'bf_401', 'bf_402', 'bf_409', 
	'bf_410', 'bf_415', 'bf_425', 'bf_435', 'bf_451', 'bf_461', 'bf_469', 
	'bf_474', 'bf_477', 'bf_480', 'bf_482', 'bf_489', 'bf_500', 'bf_503', 
	'bf_504', 'bf_505', 'bf_510', 'bf_511', 'bf_600', 'bf_602', 'bf_603', 
	'bf_604', 'bf_610', 'bf_611', 'bf_613', 'bf_614', 'bf_615', 'bf_634', 
	'bf_700', 'bf_708', 'bf_717', 'bf_718',	'bf_719', 'bf_720', 'bf_744', 
	'bf_747', 'bf_755', 'bf_775', 'bf_813', 'bf_814', 'bf_818', 'bf_854', 
	'bf_856', 'bf_868', 'bf_879'
	]
all_labels = bc_labels + bf_labels
coco_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19, 20, 
	21, 22, 23, 24, 25, 27, 28, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 
	43, 44, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 
	63, 64, 65, 67, 70, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 84, 85, 86, 87, 88, 89, 90]
coco_classes = ["person", "bicycle", "car", "motorcycle", "airplane", "bus", 
	"train", "truck", "boat", "traffic light", "fire hydrant", "stop sign", 
	"parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow", 
	"elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag", 
	"tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite", 
	"baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket", 
	"bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", 
	"apple", "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", 
	"donut", "cake", "chair", "couch", "potted plant", "bed", "dining table", 
	"toilet", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone", 
	"microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", 
	"vase", "scissors", "teddy bear", "hair drier", "toothbrush"]
md_ids = [1, 2, 3]
md_classes = ['animal', 'person', 'vehicle']
object_classes_d = defaultdict ()

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
##  set global verbosity
##------------------------------------------------------------
def set_verbosity  (verbosity) :
	global g_verbosity
	g_verbosity = verbosity

##------------------------------------------------------------
##  get global verbosity
##------------------------------------------------------------
def get_verbosity () :
	return g_verbosity

##------------------------------------------------------------
##  set global filetype
##------------------------------------------------------------
def set_filetype  (filetype) :
	global g_filetype
	g_filetype = filetype

##------------------------------------------------------------
##  get global filtype
##------------------------------------------------------------
def get_filetype () :
	return g_filetype

##------------------------------------------------------------
##  set global exec name
##------------------------------------------------------------
def set_exec_name  (exec_name) :
	global g_exec_name
	g_exec_name = exec_name

##------------------------------------------------------------
##  get global filtype
##------------------------------------------------------------
def get_exec_name () :
	return g_exec_name

##------------------------------------------------------------
##------------------------------------------------------------
def set_argv (argv) :
	global g_argv
	g_argv = ' '.join (argv)

##------------------------------------------------------------
##------------------------------------------------------------
def get_argv () :
	return g_argv

##------------------------------------------------------------------------
#  return count of specified pathed element from tree node
#  example of counting labels:
#      count_elem (root, "images image box label")
##------------------------------------------------------------------------
def count_elem (node, child_elem):
	count=0
	elems = child_elem.split ()
	if (len (elems) == 1):
		children = node.findall (child_elem)
		return len (children)
	# get the next child down, recurse
	elems = child_elem.split (' ', 1)
	for child in node.findall (elems[0]):
		count += count_elem (child, elems[1])
	return count	
    
#---------------------------------------------------------------------------
#  return count of faces/boxes in xml
#---------------------------------------------------------------------------
def count_faces (faces_xml):
	tree = ET.parse (faces_xml)
	root = tree.getroot()
	count = count_elem (root, "images image box")
	return count
    
#---------------------------------------------------------------------------
#  insert element label to "images image box" with specified string
#---------------------------------------------------------------------------
def add_box_label (tree, label_str):
	label_count=0
	for images in tree.findall ('images'):
		for image in images.findall ('image'):
			for box in image.findall ('box'):
				curLabel = box.findall ('label')
				if len(curLabel) > 0:
					print(image.text + " has existing label of " + curLabel.text)
					continue
				label = ET.SubElement (box, 'label')
				# pdb.set_trace ()
				label.text = label_str;
				label_count += 1
				# print "added label"
	return label_count

##------------------------------------------------------------
##  read in image and determine ratio to scale to max values.
##  return ratio 
##------------------------------------------------------------
def get_downscale_ratio (imgfile, max_long, max_short) :
	img = Image.open (imgfile)
	w, h = img.size
	ratio = 1
	if w * h < max_long * max_short : 
		return ratio
	if w > h :
		if (max_long / w) < (max_short / h) :
			ratio = max_long / w
		else :
			ratio = max_short / h
	else :
		if (max_long / h) < (max_short / w) :
			ratio = max_long / h
		else :
			ratio = max_short / w
	return math.sqrt (ratio)

##------------------------------------------------------------
##  read in image and determine ratio to scale to max area.
##  return ratio 
##------------------------------------------------------------
def get_downscale_ratio (imgfile, max_area) :
	img = Image.open (imgfile)
	w, h = img.size
	img_size = w * h
	ratio = max_area / img_size
	# print ('orig size: ', img_size, ' ratio: ', ratio)
	if ratio > 1 :
		ratio = 1
	return math.sqrt (ratio)

##------------------------------------------------------------
##  
## 
##------------------------------------------------------------
def get_faces_boundary (image_tag) :
	max_left = 0
	max_right = 0
	max_top = 0
	max_bottom = 0
	for box in image_tag.findall ('box') :
		left = int (box.attrib.get ('left'))
		top = int (box.attrib.get ('head_top'))
		height = int (box.attrib.get ('height'))
		width = int (box.attrib.get ('width'))
		right = left + width
		bottom = top + height
		if left > max_left :
			max_left = left
		if right > max_right :
			max_right = right
		if top > max_top :
			max_top = top
		if bottom > max_bottom :
			max_bottom = bottom
	return max_left, max_top, max_right, max_bottom

##------------------------------------------------------------
##  crop image to max size or min of faces
##  return new image
##------------------------------------------------------------
def crop_image (img, image_tag, max_x, max_y) :
	w, h = img.size
	# print ('in crop function: orig w x h ', w, h, '\n')
	if w * h < max_x * max_y :
		print (' -- no cropping')
		return img
	if w < h :
		print ('swapped x & y')
		tmp_x = max_x
		max_x = max_y
		max_y = tmp_x
	new_origin_x = 0
	new_origin_y = 0
	left, top, right, bottom = get_faces_boundary (image_tag)
	# print ('face boundary: ', left, top, right, bottom)
	faces_width = right - left
	faces_height = bottom - top
	if faces_width > max_x :  ## faces larger than max image!
		max_x = faces_width
	if faces_height > max_y :  ## faces height larger than max image!
		max_y = faces_height
	# doing proportion crop
	# pdb.set_trace ()
	new_cropped_left = int (left / w * max_y)  # new left after crop
	new_cropped_top = int (top / h * max_x)  # new left after crop
	new_origin_left = left - new_cropped_left
	new_origin_top = top - new_cropped_top
	# print ('new origin (left,top): ', new_origin_left, new_origin_top)
	# print ('cropping to (l,t,r,b) :', new_origin_left, new_origin_top, new_origin_left+max_y, new_origin_top+max_x)
	cropped_img = img.crop ((new_origin_left, new_origin_top, new_origin_left+max_y, new_origin_top+max_x))
	pan_boxes (image_tag, new_origin_left, new_origin_top)
	return cropped_img

##------------------------------------------------------------
##  downscale image by ratio
##  return new image
##------------------------------------------------------------
def downscale_image (imgfile, ratio) :
	img = Image.open (imgfile)
	w, h = img.size

	new_w = int (w*ratio)
	new_h = int (h*ratio)

	resized_img = img.resize ((new_w, new_h))
	return resized_img

##------------------------------------------------------------
##  downscale image and boxes by ratio
##  return new image
##------------------------------------------------------------
def downscale_image_and_boxes (imgfile, image_tag, ratio) :
	resized_img = downscale_image (imgfile, ratio)
	for box_tag in image_tag.findall ('box') :
		scale_box (box_tag, ratio)
	return resized_img

##------------------------------------------------------------
## return largest of any dimension of face
##------------------------------------------------------------
def get_min_img_face_size (image_tag) :
	min_face_size = 2000
	for box_tag in image_tag.findall ('box') :
		for attrib in ('height', 'width') :
			val = box_tag.attrib.get (attrib)
			if val != None :
				val = int (val)
				if val < min_face_size :
					min_face_size = val
			else :
				print ('attrib ', attrib, 'not found')
	return min_face_size

##------------------------------------------------------------
##------------------------------------------------------------

##------------------------------------------------------------
##	scales attributes in box using ratio
##    modifies: box (height, width, top, left), box.part (x, y)
##------------------------------------------------------------
def scale_box (box, pxRatio) :
	found_head = False
	for attrib in g_box_attrs:
		val = box.attrib.get (attrib)
		if val != None :
			val = int (val)
			box.set (attrib, str (int (val * pxRatio)))
		else :
			print ('attrib ', attrib, 'not found')
	for part in box.findall ('./part') :
		for attrib in ('x', 'y') :
			val = part.attrib.get (attrib)
			if val != None :
				val = int (val)
				part.set (attrib, str (int (val * pxRatio)))
			else :
				print ('attrib ', attrib, 'not found')

##------------------------------------------------------------
##	scales attributes in box using ratio
##    modifies: box (height, width, top, left), box.part (x, y)
##------------------------------------------------------------
def pan_boxes (image_tag, new_origin_left, new_origin_top) :

	for box in image_tag.findall ('box') :
		val = box.attrib.get ('head_top')
		if val != None :
			val = int (val)
			box.set ('head_top', str (int (val - new_origin_top)))
		else :
			print ('attrib ', 'head_top', ' not found')
		val = box.attrib.get ('left')
		if val != None :
			val = int (val)
			box.set ('left', str (int (val - new_origin_left)))
		else :
			print ('attrib ', 'left', ' not found')

		for part in box.findall ('./part') :
			val = part.attrib.get ('x')
			if val != None :
				val = int (val)
				part.set ('x', str (int (val - new_origin_left )))
			else :
				print ('attrib ', 'x', ' not found')
			val = part.attrib.get ('y')
			if val != None :
				val = int (val)
				part.set ('y', str (int (val - new_origin_top )))
			else :
				print ('attrib ', 'y', ' not found')

##------------------------------------------------------------
#   for each image in file if larger than max_dimension
#	  - downscale to max_dimension or min_face_size
#	  - if downscale to min_face_size, crop to max_dimension 
#	  - write image to parallel directory 
#		(imageSource ->imageSourceSmall)
#	  - write out xml with new info
##------------------------------------------------------------
def resize_face_file (orig_file, max_x=1500, max_y=2000, min_face_size=180) :

	root, tree = load_file (orig_file)
	print ('\n... processing file : ', orig_file)
	for image_tag in root.findall ('./images/image'):
		imgfile = image_tag.attrib.get ('file')
		ratio_downscale = get_downscale_ratio (imgfile, max_x, max_y)
		min_img_face_size = get_min_img_face_size (image_tag)
		ratio_min_face = min_face_size / min_img_face_size 
		print ('..... resizing ', imgfile)
		print ('\tface size: ', min_img_face_size) #-test
		if min_img_face_size < 150 :
			print ('\tface less than 150.')
		elif min_img_face_size < 224 :
			print ('\tface less than 224.')
		# print ('ratio_min_face: ', ratio_min_face, '\n') #-test
		# print ('ratio_downscale: ', ratio_downscale, '\n') #-test
		if ratio_min_face > 1 : # orig face smaller than min, don't downscale
			resized_image = Image.open (imgfile)
			# print ('no scaling \n') #-test
		elif ratio_downscale > ratio_min_face :	# larger ratio == less downscaling
			resized_image = downscale_image_and_boxes (imgfile, image_tag, ratio_downscale)
			# print ('scaling by image\n') #-test
		else :
			resized_image = downscale_image_and_boxes (imgfile, image_tag, ratio_min_face)
			# print ('scaling by min face\n') #-test
		resized_image = crop_image (resized_image, image_tag, max_x, max_y)
		new_imgfile = imgfile.replace ('imageSource', 'imageSourceSmall')
		new_imgfile_dir = os.path.dirname (new_imgfile)
		if not os.path.isdir (new_imgfile_dir) :
			os.makedirs (new_imgfile_dir)
		# imgfile_base, imgfile_ext = os.path.splitext (os.path.basename (imgfile)) #-test
		# new_imgfile = imgfile_base + '_resize' + imgfile_ext #-test
		# pdb.set_trace ()
		resized_image.save (new_imgfile)
		print ('\t... writing image to : ', new_imgfile)
		image_tag.set ('file', new_imgfile) # fix xml image_tag
	filebase, fileext = os.path.splitext (orig_file)
	new_file = filebase + '_resize' + fileext
	print("\n... writing new face xml : ", new_file, "\n\n")
	indent (root)
	# pdb.set_trace ()
	tree.write (new_file)
	return 

##------------------------------------------------------------
#   for each image in file, if larger than 1500 by 2000, 
#     - downscale image and face info
#	  - write image to parallel directory
#	  - write out xml with new info
##------------------------------------------------------------
def downscale_face_file (orig_file, max_size, path_replace) :

	root, tree = load_file (orig_file)
	ET.SubElement (root, 'command').text = get_argv ()
	print ('\n... downscaling : ', orig_file, ' to ', max_size, '\n')
	for image_tag in root.findall ('./images/image'):
		# get file and downscale
		imgfile = image_tag.attrib.get ('file')
		ratio = get_downscale_ratio (imgfile, max_size)
		downscaled_image = downscale_image_and_boxes (imgfile, image_tag, ratio)
		if path_replace[0] == '' :
			new_imgfile = './' + imgfile
		else :
			new_imgfile = imgfile.replace (path_replace[0], path_replace[1])
		new_imgfile_dir = os.path.dirname (new_imgfile)
		if not os.path.isdir (new_imgfile_dir) :
			os.makedirs (new_imgfile_dir)
		print ('\t... writing new image to: ', new_imgfile, '\n')
		downscaled_image.save (new_imgfile)
		image_tag.set ('file', new_imgfile) # fix xml image_tag

	filebase, fileext = os.path.splitext (orig_file)
	new_file = filebase + '_tiny' + fileext
	print("\n\t... writing new face xml : ", new_file, "\n\n")
	indent (root)
	# pdb.set_trace ()
	tree.write (new_file)
	return 

#---------------------------------------------------------------------------
#  load file, return root
#---------------------------------------------------------------------------
def load_file (file):
	tree = ET.parse (file)
	root = tree.getroot()
	return root, tree
	
##------------------------------------------------------------
##  load xml into dictionary of <string><element_list>
##  ex:  d["b-032"] = ["<Element 'chip' at 0x123,..,<Element 'chip' at 0x43]
##       d["b-747"] = ["<Element 'chip' at 0x987,..,<Element 'chip' at 0x65]
##  returns list of images
##------------------------------------------------------------
def load_objs (root, d_objs, filetype) :
	## print "loading chips"

	objects = []
	global g_stats_few
	global g_stats_many
	if filetype == 'chips' :
		for chip in root.findall ('./chips/chip'):
			label_list = chip.findall ('label')
			chipfile = chip.attrib.get ('file')
			if len (label_list) < 1 :
				g_stats_few.append (chipfile)
				print("no labels: ", label_list)
				continue
			if len (label_list) > 1 :
				g_stats_many.append (chipfile)
				print("too many labels: ", label_list)
				continue
			label = label_list[0].text
			objects.append (chipfile)
			d_objs[label].append(chip)
	elif filetype == 'images' :
		# pdb.set_trace ()
		for image in root.findall ('./images/image'):
			facefile = image.attrib.get ('file')
			objects.append (facefile)
	elif filetype == 'faces' :
		# pdb.set_trace ()
		multi_faces = defaultdict(lambda:0)
		for image in root.findall ('./images/image'):
			box = image.findall ('box')
			facefile = image.attrib.get ('file')
			multi_faces[len(box)] += 1
			if len (box) == 0 :
				g_stats_few.append (facefile)
				continue
			if len (box) > 1 :
				g_stats_many.append (facefile)
				print (len (box), " boxes (faces) in file ", facefile)
				continue
			label_list = box[0].findall ('label')
			label = label_list[0].text
			objects.append (facefile)
			d_objs[label].append(image)
		print ('\n    face count:')
		for key,val in multi_faces.items():
			print ('\t',key, ':', val)
	elif filetype == 'pairs' :
		matched = 0
		unmatched = 1
		matched_cnt = 0
		unmatched_cnt = 0
		# pdb.set_trace ()
		for pair in root.findall ('./pairs/pair_matched'):
			labels = pair.findall ('./chip/label')
			if len (labels) != 2 :
				print('error: expecting only 2 chips in pair, got: ', labels)
				continue
			if labels[0].text != labels[1].text :
				print('error: labels should match: ', labels)
			matched_cnt += 1
			d_objs[matched].append(labels[0])
		objects.append (d_objs[matched])
		for pair in root.findall ('./pairs/pair_unmatched'):
			labels = pair.findall ('./chip/label')
			if len (labels) != 2 :
				print('error: expecting only 2 chips in pair, got: ', labels)
				continue
			if labels[0].text == labels[1].text :
				print('error: labels should not match: ', labels)
			unmatched_cnt += 1
			d_objs[unmatched].append(labels)
		objects.append (d_objs[unmatched])
	elif filetype == 'embeddings' :
		for embedding in root.findall ('./embeddings/embedding'):    
			embed_val = embedding.find ('./embed_val')
			label = embedding.find ('./label')
			# pdb.set_trace ()
			embed_float = str_to_float (embed_val.text)
			d_objs[label.text].append(embed_float)
	else :
		print('Error: unknown filetype.  Expected one of "faces" or "chips" or "pairs".')
	return objects


##------------------------------------------------------------
##
##------------------------------------------------------------



##------------------------------------------------------------
##  print dictionary
##------------------------------------------------------------
def print_dict (chips_d) :
	for key, value in list(chips_d.items()):
		print(key)
		print(value)

##------------------------------------------------------------
##  ^^^^^^^^^^ START COMMENT ^^^^^^^^^^^^^^^^^^^^^^
##  ^^^^^^^^^^ END COMMENT ^^^^^^^^^^^^^^^^^^^^^^

##------------------------------------------------------------
##  partition all files into x and y percent
##------------------------------------------------------------
def generate_partitions (files, x, y, output, shuffle=True, img_cnt_min=0, test_min=0, image_size_min=0, filetype="chips") :
	# print "partitioning chips into: ", x, " ", y
	# pdb.set_trace ()
	# detect if chips file or faces file

	chips_d = defaultdict(list)
	load_objs_from_files (files, chips_d, filetype)
	chunks = partition_chips (chips_d, x, y, shuffle, img_cnt_min, test_min, image_size_min, filetype)
	# pdb.set_trace ()
	file_x = output + "_" + str(x) + ".xml"
	file_y = output + "_" + str(y) + ".xml"
	file_small_img = file_unused = None
	if len (chunks[g_unused]) > 0 :
		file_unused = output + "_unused" + ".xml"
	if len (chunks[g_small_img]) > 0 :
		file_small_img = output + "_small_faceMeta" + ".xml"
	filenames = [file_x, file_y, file_unused, file_small_img]
	generate_partition_files (chunks, filenames, filetype)

##------------------------------------------------------------
##  remove chips with resolution below min
##  returns list of tiny chips
##------------------------------------------------------------
def remove_tiny_chips (chips, image_size_min) :
	small_chips = []
	for i in range (len (chips)-1, 0, -1) :
		res = chips[i].find ('resolution')
		if int (res.text) < image_size_min :
			small_chips.append (chips.pop (i))
	return small_chips

##------------------------------------------------------------
##  given list of chips, return list of face images
##------------------------------------------------------------
def make_images_from_chips (chips) :
	faces = [chip.find ('source') for chip in chips] 
	for face in faces :
		face.tag = 'image'
	return faces

##------------------------------------------------------------
##  partition chips into x and y percent
##------------------------------------------------------------
def partition_chips (chips_d, x, y, shuffle=True, img_cnt_min=0, test_minimum=0, image_size_min=0, filetype="chips") :
	# print "partitioning chips into: ", x, " ", y
	# pdb.set_trace ()
	chunks = []
	if (shuffle == True) :  ## concat all labels, then split
		## TODO check for image_size_min
		all_chips=[]
		for label, chips in list(chips_d.items()):
			all_chips.extend (chips)
		if image_size_min != 0 :
			small_chips = remove_tiny_chips (all_chips, image_size_min)
		random.shuffle (all_chips)
		partition = int(round(len(all_chips) * float (x) / float (100)))
		# print "partition value : ", partition
		chunks.append (all_chips[:partition])
		chunks.append (all_chips[partition:])
		print("\nmixed partition of ", x, ", len : ", len (chunks[0]))
		print("shuffled partition of ", y, ", len : ", len (chunks[1]))
		print("shuffled total of ", len (chunks[0]) + len (chunks[1]))
		# print "chips count: ", len (all_chips)
	else :				## split per label, then combine into chunks
		# pdb.set_trace ()
		chunks_x = []
		chunks_y = []
		chunks_few = []
		labels_few = []
		small_images_chips = []
		chip_cnt = 0
		for label, chips in list(chips_d.items()):
			# remove chips below size minimum
			if image_size_min != 0 :
				small_images_chips.extend (remove_tiny_chips (chips, image_size_min))
			if len (chips) < img_cnt_min :
				chunks_few.extend (chips)
				labels_few.append (label)
				continue
			random.shuffle (chips)
			chip_cnt += len (chips)
			partition = int(round(len(chips) * float (x) / float (100)))
			chunks_x.extend (chips[:partition])
			chunks_y.extend (chips[partition:])
		chunks.append (chunks_x)
		chunks.append (chunks_y)
		print()
		print(len (chunks_x), ' chips in individual partition of', x)
		print(len (chunks_y), ' chips in individual partition of', y)
		print(chip_cnt, 'total', filetype)
		print()
		if len (labels_few) > 0 :
			chunks.append (chunks_few)
			print(len (labels_few), 'unused labels, each with less than ', img_cnt_min, 'images')
			# print labels_few
		else :
			print('All labels used.')
			chunks.append ([])
		if len (small_images_chips) :
			# files_small = [chip.attrib.get ('file') for chip in small_images_chips]
			# img_list = '\n   '.join (files_small)
			# print img_list
			print(len (small_images_chips), 'images unused due to size below', image_size_min)
			small_images_faces = make_images_from_chips (small_images_chips) 
			chunks.append (small_images_faces)
		else :
			print('All chips used.\n')
			chunks.append ([])

	# pdb.set_trace ()
	return chunks

##------------------------------------------------------------
##  split defaultdict<string><list> into n equal random parts
##  returns array  (list of n lists)
##  By default, all labels are combined, shuffled, then split.
##	If shuffle is False, shuffle each label, split, then added to chunks
##
##------------------------------------------------------------
def split_chips_into_n (chips_d, n, shuffle_mode) :
	chips_d_items = list(chips_d.items ())
	all_chips_cnt = sum ([len (chips) for label, chips in chips_d_items])
	mode_text = ''
	if shuffle_mode == 0 :  ## concat all labels, then split
		chunks=[]
		all_chips=[]
		for label, chips in chips_d_items :
			all_chips.extend (chips)
		random.shuffle (all_chips)
		chunk_size = len(all_chips) / float (n)
		print("\nshuffled fold size : ", int (chunk_size))
		print("chips count: ", all_chips_cnt)
		mode_text = 'All chips are mixed together then divided info each fold.'
		for i in range (n):
			start = int(round(chunk_size * i))
			end = int(round(chunk_size * (i+1)))
			# print "start : ", start
			# print "end : ", end
			chunks.append (all_chips[start:end])
	elif shuffle_mode == 1 :  ## split per label, then combine into chunks
		# pdb.set_trace ()
		chunks = [[] for i in range(n)]		# create n empty lists
		mode_text = '      chips of each label are split evenly into each fold.'
		for label, chips in chips_d_items :
			random.shuffle (chips)
			chunk_size = len(chips) / float (n)
			j = list(range(n))
			# randomize order of fold assignment since many labels
			# have few chips.  prevents single chips from all being
			# in same fold.
			random.shuffle (j)
			for i in range (n):
				start = int(round(chunk_size * i))
				end = int(round(chunk_size * (i+1)))
				chunks[j[i]].extend (chips[start:end])
	else :				## split across labels
		##  TODO : split labels here
		chunks = [[] for i in range(n)]		# create n empty lists
		random.shuffle (chips_d_items)
		# randomize order of fold assignment
		j = list(range(n))
		random.shuffle (j)
		chunk_size = len (chips_d_items) / float (n)
		# pdb.set_trace ()
		for i in range (n):
			start = int(round(chunk_size * i))
			end = int(round(chunk_size * (i+1)))
			labels_list = chips_d_items[start:end]
			for label, chips in labels_list :
				chunks[j[i]].extend (chips)
		print(len (chips_d), 'total labels, split into', n, 'folds = ~', int (len (chips_d) / float (n)))

	print(all_chips_cnt, 'total chips, split into', n, 'folds = ~', int (all_chips_cnt / float (n)))
	print('     ', mode_text)
	folds_cnt = [len (fold) for fold in chunks]
	labels_cnt = [[] for i in range (n)]
	for i in range (n) :
		labels = [(chip.find ('label')).text for chip in chunks[i]]
		labels_cnt[i] = len (set (labels))
	print('count per fold:')
	print('     ', folds_cnt, 'sum: ', sum (folds_cnt))
	print('labels per fold:')
	print('     ', labels_cnt)
	# pdb.set_trace ()
	return chunks

##------------------------------------------------------------
##  create n sets of trees of train & validate content
##  then write xml files
##------------------------------------------------------------
def generate_folds_files (train_list, validate_list, filename) :
	n = len (train_list)
	# write 2 files for each fold

	print("\nGenerated", n, "sets of folds files: ")
	for i in range(n) :
		t_root, t_chips = create_new_tree_w_element ()
		for j in range (len (train_list[i])) :
			chip = train_list[i][j]
			t_chips.append (chip)
		v_root, v_chips = create_new_tree_w_element ()
		for j in range (len (validate_list[i])) :
			chip = validate_list[i][j]
			v_chips.append (chip)
		tree_train = ET.ElementTree (t_root)
		tree_validate = ET.ElementTree (v_root)
		t_name = filename + "_train_" + str(i) + ".xml"
		v_name = filename + "_validate_" + str(i) + ".xml"
		indent (t_root)
		indent (v_root)
		tree_train.write (t_name)
		tree_validate.write (v_name)
		print("\t", t_name, "\n\t", v_name)
	print("")

##------------------------------------------------------------
##  create each xml tree for x and y partition
##  then write xml files
##------------------------------------------------------------
def generate_partition_files (chunks, filenames, filetype="chips") :
	list_x = chunks[g_x]
	list_y = chunks[g_y]
	file_x = filenames[g_x]
	file_y = filenames[g_y]
	file_unused = filenames[g_unused]
	file_small_img = filenames[g_small_img]

	root_x, chips_x = create_new_tree_w_element (filetype)
	for i in range(len(list_x)):
		chips_x.append (list_x[i])
	root_y, chips_y = create_new_tree_w_element (filetype)
	for i in range(len(list_y)):
		chips_y.append (list_y[i])

	indent (root_x)
	indent (root_y)
	tree_x = ET.ElementTree (root_x)
	tree_y = ET.ElementTree (root_y)
	tree_x.write (file_x)
	tree_y.write (file_y)
	print("\nGenerated partition files: \n\t", file_x, "\n\t", file_y)
	print("")

	if file_unused :
		list_unused = chunks[g_unused]
		root_unused, chips_unused = create_new_tree_w_element (filetype)
		for chip in list_unused :
			chips_unused.append (chip)
		indent (root_unused)
		tree_unused = ET.ElementTree (root_unused)
		tree_unused.write (file_unused)
		print('\t', len (list_unused), 'labels unused due to less than minimum # of images, written to file : \n\t', file_unused, '\n')
		print()
	if file_small_img :
		list_small_img = chunks[g_small_img]
		root_small, chips_small = create_new_tree_w_element ('faces')
		for i in range(len(list_small_img)):
			chips_small.append (list_small_img[i])
		indent (root_small)
		tree_small = ET.ElementTree (root_small)
		tree_small.write (file_small_img)
		print(len (list_small_img), 'unused chips below min size written to file : \n\t', file_small_img, '\n')
	print()

##------------------------------------------------------------
##  create n sets of train & validate files
##  split list into n chunks
##  foreach i in n: chunks[n] is in validate, the rest in train
##  returns list of train content and list of validate content
##     to be consumed by generate_folds_files
##------------------------------------------------------------
def generate_folds_content (chips_d, n_folds, shuffle=True) :
	n = int (n_folds)
	validate_list = []
	train_list = [[] for i in range(n)]
	chunks = split_chips_into_n (chips_d, n, shuffle)
	for i in range (n):
		validate_list.append (chunks[i])
		# pdb.set_trace()
		for j in range (n):
			if (j == i):
				continue
			train_list[i].extend (chunks[j])
	return train_list, validate_list

##------------------------------------------------------------
##  creates new tree, add standard file heading, 
##    then add specified element.  returns root and new element
##------------------------------------------------------------
def create_new_tree_w_element (filetype="chips") :
	r = ET.Element ('dataset')
	r_c = ET.SubElement (r, 'comment').text = 'generated by ' + g_exec_name
	curtime = datetime.datetime.now().strftime("%Y%m%d:%H%M")
	ET.SubElement (r, 'date').text = filetype + ' file generated at ' + curtime
	ET.SubElement (r, 'command').text = get_argv ()
	ET.SubElement (r, 'filetype').text = get_filetype ()
	if filetype in ['faces', 'images'] :
		elem_name = "images"
	else :
		elem_name = filetype
	r_elem = ET.SubElement (r, elem_name)
	return r, r_elem

##------------------------------------------------------------
##  
##------------------------------------------------------------
def write_file_with_label (xml_file_in, xml_file_out, key):
	tree_i = ET.parse (xml_file)
	root_i = tree.getroot()

	for chip in root_i.findall ('./chips/chip'):
		label_list = chip.findall ('label')
		if len (label_list) > 1 :
			print("too many labels: ", label_list)
			continue
		label = label_list[0].text
		if label != key :
			root.remove (chip)
	indent (root_i)
	tree_i.write (xml_file_out)

##------------------------------------------------------------
##
##------------------------------------------------------------
def unpath_chips (xml_files, append):
	# pdb.set_trace ()
	for xml_file in xml_files:
		root, tree = load_file (xml_file)
		for chip in root.findall ('./chips/chip'):
			label_list = chip.findall ('label')
			pathed_chipfile = chip.attrib.get ('file')
			unpathed_chipfile = os.path.basename (pathed_chipfile)
			# pdb.set_trace ()
			chip.set ('file', unpathed_chipfile)
			# print "   ", pathed_chipfile
			# print "  --->  ", unpathed_chipfile
		basename, ext = os.path.splitext(xml_file)
		if append:
			xml_file_unpathed = xml_file + "_unpathed"
		else:
			xml_file_unpathed = basename + "_unpathed" + ext
		# pdb.set_trace ()
		if get_verbosity () > 1 :
			print("\n\twriting unpath chips to file: ", xml_file_unpathed, "\n")
		indent (root)
		tree.write (xml_file_unpathed)

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
##   return flattened list of all image files (jpg, jpeg, png)
##------------------------------------------------------------
def get_dirs_images (inputdirs):
	imgs = []
	print ('getting images for : ', inputdirs)
	for inputdir in inputdirs :
		jpgs = list (Path(inputdir).rglob ("*.[jJ][pP][gG]"))
		jpegs = list (Path(inputdir).rglob ("*.[jJ][pP][eE][gG]"))
		png = list (Path(inputdir).rglob ("*.[pP][nN][gG]"))
		imgs.extend (jpgs)
		imgs.extend (jpegs)
		imgs.extend (png)
		# print ('\t jpgs: ', jpgs)
		# print ('\t jpegs: ', jpegs)
		# print ('\t png: ', png)
	return imgs

##------------------------------------------------------------
##  load objs from list of files into objs_d
##    if filename is directory, load all its xml files
##  objs_d is dictionary of <string><element_list>
##  ex:  d["b-032"] = ["<Element 'chip' at 0x123,..,<Element 'chip' at 0x43]
##       d["b-747"] = ["<Element 'chip' at 0x987,..,<Element 'chip' at 0x65]
##  return list of files in metadata
##------------------------------------------------------------
def load_objs_from_files (filenames, objs_d, filetype="chips"):
	objfiles = []
	# print "in load_objs_from_files"
	# pdb.set_trace ()
	## load all chips into objs_d
	# print("\nLoading", filetype, "for files: ")
	for file in filenames:
		print("\t", file)
		# pdb.set_trace()
		root, tree = load_file (file)
		objfiles.extend (load_objs (root, objs_d, filetype))
	# pdb.set_trace()
	return objfiles

##------------------------------------------------------------
##  filter chips :
##	  given list of chip files, and circle defined by
##    pt and distance, return chips with nose in circle
##------------------------------------------------------------
def filter_chips (infiles, pt, distance, outfile):
	chips_d = defaultdict(list)
	objfiles = load_objs_from_files (infiles, chips_d)
	l_eye, r_eye, nose, noses = get_chip_face_stats (chips_d)
	# pdb.set_trace ()
	if (pt[0] == 0) and (pt[1] == 0):
		nose_x = noses[0]
		nose_y = noses[1]
	else:
		nose_x = pt[0]
		nose_y = pt[1]
	if distance == 0: ## use 1/2 distance between eyes
		distance = (l_eye[0]-r_eye[0])/2
	chips_list, x_list, y_list, label_count = get_chips_noses_in_circle (
	    chips_d, nose_x, nose_y, distance)
	y_list_flip = []
	for y in y_list :
		y_list_flip.append (0-y)
	have_display = "DISPLAY" in os.environ
	if have_display:
		# plt.autoscale(enable=True, axis='both', tight=None)
		plt.axis('equal')
		plt.axis('off')
		plt.scatter (l_eye[0], 0-l_eye[1], c='blue', s=64)
		plt.scatter (r_eye[0], 0-r_eye[1], c='blue', s=64)
		plt.scatter (x_list, y_list_flip, c='green', s=16)
		plt.scatter (nose_x, 0-nose_y, c='red', s=128)
		#plt.imsave ("noses.jpg", format="png")
		plt.savefig ("nose_fig.png")
		plt.show ()
	write_chip_file (chips_list, outfile)
	print('----------------------------------')
	print('eyes:', r_eye, l_eye)
	print('center:', nose_x, nose_y)
	print('radius:', distance)
	print('----------------------------------')
	print(len (x_list), 'chips matched from', chips_count (chips_d))
	print('with', label_count, 'labels from original', len (chips_d))
	print('  chips written to file:', outfile)
	print('')
	# pdb.set_trace ()

##------------------------------------------------------------
##  return count of chips in dict
##------------------------------------------------------------
def chips_count (chips_d):
	count = 0
	for key, chips in sorted(chips_d.items()): ## list of chips
		count += len (chips)
	return count

##------------------------------------------------------------
##  return chips with noses within
## 	 circle of radius d, centered at x,y
##------------------------------------------------------------
def get_chips_noses_in_circle (chips_d, pt_x, pt_y, distance):
	x_list = []
	y_list = []
	filtered_chips = []
	# pdb.set_trace ()
	## comparing with squares since sqrt is slow
	distance = distance**2
	label_count = 0
	for key, chips in sorted(chips_d.items()): ## list of chips
		chip_count = 0
		for chip in chips:
			for part in chip.findall ('part'):
				name = part.attrib.get ('name')
				if name == "nose" :
					nose_x = int (part.attrib.get ('x'))
					nose_y = int (part.attrib.get ('y'))
					## check to see if within specified dist
					d = (pt_x-nose_x)**2 + (pt_y-nose_y)**2
					if d <= distance:
						x_list.append (nose_x)
						y_list.append (nose_y)
						filtered_chips.append (chip)
						chip_count = 1
		if chip_count > 0:
			label_count += 1
	return filtered_chips, x_list, y_list, label_count

##------------------------------------------------------------
##  given chip list, write to xml file
##------------------------------------------------------------
def write_chip_file (chips, outfile):
	root, chips_elem = create_new_tree_w_element ()
	for chip in chips:
		chips_elem.append (chip)
	indent (root)
	tree = ET.ElementTree (root)
	tree.write (outfile)

##------------------------------------------------------------
##  given list, write to xml file
##------------------------------------------------------------
def write_xml_file (outfile, tags, filetype):
	root, tags_elem = create_new_tree_w_element (filetype)
	for tag in tags :
		tags_elem.append (tag)
	indent (root)
	tree = ET.ElementTree (root)
	tree.write (outfile)

##------------------------------------------------------------
##  get chip face stats :
##       nose (x, y), eye1 (x,y), eye2 (x, y), eye dist
##    collect all nose_x, nose_y, get average
##    get first chip, extract eye1, eye2, get distance
##------------------------------------------------------------
def chip_face_stats (filenames):
	chips_d = defaultdict(list)
	objfiles = load_objs_from_files (filenames, chips_d)
	l_eye, r_eye, nose, noses = get_chip_face_stats (chips_d)
	have_display = "DISPLAY" in os.environ
	if not have_display:
		return
	display_hist_heat (noses)
	display_hist (noses)
	band_width, bands = get_dist_hist (noses)
	default_dist = (l_eye[0] - r_eye[0]) / 2
	display_dist_hist (bands, band_width, default_dist)
	plt.show ()

##------------------------------------------------------------
##  plot nose dist histogram
##------------------------------------------------------------
def display_dist_hist (bands, band_width, default_dist=0, label_x='', label_y='', title=''):
	band_label = [(x+1) * band_width for x in range(len(bands))]
	# pdb.set_trace ()
	# plt.autoscale(enable=True, axis='both', tight=None)
	# plt.axis('equal')
	fig3 = plt.figure()
	if not title :
		plt.title ('distance histogram. default @' + str (default_dist))
	plt.axis('on')
	if not label_y :
		plt.ylabel('face count')
	if not label_x :
		plt.xlabel('distance')
	plt.bar (band_label, bands, 7, color='green')
	if default_dist :
		plt.bar (default_dist, max(bands), 7, color='red')
	# plt.scatter (band_label, bands, c='green', s=16)
	# plt.savefig ("nose_fig.png")

##------------------------------------------------------------
##  plot histogram heatmap
##------------------------------------------------------------
def display_hist_heat (noses):
	x = noses[0]
	y = noses[1]
	# Plot data
	fig1 = plt.figure()
	plt.title ('nose histogram.')
	plt.plot(x,y,'.r')
	plt.xlabel('x')
	plt.ylabel('y')

	# Estimate the 2D histogram
	nbins = 10
	H, xedges, yedges = np.histogram2d(x,y,bins=nbins)

	# H needs to be rotated and flipped
	H = np.rot90(H)
	H = np.flipud(H)

	# Mask zeros
	Hmasked = np.ma.masked_where(H==0,H) # Mask pixels with a value of zero

	# Plot 2D histogram using pcolor
	fig2 = plt.figure()
	plt.title ('nose histogram heat map: ' + str (nbins) + ' bins.')
	plt.pcolormesh(xedges,yedges,Hmasked)
	plt.xlabel('x')
	plt.ylabel('y')
	cbar = plt.colorbar()
	cbar.ax.set_ylabel('Counts')
	# plt.show ()

##------------------------------------------------------------
## return list of paired tuple
##------------------------------------------------------------
def create_tuple_pair (label1, image1, label2, image2):
	return ((label1, image1), (label2, image2))

##------------------------------------------------------------
## generate all possible index pairs of images of given label
## return list of list.  one list per label of all combination
##		for that label
##------------------------------------------------------------
def gen_all_matched_obj_pairs  (chips_d):
	matched_lists = []
	matched_pairs = []
	chips_list = sorted(chips_d.items())
	label_count = len (chips_list)
	for label1 in range (label_count) :		# for each label
		matched_pairs = []
		chip1s_cnt = len (chips_list[label1][1])
		# pdb.set_trace ()
		for i in range (chip1s_cnt) :		# iterate thru images
			for j in range (i+1, chip1s_cnt) :
				pairs = create_tuple_pair (label1, i, label1, j)
				matched_pairs.append (pairs)
		# pdb.set_trace ()
		matched_lists.append (matched_pairs)
	# pdb.set_trace ()
	return matched_lists

##------------------------------------------------------------
## generate all possible index pairs of images of different labels
## return array of lists.  List indices >= to first index will be null.
## i.e. len (lists[4][2]) = 0 . len (lists [2][4] = unmatched pairs
##      for bear 2 and bear 4
##   e.g. unmatched images for labels 5, 3 ##   will be in lists[3][5]
## Need to have this table to counter labels with lots of images.
##   If we were to only generate list of unmatched images for a
##   label, it would be weighted towards the labels with greater
##   images.  To use this table, select a random label1, then a 
##   random label2, then select random entry of list in this table.
##------------------------------------------------------------
def gen_all_unmatched_obj_pairs  (chips_d):
	unmatched_lists = []
	unmatched_sublist = []
	unmatchted_pairs = []
	chips_list = sorted(chips_d.items())
	label_count = len (chips_list)
	for label1 in range (label_count) :
		unmatched_sublist = []
		for x in range (label1+1) : # empty out lower indices
			unmatched_sublist.append ('')
		chip1s_cnt = len (chips_list[label1][1])
		for label2 in range (label1+1, label_count) :
			unmatched_pairs = []
			chip2s_cnt = len (chips_list[label2][1])
			for i in range (chip1s_cnt) :
				for j in range (chip2s_cnt) :
					pairs = create_tuple_pair (label1, i, label2, j)
					unmatched_pairs.append (pairs)
			unmatched_sublist.append (unmatched_pairs)
		# pdb.set_trace ()
		unmatched_lists.append (unmatched_sublist)
	return unmatched_lists

##------------------------------------------------------------
## write out N pairs of matched pairs and M pairs of unmatched pairs
##------------------------------------------------------------
def generate_chip_pairs (input_files, matched_cnt, unmatched_cnt, triplets, output):
	chips_d = defaultdict(list)
	load_objs_from_files (input_files, chips_d)
	if triplets > 0 :
		unmatched_cnt = matched_cnt = triplets
	selected_matched_indices, selected_unmatched_indices = get_selected_pair_indices (chips_d, matched_cnt, unmatched_cnt, triplets)
	matched_chips = create_chip_list (chips_d, selected_matched_indices)
	unmatched_chips = create_chip_list (chips_d, selected_unmatched_indices)

	## create xml content
	root, chips = create_new_tree_w_element ('pairs')
	elem_name = "pair_matched"
	for i in range (0, len (matched_chips), 2) :
		# create new matched pair element, then put 2 chips under it
		pair = ET.SubElement (chips, elem_name)
		pair.append (matched_chips[i])
		pair.append (matched_chips[i+1])
		# pdb.set_trace ()
	elem_name = "pair_unmatched"
	for i in range (0, len (unmatched_chips), 2) :
		# create new matched pair element, then put 2 chips under it
		pair = ET.SubElement (chips, elem_name)
		pair.append (unmatched_chips[i])
		pair.append (unmatched_chips[i+1])

	# pdb.set_trace ()
	if matched_cnt == 0 :
		matched_cnt = len (selected_matched_indices)
	if unmatched_cnt == 0 :
		unmatched_cnt = len (selected_unmatched_indices)
	## write out file
	print('\nWriting', matched_cnt, 'matched pairs and', unmatched_cnt, 'unmatched pairs to file:')
	print('\t', output, '\n')
	indent (root)
	tree = ET.ElementTree (root)
	tree.write (output)

##------------------------------------------------------------
##  return two lists of pairs for matched and unmatched
##    generate a list of all possible indices for matching and 
##    unmatching pairs for each label.  store in table of labels
##    select random label, then select random un/matching pair of label
##------------------------------------------------------------
def get_selected_pair_indices (chips_d, matched_cnt, unmatched_cnt, triplet=0) :
	all_matched_pairs_arr = gen_all_matched_obj_pairs (chips_d)
	all_unmatched_pairs_3arr = gen_all_unmatched_obj_pairs (chips_d)
	selected_matched_list = []
	selected_unmatched_list = []
	label_cnt = len (chips_d)
	max_matched_cnt = sum ([len (pairs_list) for pairs_list in all_matched_pairs_arr])
	max_unmatched_cnt = sum ([len (pairs_list) for pairs_arr in all_unmatched_pairs_3arr for pairs_list in pairs_arr])

	# pdb.set_trace ()
	if matched_cnt == 0 :
		matched_cnt = max_matched_cnt
	if matched_cnt > max_matched_cnt :
		print('  *** requesting more matched pairs than exists.')
		print('  *** creating max number of matched pairs.')
		matched_cnt = max_matched_cnt
	if unmatched_cnt == 0 :
		unmatched_cnt = max_unmatched_cnt
	if unmatched_cnt > max_unmatched_cnt :
		print('  *** requesting more unmatched pairs than exists.')
		print('  *** creating max number of unmatched pairs.')
		unmatched_cnt = max_unmatched_cnt
	# pdb.set_trace ()
	# need to start with matched set to ensure there is a set
	i = 0
	if matched_cnt == max_matched_cnt :  # getting ALL matched pairs
		selected_matched_list = [pair for pair_list in all_matched_pairs_arr for pair in pair_list]
		i = matched_cnt
	while i < matched_cnt :
		x = random.randint(0,label_cnt-1)
		img_cnt = len (all_matched_pairs_arr[x])
		if img_cnt == 0 :
			continue
		label_list = all_matched_pairs_arr[x]
		z = random.randint(0,img_cnt-1)
		# if looking for triplet, find unmatched set now
		if triplet > 0 :
			w = random.randint(0, 1)  # pick one of 2 sets
			set1 = label_list[z][w]	  # anchor
			label_y = label_x = set1[0]
			while label_y == label_x :
				label_y = random.randint(0,label_cnt-1)
			if label_x > label_y :
				label_list_u = all_unmatched_pairs_3arr[label_y][label_x]
			else :
				label_list_u = all_unmatched_pairs_3arr[label_x][label_y]
			img_cnt_u = len (label_list_u)
			#   need to find anchor set1 then move entry to selected
			found_match = False
			for u in range (img_cnt_u-1) :
				# pdb.set_trace ()
				if set1 in label_list_u[u]:  # take first match rather than find all and random select
					selected_unmatched_list.append (label_list_u.pop(u))
					found_match = True
					break
			if not found_match :
				print('Unable to find unmatch set for anchor', set1, ', trying again.')
				continue
		selected_matched_list.append (label_list.pop(z))
		i += 1
	if triplet > 0 :
		return selected_matched_list, selected_unmatched_list
	i = 0
	if unmatched_cnt == max_unmatched_cnt :  # getting ALL unmatched pairs
		selected_unmatched_list = [pair for pairs_arr in all_unmatched_pairs_3arr for pair_list in pairs_arr for pair in pair_list]
		i = unmatched_cnt
	while i < unmatched_cnt :
		y = x = random.randint(0,label_cnt-1)
		while y == x :
			y = random.randint(0,label_cnt-1)
		if x > y :
			label_list = all_unmatched_pairs_3arr[y][x]
		else :
			label_list = all_unmatched_pairs_3arr[x][y]
		# pdb.set_trace ()
		img_cnt = len (label_list)
		if img_cnt == 0 :
			continue
		z = random.randint(0,img_cnt-1)
		# move entry to selected
		selected_unmatched_list.append (label_list.pop(z))
		i += 1
	return selected_matched_list, selected_unmatched_list

##------------------------------------------------------------
##  create lists of chips pairs given indices in the form:
##    [ ((l1, image1), (l2, image2)), ... ]
##------------------------------------------------------------
def create_chip_list (chips_d, indices) :
	chips_list = sorted (chips_d.items())
	chips = []
	#  label, chips in chips_d.items():
	for pair in indices :
		l1 = pair[0][0]
		i1 = pair[0][1]
		l2 = pair[1][0]
		i2 = pair[1][1]
		# print '((', l1, i1, '), (', l2, i2, '))'
		# l, 1, i : is to access the list of (label,chips)
		chip1 = chips_list[l1][1][i1]
		chip2 = chips_list[l2][1][i2]
		chips.append (chip1)
		chips.append (chip2)
	return chips

##------------------------------------------------------------
##  plot histogram of points, of nxn bins
##------------------------------------------------------------
def display_hist (noses):
	fig = plt.figure()
	ax = fig.add_subplot(111, projection='3d')
	# x, y = np.random.rand(2, 100) * 4
	x = noses[0]
	y = noses[1]
	nbins = 10
	hist, xedges, yedges = np.histogram2d(x, y, bins=nbins)

	# Note: np.meshgrid gives arrays in (ny, nx) so we use 'F' to flatten xpos,
	# ypos in column-major order. For numpy >= 1.7, we could instead call meshgrid
	# with indexing='ij'.
	# xpos, ypos = np.meshgrid(xedges[:-1] + 0.25, yedges[:-1] + 0.25)
	plt.title ('nose histogram : ' + str (nbins) + ' bins.')
	xpos, ypos = np.meshgrid(xedges[:-1] + 1.0, yedges[:-1] + 1.0)
	xpos = xpos.flatten('F')
	ypos = ypos.flatten('F')
	zpos = np.zeros_like(xpos)

	# Construct arrays with the dimensions for the 16 bars.
	#dx = 0.5 * np.ones_like(zpos)
	dx = 1.0 * np.ones_like(zpos)
	dy = dx.copy()
	dz = hist.flatten()

	ax.bar3d(xpos, ypos, zpos, dx, dy, dz, color='y', zsort='average')
	# plt.show()

##------------------------------------------------------------
##  plot distance histogram from mean.
##------------------------------------------------------------
def get_dist_hist (noses, band_width=0):
	x_list = noses[0]
	y_list = noses[1]
	sorted_x = sorted (x_list)
	sorted_y = sorted (y_list)
	nose_x = sum (x_list) / len (x_list)
	nose_y = sum (y_list) / len (y_list)
	band_count = 30
	if band_width == 0 :
		x_dist = sorted_x[-1] - sorted_x[0]
		y_dist = sorted_y[-1] - sorted_y[0]
		dist = math.sqrt (x_dist**2 + y_dist**2)
		band_width = int (dist/band_count)
	bands = [0] * (band_count + 1)
	# pdb.set_trace ()
	for i in range (len (y_list)) :
		pt_x = x_list[i]
		pt_y = y_list[i]
		d = math.sqrt ((pt_x-nose_x)**2 + (pt_y-nose_y)**2)
		band = int (d/band_width)
		bands[band] += 1
	print('nose count: ', len (x_list))
	end = len (bands) - 1
	# pdb.set_trace ()
	for i in range (end, 0, -1) :
		if bands[i] :
			end = i+1
			break
	cnt = 0
	for i in range (len(bands)) :
		print('---   ', i, ':', bands[i])
		cnt += bands[i]
	print('# bands : ', end)
	print('band width     : ', band_width)
	print('total in bands : ', cnt)
	return band_width, bands[:end]

##------------------------------------------------------------
##  given dict of chips, return eyes and list of noses
##------------------------------------------------------------
def get_chip_face_stats (chips_d, verbose=1):
	x_list = []
	y_list = []
	# pdb.set_trace ()
	get_reye = True
	get_leye = True
	all_chips = sorted(chips_d.items())
	for key, chips in all_chips :  ## list of chips
		for chip in chips :
			for part in chip.findall ('part'):
				name = part.attrib.get ('name')
				if get_leye :
					if name == "leye" :
						leye_x = int (part.attrib.get ('x'))
						leye_y = int (part.attrib.get ('y'))
						get_leye = False
						continue
				if get_reye :
					if name == "reye" :
						reye_x = int (part.attrib.get ('x'))
						reye_y = int (part.attrib.get ('y'))
						get_reye = False
						continue
				if name == "nose" :
					x = int (part.attrib.get ('x'))
					y = int (part.attrib.get ('y'))
					x_list.append (x)
					y_list.append (y)
	nose_x = sum (x_list) / len (x_list)
	nose_y = sum (y_list) / len (y_list)
	if verbose > 0 :
		print('average nose : ', nose_x, nose_y)
		print('median  nose : ', np.median (x_list), np.median (y_list))
		print('reye : ', reye_x, reye_y)
		print('leye : ', leye_x, leye_y)
	return [leye_x, leye_y], [reye_x, reye_y], [nose_x, nose_y], [x_list, y_list]

##------------------------------------------------------------
##  print pairs stats
##------------------------------------------------------------
def print_pairs_stats (objs_d) :
	matched = 0
	unmatched = 1
	matched_list = objs_d[matched]
	unmatched_list = objs_d[unmatched]
	# pdb.set_trace ()

	# get unique list of entries, then show count
	matched_labels = [label.text for label in matched_list]
	unmatched_labels = [(label[0].text, label[1].text) for label in unmatched_list]

	flatten_unmatched = [label for tupl in unmatched_labels for label in tupl]
	print('------------------------')
	print('--- matched stats:--- ')
	print('------------------------')
	for i in sorted (set (all_labels)):
		print(i, '\t,\t', matched_labels.count (i))
	print('------------------------')
	print('total : ', len (matched_labels))

	print('------------------------')
	print('--- unmatched stats:--- ')
	print('------------------------')
	for i in sorted (set (all_labels)):
		print(i, '\t,\t', flatten_unmatched.count (i))
	print('unmatched pairs: ', len (unmatched_labels))

##------------------------------------------------------------
##  prints: 
##     min size, 
##     max size, 
##	   resolution of min image, 
##     resoulution of max image
##     count of each diffent types of images 
##        img.format (), img.size 
##------------------------------------------------------------
def print_imgs_stats (img_files) :
	imgs_d = defaultdict(int)
	# print (len (img_files), ': ', img_files)
	for i in range (len (img_files)) : 	# all labels
		img = Image.open (img_files[i])
		imgs_d [img.format] += 1
		if img.format == 'MPO' :
			mpo_file = img_files[i]
		width, height = img.size
		size = width * height
		if i == 0 :
			min_size = size
			max_size = size
			min_img = img
			max_img = img
			min_img_file = img_files[i]
			max_img_file = img_files[i]
		if size < min_size :
			min_size = size
			min_img = img
			min_img_file = img_files[i]
		elif size > max_size :
			max_size = size
			max_img = img
			max_img_file = img_files[i]
	print ('min image : ', min_img_file)
	print ('resolution: ', min_img.width, min_img.height)
	print ('min size  : ', min_size)
	print ('max image : ', max_img_file)
	print ('resolution: ', max_img.width, max_img.height)
	print ('max size  : ', max_size)

	for img_format, count in imgs_d.items () :  ## iterate through all chips
		print (img_format, ' : ', count)
	print ('\n\t MPO : ', mpo_file)
	return

##------------------------------------------------------------
##  return label stats in file
##------------------------------------------------------------
def get_obj_stats (filenames, print_files=False, filetype="chips", verbosity=1, write_stats=False):
	objs_d = defaultdict(list)
	objfiles = load_objs_from_files (filenames, objs_d, filetype)
	# pdb.set_trace ()
	if filetype == "images" :
		print_imgs_stats (objfiles)
		return
	if filetype == "pairs" :
		print_pairs_stats (objs_d)
		return
	print('')
	all_objs = sorted(objs_d.items())
	img_cnt_per_label = [len (objs) for key, objs in all_objs]
	obj_count = sum (img_cnt_per_label)
	if get_verbosity () > 1 :
		for label in sorted (set (all_labels)):
			if get_verbosity () > 2 or len (objs_d[label]) > 0 :
				print(label, '	,	', len (objs_d[label]))
	u_combos = 0
	chips_count_list = img_cnt_per_label
	diff_chip_count  = obj_count
	# pdb.set_trace ()
	for i in range (len (chips_count_list)-1) : 	# all labels
		i_count = len (all_objs[i][1])			# count of ith label
		diff_chip_count -= i_count				# count of different labels
		u_combos += (i_count * diff_chip_count)

	print('-----------------------------')
	print('            total', filetype, ':', obj_count)
	print('                # bears :', len (chips_count_list))
	if len (chips_count_list) > 0:
		print(' average', filetype, 'per bear :', obj_count / len (chips_count_list))
		print('  median', filetype, 'per bear :', np.median (img_cnt_per_label))
	combos = sum ([(n*(n-1)/2) for n in img_cnt_per_label if n > 1])
	print('  possible matched sets :', combos)
	print('possible unmatched sets :', u_combos)
	# display_dist_hist (img_cnt_per_label, 2, 0, 'bear index', '# images')
	have_display = "DISPLAY" in os.environ
	if (get_verbosity () > 2) :
		if have_display:
			#plt.hist(img_cnt_per_label, len(objs_d)/5, facecolor='blue', alpha=0.5)
			hist_info = plt.hist(img_cnt_per_label, 20, facecolor='blue', alpha=0.5)
			plt.title('histogram of ' + filetype + ' count per bear')
			plt.xlabel('# chips per bear (total=' + str (obj_count) + ')')
			plt.ylabel('# bears (total=' + str (len (objs_d)) + ')')
			hist_obj_cnt_file = 'hist_obj_cnt.png'
			plt.savefig (hist_obj_cnt_file)
			print('\n--- histogram of image count written to: ', hist_obj_cnt_file, '\n')
			plt.show ()
			if filetype == 'chips' :
				chip_sizes = [math.sqrt (int (res.text)) for key, chips in all_objs \
					for chip in chips for res in chip.findall ('resolution')]
				print('\naverage face size (NxN): ', int (sum (chip_sizes)/len (chip_sizes)))
				print('median face size  (NxN): ', int (np.median (chip_sizes)))
				plt.title ('histogram of of face sizes')
				plt.xlabel ('N (image size=NxN)')
				plt.ylabel ('# chips (total=' + str (obj_count) + ')' )
				hist_info = plt.hist (chip_sizes, 20, facecolor='green', alpha=0.5)
				hist_chip_sizes_file = 'hist_chip_sizes.png'
				plt.savefig (hist_chip_sizes_file)
				print('\n--- histogram of chip sizes written to: ', hist_chip_sizes_file, '\n')
				plt.show ()
				tiny_chips = [chip for key, chips in all_objs \
					for chip in chips for res in chip.findall ('resolution') if int (res.text) < 22500]
				chip.attrib.get ('file')
				tiny_chips_names = [chip.attrib.get ('file') for chip in tiny_chips]
				# pdb.set_trace ()

		else :
			print('\n  ***  unable to show histogram: no access to display.  *** \n')

	if filetype == 'faces':
		print_faces_stats (write_stats)
	if print_files :
		objfiles.sort ()
		for objfile in objfiles:
			print('\t', objfile)

##------------------------------------------------------------
##------------------------------------------------------------
##------------------------------------------------------------
def is_png (image_file) :
	imgfile_base, imgfile_ext = os.path.splitext (image_file)
	if imgfile_ext.lower() == '.png' :
		return True
	else :
		return False

##------------------------------------------------------------
##------------------------------------------------------------
def get_YMD_from_date (image_date) :
	# pdb.set_trace ()
	if image_date is None:
		return 0, 0, 0
	image_year = image_date[:4]
	image_month = image_date[5:7]
	image_day = image_date[8:10]
	return image_year, image_month, image_day

##------------------------------------------------------------
##------------------------------------------------------------
def get_image_creation_date (image_file):
	# pdb.set_trace ()
	if is_png (image_file) :
		return ''
	print ('image: ', image_file)
	img = Image.open (image_file)
	exif_data = img._getexif ()
	if exif_data != None :
		date = exif_data.get (36867)
		return date
	else :
		return ''

##------------------------------------------------------------
##------------------------------------------------------------
def get_photo_source (image_file):
	label_path = os.path.dirname (image_file)
	source_path = os.path.dirname (label_path)
	source_split = os.path.split (source_path)
	return source_split [1]

##------------------------------------------------------------
##------------------------------------------------------------
def get_image_size (image_file):
	img = Image.open (image_file)
	w,h = img.size
	return w * h

##------------------------------------------------------------
##------------------------------------------------------------
def get_orig_img_by_name (image_file, cur_str, orig_str):
	str_index = image_file.find (cur_str)
	if str_index > 0 :
		orig_image_file = image_file.replace (cur_str, orig_str)
		if not os.path.exists (orig_image_file) :
			print ('   Warning: orig image ', orig_image_file, 'does not exist')
		return orig_image_file
	return ''

##------------------------------------------------------------
##------------------------------------------------------------
def trim_path_start (pathname, dir_depth) :
	path = pathname
	for i in range (dir_depth) :
		path = os.path.dirname (path)
	# pdb.set_trace ()
	path += '/'
	rel_pathname = pathname.replace (path, '')
	return rel_pathname

##------------------------------------------------------------
##------------------------------------------------------------
def get_nose_xy (chip_tag):
	for part in chip_tag.findall ('part'):
		name = part.attrib.get ('name')
		if name == "nose" :
			nose_x = int (part.attrib.get ('x'))
			nose_y = int (part.attrib.get ('y'))
			return nose_x, nose_y

##------------------------------------------------------------
##------------------------------------------------------------
def get_face_size (image_tag):
	# pdb.set_trace ()
	box = image_tag.find ('box')
	if box is None:
		return 0
	height = box.attrib.get ('height')
	width = box.attrib.get ('width')
	if height and width :
		face_size = int (height) * int (width)
	else:
		face_size = 0
	return face_size

##------------------------------------------------------------
##  return string with content:
##    	file, label, date, size, photo_source,
##		nose_xy, nose_source_file, orig_image, permission?, age
##------------------------------------------------------------
def gen_image_csv_str (image_tag):
	# pdb.set_trace () 
	image_label = get_obj_label_text (image_tag)
	image_file = image_tag.attrib.get ('file')
	image_date = get_image_creation_date (image_file)
	image_year, image_month, image_day = get_YMD_from_date (image_date)
	photo_source = get_photo_source (image_file)
	image_size = get_image_size (image_file)
	face_size = get_face_size (image_tag)
	if get_verbosity () > 1 :
		print ('file   : ', image_file)
		print ('label  : ', image_label)
		print ('date   : ', image_date)
		print ('source : ', photo_source)
		print ('size   : ', image_size)
		print('-----------------------------')
	csv_str = trim_path_start (image_file, 5)
	csv_str += ';' + image_label
	csv_str += ';' + str (image_date)
	csv_str += ';' + str (image_year)
	csv_str += ';' + str (image_month)
	csv_str += ';' + str (image_day)
	csv_str += ';' + str (image_size)
	csv_str += ';' + trim_path_start (photo_source, 5)
	csv_str += ';' + str (face_size)
	return csv_str

##------------------------------------------------------------
##  return string with content:
##    	file, label
##------------------------------------------------------------
def gen_svm_csv_str (image_tag):
	# pdb.set_trace () 
	image_label = get_obj_label_text (image_tag)
	image_file = image_tag.attrib.get ('file')
	truth_label = get_truth_label (image_file)
	if truth_label == image_label :
		match = '1'
	else :
		match = '0'
	if get_verbosity () > 1 :
		print ('file   : ', image_file)
		print ('label  : ', image_label)
		print('-----------------------------')
	csv_str = trim_path_start (image_file, 5)
	csv_str += ';' + image_label
	csv_str += ';' + truth_label
	csv_str += ';' + match
	return csv_str

##------------------------------------------------------------
##  return string with content:
##    	file, label, size,
##		nose_xy, orig_image
##------------------------------------------------------------
def gen_chip_csv_str (chip_tag):
	image_file = chip_tag.attrib.get ('file')
	image_label = get_obj_label_text (chip_tag)
	image_size = get_image_size (image_file)
	orig_file = get_chip_source (chip_tag)
	nose_x, nose_y = get_nose_xy (chip_tag)
	if get_verbosity () > 1 :
		print ('file      : ', image_file)
		print ('label     : ', image_label)
		print ('size      : ', image_size)
		print ('orig_file : ', orig_file)
		print ('nose_xy   : ', nose_x, nose_y)
		print('-----------------------------')
	csv_str = trim_path_start (image_file, 5)
	csv_str += ';' + image_label
	csv_str += ';' + str (image_size)
	csv_str += ';' + trim_path_start (orig_file, 5)
	csv_str += ';' + str (nose_x) + ' ' + str (nose_y)
	csv_str += ';' + str (nose_x)
	csv_str += ';' + str (nose_y)
	return csv_str

##------------------------------------------------------------
##  return string with content:
##    	file, label, date, size
##		nose_xy, nose_source_file, orig_image, permission?, age
##------------------------------------------------------------
def gen_derived_image_csv_str (image_tag):
	image_label = get_obj_label_text (image_tag)
	image_file = image_tag.attrib.get ('file')
	image_size = get_image_size (image_file)
	orig_image = get_orig_img_by_name (image_file, 'imageSourceSmall', 'imageSource')
	permission = ''
	face_size = get_face_size (image_tag)
	age = ''
	if get_verbosity () > 1 :
		print ('file   : ', image_file)
		print ('label  : ', image_label)
		print ('size   : ', image_size)
		print ('orig   : ', orig_image)
		print('-----------------------------')
	csv_str = trim_path_start (image_file, 5)
	csv_str += ';' + image_label
	csv_str += ';' + str (image_size)
	csv_str += ';' + trim_path_start (orig_image, 5)
	csv_str += ';' + str (face_size)
	return csv_str

##------------------------------------------------------------
##  write csv file of image info containing:
##    filename, label, date, location??, source (level above label)
##------------------------------------------------------------
def write_image_info_csv (filenames, outfile, filetype):
	objs_d = defaultdict(list)
	objtype = filetype
	if objtype == 'derived_faces' or objtype == 'svm':
		objtype = 'faces'
	objfiles = load_objs_from_files (filenames, objs_d, objtype)

	csv_fp = open (outfile, "w")

	# images, derived_image: images/image
	# chips: chips/chip
	# pdb.set_trace ()
	for label, tags in list(objs_d.items ()) :
		for tag in tags:
			# pdb.set_trace ()
			if filetype == 'faces' :
				image_csv = gen_image_csv_str (tag)
			elif filetype == 'derived_faces' :
				image_csv = gen_derived_image_csv_str (tag)
			elif filetype == 'chips' :
				image_csv = gen_chip_csv_str (tag)
			elif filetype == 'svm' :
				image_csv = gen_svm_csv_str (tag)
			csv_fp.write (image_csv + '\n')
	csv_fp.close ()
	print("... generated file:", outfile)

##------------------------------------------------------------
##
##------------------------------------------------------------


##------------------------------------------------------------
##
##------------------------------------------------------------
def print_faces_stats (write_unused_images) :
	print("-----------------------------")
	print("....files with no faces      : ", len (g_stats_few))
	print("....files with multiple faces: ", len (g_stats_many))
	# pdb.set_trace ()
	if write_unused_images:
		if len (g_stats_few) :
			stats_name = datetime.datetime.now().strftime("stats_few_%Y%m%d_%H%M")
			stats_fp = open (stats_name, "w")
			for face in g_stats_few:
				stats_fp.write (face + '\n')
			stats_fp.close ()
			print("... generated file:", stats_name)
		if len (g_stats_many) :
			stats_name = datetime.datetime.now().strftime("stats_many_%Y%m%d_%H%M")
			stats_fp = open (stats_name, "w")
			for face in g_stats_many:
				stats_fp.write (face + '\n')
			stats_fp.close ()
			print("... generated file:", stats_name)
	print('')

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
##  write list of images into output_file xml
##------------------------------------------------------------
def create_imgs_xml (img_list, output_file) :
	img_files = get_img_files (img_list)
	root, images_tag = create_new_tree_w_element ('images')
	# pdb.set_trace ()
	for img_file in img_files :
		image_tag = ET.SubElement (images_tag, 'image')
		image_tag.set ('file', str (img_file))
	indent (root)
	tree = ET.ElementTree (root)
	tree.write (output_file)
	print('\n\tGenerated images file: ', output_file)

##------------------------------------------------------------
##  return images files in (sub)directories
##------------------------------------------------------------
def get_img_files (filenames, abs_path=False) :
	img_files = []
	pathed_dirs = []
	for filename in filenames :
		if abs_path :
			filename = os.path.abspath (filename)
		if os.path.isdir (filename) :
			img_files.extend (get_dirs_images ([filename]))
		else :
			img_files.append (filename)
	return img_files

##------------------------------------------------------------
##  get box 
##------------------------------------------------------------
def get_box (image_tag) :
	box_d = defaultdict ()
	for box in image_tag.findall ('box') : # TODO : multiple??
		for part in g_box_attrs :
			box_d[part] = box.attrib.get (part)
	return box_d

##------------------------------------------------------------
##  get shape parts 
##------------------------------------------------------------
def get_shape_parts (image_tag) :
	parts_d = defaultdict ()
	for box in image_tag.findall ('box') : # TODO : multiple??
		parts = box.findall ('part')
	# pdb.set_trace ()
	for part in parts :
		name = part.attrib.get ('name')
		if name in g_shape_parts_find :
			if name == 'head_top' or name == 'htop' :	## tmp fix for erroneous 'head_top'
				name = 'head_top'
			x = part.attrib.get ('x')
			y = part.attrib.get ('y')
			parts_d[name] = {x, y}
	return parts_d

##------------------------------------------------------------
##  diff objs
##------------------------------------------------------------
def obj_equal (obj1, obj2, parts) :
	for part in parts :
		if obj1[part] != obj2[part] :
			return False
	return True
		
##------------------------------------------------------------
##  returns true if box and parts of the two tags match
##------------------------------------------------------------
def diff_image_tags (image1, image2) :
	box_1 = get_box (image1)
	parts_1 = get_shape_parts (image1)
	box_2 = get_box (image2)
	parts_2 = get_shape_parts (image2)
	filename1 = image_tag_file (image1)
	filename2 = image_tag_file (image2)
	# print ('\ncomparing content for : ')
	# print ('\t', filename1)
	# print ('\t', filename2)
	if not obj_equal (box_1, box_2, g_box_attrs) :
		return False
	if not obj_equal (parts_1, parts_2, g_shape_parts) :
		return False
	return True

##------------------------------------------------------------
##  returns name of label.  assumes 1 box, 1 label. does no err checks 
##------------------------------------------------------------
def get_obj_label_text (obj_tag) :
	if obj_tag.tag == 'image' :
		label_tag = obj_tag.find ('box/label')
		# box_tag = obj_tag.find ('box')
		# label_tag = box_tag.find ('label')
	elif obj_tag.tag == 'chip' :
		label_tag = obj_tag.find ('label')
	return label_tag.text

##------------------------------------------------------------
##  returns golden label, parsed from directory path
##------------------------------------------------------------
def get_truth_label (filename) :
	path = os.path.dirname (filename)
	label = os.path.basename (path)
	return label

##------------------------------------------------------------
##------------------------------------------------------------
def get_chip_source (chip_tag) :
	# pdb.set_trace ()
	source_tag = chip_tag.find ('source')
	source_file = source_tag.attrib.get ('file')
	return source_file

##------------------------------------------------------------
##  get_new_face (face,faces_orig_d).  find matching file name
##------------------------------------------------------------
def get_new_face (face, faces_new_d) :
	imagefile_old = face.attrib.get ('file')
	label_old = get_obj_label_text (face)
	pdb.set_trace ()
	for label_new, faces in list(faces_new_d.items ()) :
		if label_old != label_new :
			continue;
		# look for file name
		for face in faces :
			imagefile_new = face.attrib.get ('file')
			if imagefile_new == imagefile_old :
				return face
	return None

##------------------------------------------------------------
##  validate_file - create new file with only valid chip files
##------------------------------------------------------------
def validate_file (xml_file, output_file) :
	chips_d = defaultdict (list)
	filetype = 'chips'
	objfiles = load_objs_from_files ([xml_file], chips_d, filetype)
	valid_chips = []
	print('')
	for key, chips in list(chips_d.items ()) :  ## iterate through all chips
		for chip in chips :
			# pdb.set_trace ()
			chipfile = chip.attrib.get ('file')
			if os.path.exists (chipfile) :
				valid_chips.append (chip)
			else :
				print('\t...unable to find file: ', chipfile)
	print('\n\tGenerated valid chip file: ', output_file)
	print('')
	root, tree = create_new_tree_w_element (filetype)
	for chip in valid_chips :
		tree.append (chip)
	indent (root)
	tree = ET.ElementTree (root)
	tree.write (output_file)

##------------------------------------------------------------
##  find matching image (face,faces_orig_d).
##    returns matched image_tag
##------------------------------------------------------------
def get_matching_image (image_file, images_d) :
	for l , image_tags in list(images_d.items ()) :
		# ignores label, which is only accurate during testing
		# look for file name
		for image_tag in image_tags :
			image_file_2 = image_tag.attrib.get ('file')
			if image_file == image_file_2 :
				return image_tag
	return None

##------------------------------------------------------------
##  return file for image tag
##------------------------------------------------------------
def image_tag_file (image_tag) :
	filename = image_tag.attrib.get ('file')
	return filename

##------------------------------------------------------------
##  remove image_tag from dict
##------------------------------------------------------------
def remove_image_tag (image_file, images_d) :
	for l , image_tags in list(images_d.items ()) :
		# ignores label, which is only accurate during testing
		# look for file name
		for i in range (len (image_tags)) :
			image_file_2 = image_tag_file (image_tags[i])
			if image_file == image_file_2 :
				del image_tags[i]
				return True
	return False

##------------------------------------------------------------
##  diff_face_files .  check for matching images, box, parts
##------------------------------------------------------------
def diff_face_files (xml1, xml2) :
	images1_d = defaultdict(list)
	images2_d = defaultdict(list)
	filetype = "faces"
	print ('\ncomparing files: ', xml1, ' ', xml2)
	objfiles1 = load_objs_from_files ({xml1}, images1_d, filetype)
	objfiles2 = load_objs_from_files ({xml2}, images2_d, filetype)
	newfaces = []
	images_one_only = []
	images_mismatch = []
	images_two_only = []
	for label, images1 in list(images1_d.items ()) :  ## iterate through all images
		for image1 in images1 :
			# pdb.set_trace ()
			image_filename = image_tag_file (image1)
			image2 = get_matching_image (image_filename, images2_d)
			if image2 is None :
				print ("no image match for ", image_filename)
				images_one_only.append (image1)
				continue
			match = diff_image_tags (image1, image2)
			if not match :
				print ("content mismatch for ", image_filename)
				images_mismatch.append (image1)
				remove_image_tag (image_filename, images2_d)
				continue
			# here only if found mathcing box and parts, remove match image2 from list
			remove_image_tag (image_filename, images2_d)
	for label, images2 in list(images2_d.items ()) : ## go through dict and make a list
		for image2 in images2 :
			images_two_only.append (image2)

	write_xml_file ("images_two_only.xml", images_two_only, filetype)
	write_xml_file ("images_one_only.xml", images_one_only, filetype)
	write_xml_file ("images_mismatch.xml", images_mismatch, filetype)
	print ("writing files:")
	print ("\timages_mismatch.xml")
	print ("\timages_one_only.xml")
	print ("\timages_two_only.xml")

##------------------------------------------------------------
##  replicate_file - create file of same list of images with new data
##------------------------------------------------------------
def replicate_file (orig_file, new_files, output_file) :
	faces_orig_d = defaultdict(list)
	faces_new_d = defaultdict(list)
	filetype = "faces"
	objfiles1 = load_objs_from_files (orig_file, faces_orig_d, filetype)
	objfiles2 = load_objs_from_files (new_files, faces_new_d, filetype)
	newfaces = []
	for key, faces in list(faces_orig_d.items ()) :  ## iterate through old list of tests
		for face in faces :
			# pdb.set_trace ()
			newface = get_new_face (face, faces_new_d) ## get new data for same file
			if newface :
				newfaces.append (newface)
			else :
				print('unable to match file:  ', face.attrib.get ('file'))
	root, tree = create_new_tree_w_element (filetype)
	for face in newfaces :
		tree.append (face)
	indent (root)
	tree = ET.ElementTree (root)
	tree.write (output_file)

##------------------------------------------------------------
##  convert a string to floats for each label
##------------------------------------------------------------
def str_to_float (floats_str) :
	float_list = []
	float_strs = floats_str.split ()
	for float_str in float_strs:
		f = float (float_str)
		float_list.append (f)
	return float_list

##------------------------------------------------------------
##  plot embeddings
##------------------------------------------------------------
def write_embed_tsv (input_files) :
	embeds_d = defaultdict(list)
	load_objs_from_files (input_files, embeds_d, 'embeddings')
	label_list = []
	embeds_list = []
	for label, embeds in sorted(embeds_d.items()): ## list of embeds
		for embed in embeds :
			embeds_list.append (embed)
			label_list.append (label)
	embeds_tsv_file = open ("embeds.tsv", "w")
	labels_tsv_file = open ("labels.tsv", "w")
	for i in range(len (embeds_list)):
		embeds_tsv_file.write ('\t'.join (str(x) for x in embeds_list[i]))
		embeds_tsv_file.write ('\n')
		labels_tsv_file.write (label_list[i])
		labels_tsv_file.write ('\n')
	embeds_tsv_file.close ()
	labels_tsv_file.close ()

	print ("generated tsv files: ")
	print ("\tembeds.tsv")
	print ("\tlabels.tsv")

	# print ('\t'.join (str(x) for x in embeds_list[0]))

##------------------------------------------------------------
##  plot embeddings
##------------------------------------------------------------
def plot_embeddings (input_files) :
	embeds_d = defaultdict(list)
	load_objs_from_files (input_files, embeds_d, 'embeddings')
	label_list = []
	embeds_list = []
	for label, embeds in sorted(embeds_d.items()): ## list of embeds
		for embed in embeds :
			embeds_list.append (embed)
			label_list.append (label)
	tsne = TSNE(n_components=2, random_state=0, perplexity=5, learning_rate=10, method='exact', n_iter=2000)
	features = np.array(embeds_list)
	X_2d = tsne.fit_transform(features)
	label_list_set = set (label_list)
	target_names = list (label_list_set)
	target_names.sort ()
	target_ids = range(len(target_names))
	y = np.array (label_list)
	pdb.set_trace ()	

	have_display = "DISPLAY" in os.environ
	if have_display:
		plt.figure()
		ax = plt.subplot (111)
		markers = 'o', 'o', 'o', 'o', 'o', 'o', 'o', 'o', '^', '^', '^', '^', '^', '^', '^', '^'
		colors  = 'r', 'g', 'b', 'c', 'm', 'y', 'k', 'w', 'r', 'g', 'b', 'c', 'm', 'y', 'k', 'w'
		for i, c, label, m in zip(target_ids, colors, target_names, markers):
			# print (i, ' ', c, ' ', label)
			ax.scatter(X_2d[y == label, 0], X_2d[y == label, 1], c=c, label=label, marker=m, s=100)
			# pdb.set_trace ()	
		chartBox = ax.get_position ()
		plt.tight_layout()
		ax.set_position ([chartBox.x0, chartBox.y0, chartBox.width*0.90, chartBox.height])
		ax.legend(bbox_to_anchor=(0.87,1.0),loc='upper left', ncol=1, scatterpoints=1)
		plt.xticks([])
		plt.yticks([])
		plt.savefig('emb.png')
		plt.show()
	else:
		print ('\n\tUnable to plot, no display detected.\n')

	# print ('\t'.join (str(x) for x in embeds_list[0]))


##------------------------------------------------------------------------------
##------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def get_bear_count (res, image_np, min_score, do_display=False) :
	have_display = "DISPLAY" in os.environ
	display = have_display and do_display
	dim = image_np.shape
	width = dim[1]
	height = dim[0]
	bear_cnt = 0
	if display :
		fig,ax = plt.subplots(1)
		# Display the image
		ax.imshow(image_np)
	boxes = res.json()['predictions'][0]['detection_boxes']
	scores = res.json()['predictions'][0]['detection_scores']
	classes = res.json()['predictions'][0]['detection_classes']
	detections = int(res.json()['predictions'][0]['num_detections'])
	for i in range(detections):
		label = coco_classes_d [int (classes[i])]
		if (scores[i] < float (min_score)):
			# print('Scores too low below ', i)
			break
		if label == 'bear' :
			bear_cnt += 1
		else :
			continue
		# print('  Class', label, 'Score', scores[i])
		ymin = int(boxes[i][0] * height)
		xmin = int(boxes[i][1] * width)
		ymax = int(boxes[i][2] * height)
		xmax = int(boxes[i][3] * width)
		b_width = xmax-xmin
		b_height = ymax-ymin
		# print('\t', boxes[i], end='')
		# print(xmin, ymin, b_width, b_height)
		# Create a Rectangle patch
		rect = patches.Rectangle((xmin,ymin),b_width,b_height,linewidth=1,edgecolor='r',facecolor='none')
		# Add the patch to the Axes
		if (display) :
			ax.add_patch(rect)

	if (display) :
		plt.show()
	return bear_cnt

#-------------------------------------------------------------------------------
def do_obj_count (result, image_np, min_score, objs, objs_d) :
	obj_cnt = 0
	boxes = result.json()['predictions'][0]['detection_boxes']
	scores = result.json()['predictions'][0]['detection_scores']
	classes = result.json()['predictions'][0]['detection_classes']
	detections = int(result.json()['predictions'][0]['num_detections'])
	for i in range(detections):
		label = objs_d [int (classes[i])]
		if (scores[i] < float (min_score)):  # scored are ordered
			print('Scores too low below ', i)
			break
		if label in objs :
			obj_cnt += 1
	return obj_cnt

#-------------------------------------------------------------------------------
def get_rect (dim, box, color='r') :
	width = dim[1]
	height = dim[0]
	ymin = int(box[0] * height)
	xmin = int(box[1] * width)
	ymax = int(box[2] * height)
	xmax = int(box[3] * width)
	b_width = xmax-xmin
	b_height = ymax-ymin
	# Create a Rectangle patch
	rect = patches.Rectangle((xmin,ymin),b_width,b_height,linewidth=1,edgecolor=color,facecolor='none')
	return rect

#-------------------------------------------------------------------------------
def get_obj_count (result, image_np, min_score, labels, do_display=False) :
	have_display = "DISPLAY" in os.environ
	display = have_display and do_display
	dim = image_np.shape
	if display :
		fig,ax = plt.subplots(1)
		ax.imshow(image_np)
	boxes = result.json()['predictions'][0]['detection_boxes']
	scores = result.json()['predictions'][0]['detection_scores']
	classes = result.json()['predictions'][0]['detection_classes']
	detections = int(result.json()['predictions'][0]['num_detections'])
	obj_cnt = 0
	for i in range(detections):
		label = object_classes_d [int (classes[i])]
		if (scores[i] < float (min_score)):
			# print('Scores too low below ', i)
			break
		if label in labels :
			obj_cnt += 1
		print('  Class', label, 'Score', scores[i])
		# pdb.set_trace ()
		rect = get_rect (dim, boxes[i], 'r')
		# Add the patch to the Axes
		if (display) :
			ax.add_patch(rect)
	if (display) :
		plt.show()
	return obj_cnt

#-------------------------------------------------------------------------------
def img_find_bears (img_file, min_score, labels) :
	image = Image.open(img_file)
	image_np = np.array(image)
	payload = {"instances": [image_np.tolist()]}
	result = requests.post("http://localhost:8080/v1/models/default:predict", json=payload)
	bear_cnt = get_obj_count (result, image_np, min_score, labels, True)
	return bear_cnt

#-------------------------------------------------------------------------------
def do_find_bears (img_files, out_file, min_score, model) :
	if model == 'tf-frcnn' :
		ids = coco_ids
		classes = coco_classes
		labels = ['bear']
	else : # megadetector
		ids = md_ids
		classes = md_classes
		labels = ['animal']
	for i in range (len (ids)) :
		object_classes_d[ids[i]] = classes[i]
	out_fp0 = open (out_file+'_0', "w")
	out_fp1 = open (out_file+'_1', "w")
	out_fpmulti = open (out_file+'_multi', "w")
	expected_cnt = 1
	for img_file in img_files :
		bear_cnt = img_find_bears (img_file, min_score, labels)
		# pdb.set_trace ()
		# print ('counting bears for ', img_file)
		# if bear_cnt > expected_cnt :
		if bear_cnt == 0 :
			out_fp0.write (str (img_file))
			out_fp0.write ("\n")
		elif bear_cnt == 1 :
			out_fp1.write (str (img_file))
			out_fp1.write ("\n")
		else :
			out_fpmulti.write (str (img_file))
			out_fpmulti.write ("\n")
		print (bear_cnt, 'bears:', img_file)
	print ('\n\tGenerated files: ', out_file, '_{0,1,multi}')
	print ('\n')
	out_fp0.close ()
	out_fp1.close ()
	out_fpmulti.close ()

##------------------------------------------------------------------------------
#-------------------------------------------------------------------------------



##------------------------------------------------------------
##  extract embeddings
##------------------------------------------------------------
def extract_bc_embeddings (input_files) :
	embeds_d = defaultdict(list)
	bc_embeds = []
	bc1_embeds = []
	bf_embeds = []
	xml_files = generate_xml_file_list (input_files)
	print ('\nextracting embeddings from file: ')
	for x_file in xml_files:
		print("\t", x_file)
		# pdb.set_trace()
		root, tree = load_file (x_file)
		# separate out bc & bf bears
		for embedding in root.findall ('./embeddings/embedding'):    
			label = embedding.find ('./label')
			# pdb.set_trace ()
			if label.text[:2] == 'bc' : # bc bear
				if label.text == 'bc_also' or label.text == 'bc_amber' or label.text == 'bc_beatrice' or label.text == 'bc_bella' or label.text == 'bc_flora' or label.text == 'bc_frank' or label.text == 'bc_gc' or label.text == 'bc_hoeya' or label.text == 'bc_kwatse' or label.text == 'bc_lenore' or label.text == 'bc_lillian' or label.text == 'bc_lucky' or label.text == 'bc_river' or label.text == 'bc_steve' or label.text == 'bc_toffee' or label.text == 'bc_topaz' :
					bc1_embeds.append (embedding)
				else :
					bc_embeds.append (embedding)
			else : # brooks bear
				bf_embeds.append (embedding)
	# write out bc bears
	print ('\t... # bc bears: ', len (bc_embeds))
	print ('\t... # bc1 bears: ', len (bc1_embeds))
	print ('\t... # bf bears: ', len (bf_embeds))
	# pdb.set_trace ()
	t_root, t_embeds = create_new_tree_w_element ("embeddings")
	for i in range (len (bc1_embeds)) :
		embed = bc1_embeds[i]
		t_embeds.append (embed)
	tree = ET.ElementTree (t_root)
	t_name = "bc1_embeds.xml"
	indent (t_root)
	tree.write (t_name)
	print ('wrote bc embeddings to ', t_name)

##------------------------------------------------------------
##  split bc bf objects
##------------------------------------------------------------
def split_objects_by_locales (input_files, obj_path='images/image', label_path='box/label') :
	bc_objs = []
	bf_objs = []
	unknown_objs = []
	xml_files = generate_xml_file_list (input_files)
	print ('\nextracting faces from file: ')
	for x_file in xml_files:
		print("\t", x_file)
		# pdb.set_trace()
		root, tree = load_file (x_file)
		# separate out bc & bf bears
		for obj in root.findall (obj_path):
			label = obj.find (label_path)
			# pdb.set_trace ()
			if label.text[:2] == 'bc' : # bc bear
				bc_objs.append (obj)
			elif label.text[:2] == 'bf' : # brooks bear
				bf_objs.append (obj)
			else :
				unknown_objs.append (obj)
	# write out bc bears
	print ('\t... # bc bears: ', len (bc_objs))
	print ('\t... # bf bears: ', len (bf_objs))
	print ('\t... # unknown bears: ', len (unknown_objs))
	# pdb.set_trace ()
	# for locale in [] :
	t_root, t_embeds = create_new_tree_w_element ("images")
	for i in range (len (bc_objs)) :
		embed = bc_objs[i]
		t_embeds.append (embed)
	tree = ET.ElementTree (t_root)
	t_name = "bc1_faces.xml"
	indent (t_root)
	tree.write (t_name)
	print ('wrote faces to ', t_name)

	t_root, t_embeds = create_new_tree_w_element ("images")
	for i in range (len (bc_objs)) :
		embed = bc_objs[i]
		t_embeds.append (embed)
	tree = ET.ElementTree (t_root)
	t_name = "bc_faces.xml"
	indent (t_root)
	tree.write (t_name)
	print ('wrote faces to ', t_name)

	t_root, t_embeds = create_new_tree_w_element ("images")
	for i in range (len (bf_embeds)) :
		embed = bf_embeds[i]
		t_embeds.append (embed)
	tree = ET.ElementTree (t_root)
	t_name = "bf_faces.xml"
	indent (t_root)
	tree.write (t_name)
	print ('wrote faces to ', t_name)


##------------------------------------------------------------
##   main code
##------------------------------------------------------------
def do_generate_folds (input_files, n_folds, output_file, shuffle=True) :
	chips_d = defaultdict(list)
	load_objs_from_files (input_files, chips_d)
	## print "printing chips dictionary ... "
	## print_dict (chips_d)
	train_list, validate_list = generate_folds_content (chips_d, n_folds, shuffle)
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
