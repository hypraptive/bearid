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
from collections import OrderedDict
from collections import Counter
from os import walk
import numpy as np
import scipy
from scipy.spatial import distance
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas
from mpl_toolkits.mplot3d import Axes3D
from sklearn.manifold import TSNE
from PIL import Image
from pathlib import Path

g_e_label_idx = 0
g_e_file_idx = 1
g_e_vals_idx = 2
g_e_img_idx = 3
g_e_chip_idx = 4
g_vchipnames_d = defaultdict ()
g_x = 0
g_y = 1
g_labels = []
g_unused = 2
g_small_img = 3
g_verbosity = 0
g_filetype = ''
g_stats_zero = []
g_stats_many = []
g_objs_zero = []
g_objs_many = []
g_multi_ok = False
g_multi_ok = True
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
	'bc_cleo', 'bc_clyde', 'bc_coco', 'bc_cooper', 'bc_cross-paw', 'bc_dani-bear', 
	'bc_das-auto', 'bc_diablo', 'bc_fisher', 'bc_flora', 'bc_frank', 'bc_freckles', 'bc_freda', 
	'bc_freya', 'bc_gary', 'bc_gc', 'bc_glory', 'bc_hero', 'bc_hoeya', 'bc_jaque', 
	'bc_kiokh', 'bc_kwatse', 'bc_lenore', 'bc_lil-willy', 'bc_lillian', 
	'bc_lucky', 'bc_matsui', 'bc_millerd', 'bc_mouse', 'bc_mouse_lookalike', 'bc_neana', 'bc_no-tail', 
	'bc_old-girl', 'bc_oso', 'bc_peanut', 'bc_pete', 'bc_pirate', 
	'bc_pretty-boy', 'bc_river', 'bc_sallie', 'bc_santa', 'bc_shaniqua', 
	'bc_simoom', 'bc_stella', 'bc_steve', 'bc_teddy-blonde', 'bc_teddy-brown', 
	'bc_thimble', 'bc_thumper', 'bc_toffee', 'bc_topaz', 'bc_trouble', 'bc_tuna', 'bc_ursa', 
	'kb_bc_m034'
	]
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
##  create user readable string from list of filetypes
##------------------------------------------------------------
def filetypes_to_str (filetypes) :
	filetypes_str = '<'+filetypes[0]
	for filetype in filetypes[1:-1] :
		filetypes_str += '|'+filetype
	filetypes_str += '|'+filetypes[-1]+'>'
	return filetypes_str

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
##  set global multi faces per image state
##------------------------------------------------------------
def set_multi_ok  (state) :
	global g_multi_ok
	g_multi_ok = state

##------------------------------------------------------------
##  set global multi faces per image state
##------------------------------------------------------------
def get_multi_ok  () :
	return g_multi_ok

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
##  append to g_stats_zero
##------------------------------------------------------------
def g_stats_zero_append (filename) :
	global g_stats_zero
	g_stats_zero.append (filename)

##------------------------------------------------------------
##  append to g_objs_zero
##------------------------------------------------------------
def g_objs_zero_append (filename) :
	global g_objs_zero
	g_objs_zero.append (filename)

##------------------------------------------------------------
##  append to  g_stats_many
##------------------------------------------------------------
def g_stats_many_append (filename) :
	global g_stats_many
	g_stats_many.append (filename)

##------------------------------------------------------------
##  append to  g_objs_many
##------------------------------------------------------------
def g_objs_many_append (obj) :
	global g_objs_many
	g_objs_many.append (obj)

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
##  load xml into hier dictionary of 
##  defaultdict (lambda:defaultdict(lambda: defaultdict(lambda: defaultdict(list))))
##  ex:  d["b-032"] = ["<Element 'chip' at 0x123,..,<Element 'chip' at 0x43]
##       d["b-747"] = ["<Element 'chip' at 0x987,..,<Element 'chip' at 0x65]
##  returns ??  list of filenames.  if filename_type == 'source', return 
##     chip source filenames
##  expect d_objs to be	: defaultdict (lambda:defaultdict(lambda: defaultdict(lambda: defaultdict(list))))
##------------------------------------------------------------
def hier_load_objs (root, d_objs, filetype, filename_type='file') :
	## print "loading chips"

	obj_filenames = []
	if filetype == 'chips' :
		for chip in root.findall ('./chips/chip'):
			label_list = chip.findall ('label')
			filename = chip.attrib.get ('file')
			if len (label_list) < 1 :
				g_stats_zero_append (filename)
				print("no labels: ", label_list)
				continue
			if len (label_list) > 1 :
				g_stats_many_append (filename)
				print("too many labels: ", label_list)
				continue
			label = label_list[0].text
			if filename_type == 'source' :
				source_filename = get_chip_source_file (chip)
				obj_filenames.append (source_filename)
			else :
				obj_filenames.append (filename)
			datetime_str = tag_get_datetime_str (chip, filetype)
			hier_add_obj (d_objs, chip, label, datetime_str)
			#d_objs[label].append(chip)
	# pdb.set_trace ()
	return obj_filenames
	
##------------------------------------------------------------
##  add label to global list if new
##------------------------------------------------------------
def g_add_label (label) :
	if label not in g_labels :
		g_labels.append (label)
	
##------------------------------------------------------------
##  return global list of uniq labels
##------------------------------------------------------------
def g_get_labels () :
	return g_labels
	
##------------------------------------------------------------
##  - load xml into dictionary of <string><element>
##  ex:  d["IMG_124.MP4"] = <Element 'chip' at 0x123>
##------------------------------------------------------------


##------------------------------------------------------------
##  load xml into dictionary of <string><element_list>
##  ex:  d["b-032"] = ["<Element 'chip' at 0x123,..,<Element 'chip' at 0x43]
##  - add labels to global list
##  - returns 4 lists: chips_filenames, video_filesnames, locations, datetimes
##------------------------------------------------------------
def load_video_chip_objs (root, vchips_d) : # , parent_path) :
	chip_filenames = []
	video_filenames = []
	locations = []
	datetimes = []
	labels = []
	for chip in root.findall ('./chips/chip'):
		chip_filename = chip.attrib.get ('file')
		label = obj_get_label_text (chip)
		g_add_label (label)
		video_filename = get_chip_source_file (chip, 'video_chips')
		# filename = filename.replace (parent_path, '')
		# video_filename = video_filename.replace (parent_path, '')
		# pdb.set_trace ()
		location = video_chip_get_location (chip_filename)
		dateTime = tag_get_datetime_str (chip, 'video_chips')
		video_filenames.append (video_filename)
		chip_filenames.append (chip_filename)
		locations.append (location)
		datetimes.append (dateTime)
		labels.append (label)
		vchips_d[label].append(chip)
		g_vchipnames_d[chip_filename] = chip
	return chip_filenames, video_filenames, locations, datetimes, labels

##------------------------------------------------------------
##  given path of chip, return name of location
##------------------------------------------------------------
def video_chip_get_location (chip_filename) :
	dirs = chip_filename.split('/')
	return dirs[-4]

##------------------------------------------------------------
##  load xml into dictionary of <string><element_list>
##  ex:  d["b-032"] = ["<Element 'chip' at 0x123,..,<Element 'chip' at 0x43]
##       d["b-747"] = ["<Element 'chip' at 0x987,..,<Element 'chip' at 0x65]
##  returns list of filenames.  if filename_type == 'source', return 
##     chip source filenames
##------------------------------------------------------------
def load_objs (root, d_objs, filetype, filename_type='file') :
	## print "loading chips"

	obj_filenames = []
	if filetype in ['chips', 'video_chips'] :
		for chip in root.findall ('./chips/chip'):
			label_list = chip.findall ('label')
			filename = chip.attrib.get ('file')
			if len (label_list) < 1 :
				g_stats_zero_append (filename)
				print("no labels: ", label_list)
				continue
			if len (label_list) > 1 :
				g_stats_many_append (filename)
				print("too many labels: ", label_list)
				continue
			label = label_list[0].text
			if filename_type == 'source' :
				source_filename = get_chip_source_file (chip)
				obj_filenames.append (source_filename)
			else :
				obj_filenames.append (filename)
			d_objs[label].append(chip)
			g_add_label (label)
	elif filetype == 'images' :
		# pdb.set_trace ()
		label = ''
		for image in root.findall ('./images/image'):
			facefile = image.attrib.get ('file')
			obj_filenames.append (facefile)
			d_objs[label].append(image)
	elif filetype == 'faces' :
		# pdb.set_trace ()
		multi_faces = defaultdict(lambda:0)
		for image in root.findall ('./images/image'):
			box = image.findall ('box')
			facefile = image.attrib.get ('file')
			multi_faces[len(box)] += 1
			if len (box) == 0 :
				g_stats_zero_append (facefile)
				g_objs_zero_append (image)
				continue
			if len (box) > 1 :
				g_stats_many_append (facefile)
				g_objs_many_append (image)
				print ("Warning:", len (box), "boxes (faces) in file ", facefile)
				if g_multi_ok is False :
					continue
			label_list = box[0].findall ('label')
			if len (label_list) == 0:
				pdb.set_trace ()
				print ('Warning: file', facefile, 'is missing image label')
				continue
			label = label_list[0].text
			obj_filenames.append (facefile)
			d_objs[label].append(image)
			g_add_label (label)
		if get_verbosity () > 1 :
			print ('\nface count:')
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
				print('Error: expecting only 2 chips in pair, got: ', labels)
				continue
			if labels[0].text != labels[1].text :
				print('error: labels should match: ', labels)
			matched_cnt += 1
			d_objs[matched].append(labels[0])
		obj_filenames.append (d_objs[matched])
		for pair in root.findall ('./pairs/pair_unmatched'):
			labels = pair.findall ('./chip/label')
			if len (labels) != 2 :
				print('Error: expecting only 2 chips in pair, got: ', labels)
				continue
			if labels[0].text == labels[1].text :
				print('Error: labels should not match: ', labels)
			unmatched_cnt += 1
			d_objs[unmatched].append(labels)
		obj_filenames.append (d_objs[unmatched])
	elif filetype == 'embeddings' :
		for embedding in root.findall ('./embeddings/embedding'):    
			label = embedding.find ('./label')
			# pdb.set_trace ()
			embed_val = embedding.find ('./embed_val')
			vals_str = embed_val.text.split ()
			embed_floats = [float (i) for i in vals_str]
			d_objs[label.text].append(embed_floats)
			g_add_label (label.text)
	elif  filetype == 'embeds' :
		for embedding in root.findall ('./embeddings/embedding'):    
			label = embedding.find ('./label')
			# pdb.set_trace ()
			d_objs[label.text].append(embedding)
			g_add_label (label.text)
	else :
		print('Error: unknown filetype: ', filetype, '  Expected one of "faces", "chips", "embeddings", "embeds" or "pairs".')
	# pdb.set_trace ()
	return obj_filenames

##------------------------------------------------------------
## print closest n labels from dict
##  x = sorted(d.items(), key=lambda x: x[1])
##  for dict of distances, return closest n labels
##------------------------------------------------------------
def print_nearest (e_dist_d, n) :
	sorted_e = sorted(e_dist_d.items(), key=lambda x: x[1])
	nearests = []
	for i in range (n) : 
		label = sorted_e[i][0]
		nearests.append (label)
		print (i, ': ', label, ' : distance : ', sorted_e[i][1])
	return nearests
		
##------------------------------------------------------------
## given an embedding and a list of embeddings
##  e.g. [x,y], [[a1,b1], [a2,b2], [a3,b3]]
##  return list of distances
##  e.g. [.4312, .9136, .29462]
##------------------------------------------------------------
def get_embed_distances_e_elist (embed, embeds) :
	e_array = np.array (embed)
	e_distances = []
	# pdb.set_trace ()
	for e in embeds:
		e1_array = np.array (e)
		dist = distance.euclidean (e_array, e1_array)
		e_distances.append (dist)
	return e_distances
		
##------------------------------------------------------------
## given probe embedding and list gallery embeddings
##  e.g. [x,y], [['bc_amber/a.jpg',[a1,b1]],['bf_032/bcd.jpg',[a2,b2],
##               ['bc_amber/b.jpg',[a3,b3]]
##  return list of each distance between embedding and those in list
##  e.g. ["bella": .4312, "otis": .9136, "amber": .29462]
##------------------------------------------------------------
def get_embed_distances (embed, embed_list) :
	return 42
		
##------------------------------------------------------------
## given an embedding and dict of label averages 
##  e.g. [x,y], ["bella":[a1,b1], "otis":[a2,b2], "amber":[a3,b3]]
##  return dict of each distance between embedding and averages
##  e.g. ["bella": .4312, "otis": .9136, "amber": .29462]
##------------------------------------------------------------
def get_embed_distances (embeds_d, new_embed) :
	e_dist_d = OrderedDict ()
	new_e_array = np.array (new_embed)
	for label, embed in list(embeds_d.items()):
		e_array = np.array (embed)
		e_dist_d [label] = distance.euclidean (e_array, new_e_array)
	pdb.set_trace ()
	return e_dist_d

##------------------------------------------------------------
##  returns dict of embedding average (cluster center)
##------------------------------------------------------------
def get_embed_averages (embeds_d) :
	e_averages_d = defaultdict ()
	for label, embeds in list(embeds_d.items()):
		pdb.set_trace ()
		e_array = np.array (embeds)
		e_mean = np.mean (e_array, axis=0, dtype=np.float64)
		e_averages_d [label] = e_mean.tolist ()
		pdb.set_trace ()
	pdb.set_trace ()
	return e_averages_d

##------------------------------------------------------------
##  given embedding dict, print average, and distances
##    from average
##------------------------------------------------------------
def print_e_stats (embeds_d) :
	e_averages_d = create_embed_label_averages (embeds_d)
	for label, embed_average in sorted(e_averages_d.items()): ##
		embeds = embeds_d[label]
		e_distances = get_embed_distances (embeds, embed_average)
		e_dist_fr_mean = []
		# for e in embeds
		print ('do something')
	sorted_e = sorted(e_dist_d.items(), key=lambda x: x[1])
	# for label, dist :
		# print (dist)
	# print all to csv and stdout

##------------------------------------------------------------
##  write 2 rows: 
##     value of average embed of each label 
##     name of each label
##------------------------------------------------------------
def	write_embed_averages_hdr (av_train_e_d, av_fp) :
	# write av embed for each label.  
	# av_fp.write (';')
	# for label, embeds in av_train_e_d:
		# av_fp.write (';' + embed[0])
	# av_fp.write ('\n')
	av_fp.write (';')
	for label, embeds in av_train_e_d:
		av_fp.write (';' + label)
	av_fp.write ('\n')

##------------------------------------------------------------
##  write distance to label average
##------------------------------------------------------------
def write_dist_to_averages (e_distances, av_fp):
	av_fp.write (';')
	for e_dist in e_distances:
		av_fp.write (';' + str (e_dist))

##------------------------------------------------------------
##  write n sets of label and dist
##------------------------------------------------------------
def write_n_closest (e_distances, n, av_fp) :
	av_fp.write (';')
	for e_dist in e_distances:
		av_fp.write (';' + str (e_dist))
		# write label
		av_fp.write (';' + str (e_dist))

##------------------------------------------------------------
##  find nearests labels
##  given embedding, enbed_dict, write n nearest labels
##------------------------------------------------------------
def get_closest_averages (train_e_d, test_e_d, n) :
	av_dist_file = 'av_distance_' + current_datetime () + '.csv'
	av_fp = open (av_dist_file, "w")

	e_val_probe_list = get_embed_vals_from_list (e_probe_list)
	e_val_gallery_list = get_embed_vals_from_list (e_gallery_list)



	av_train_e_d = get_embed_averages (train_e_d)
	write_embed_averages_hdr (av_train_e_d, av_fp)
	for label, embeds in test_e_d :
		for t_embed in embeds :
			e_distances = get_embed_distances (av_train_e_d, t_embed)
			write_dist_to_averages (e_distances, av_fp)
			e_distances_sorted = e_distances.sorted (e_distances, key = lambda x: x[1])
			pdb.set_trace ()
			write_n_closest (e_distances_sorted, n, av_fp)
	print_closest (e_dist_d, n)
	av_fp.close ()


##------------------------------------------------------------
##  find nearests embeddings
##------------------------------------------------------------
def get_closest_embeddings (embeds, e, n) :
	e_distances = get_embed_distances (embeds, e)
	e_distances_sorted = e_distances.sorted (e_distances, key = lambda x: x[1])
	for i in range (n) :
		print (e_distances_sorted [i])
	# print_closest (e_dist_d, n)

##------------------------------------------------------------
##  generate distance matrix
##------------------------------------------------------------
def gen_embed_distance_matrix (embeds, e) :
	e_dist_d = get_embed_distances (embeds, e)
	for i in range (n) :
		print_closest (e_dist_d, n)

##------------------------------------------------------------
##  flatten embed_d.  change dict to list of tuples (label, val)
##------------------------------------------------------------
def flatten_embedsdict (embeds_d) :
	e_list = []
	for label, embeds in embeds_d :
		for embed in embeds :
			filename = obj_get_filename (embed)
			e = [label, filename, key, val]
			e_list.append (e)
	return e_list

##------------------------------------------------------------
## 	embedding = [label, embed_file, embed_floats, , img_file, chip_file]
##------------------------------------------------------------
def einfo_get_label (embed_info) :
	return embed_info[g_e_label_idx]

##------------------------------------------------------------
## 	embedding = [label, embed_file, embed_floats, , img_file, chip_file]
#  return filename of embedding e.g. img5_chip_0.dat
##------------------------------------------------------------
def einfo_get_file (embed_info) :
	return embed_info[g_e_file_idx]

##------------------------------------------------------------
## 	embedding = [label, embed_file, embed_floats, , img_file, chip_file]
#   returns list of values
##------------------------------------------------------------
def einfo_get_vals (embed_info) :
	return embed_info[g_e_vals_idx]

##------------------------------------------------------------
## 	embedding = [label, embed_file, embed_floats, , img_file, chip_file]
##  return original image e.g. img5.jpg
##------------------------------------------------------------
def einfo_get_img (embed_info) :
	return embed_info[g_e_img_idx]

##------------------------------------------------------------
## 	embedding = [label, embed_file, embed_floats, , img_file, chip_file]
##  returns name of chip file, e.g. img5_chip_0.jpg
##------------------------------------------------------------
def einfo_get_chip (embed_info) :
	return embed_info[g_e_chip_idx]

##------------------------------------------------------------
##  get list of embedding values from embeds list
##   given: [[label, filename, embedding, img_filename], ... ]
##------------------------------------------------------------
def get_embed_vals_from_list (e_list) :
	e_vals_list = []
	for i in range (len (e_list)) :
		einfo = e_list[i]
		e_vals_list.append (einfo_get_vals (einfo))
	return e_vals_list
		
##------------------------------------------------------------
##  get list of image filenames from embeds list
##   given: [[label, filename, embedding, img_filename], ... ]
##------------------------------------------------------------
def	get_imgs_from_list (e_list):
	e_imgs_list = []
	for i in range (len (e_list)) :
		einfo = e_list[i]
		e_imgs_list.append (einfo_get_img (einfo))
	return e_vals_list

##------------------------------------------------------------
##  return subpath n dirs above file
##------------------------------------------------------------
def subpath (filename, n) :
	fnames = os.path.split (filename)
	img_name = fnames[1]
	path = fnames[0]
	if not path :
		return filename
	for i in range (n) :
		fnames = os.path.split (path)
		base = fnames[1]
		path = fnames[0]
		img_name = base + '/' + img_name
		if not path :
			return img_name
	return img_name
		
##------------------------------------------------------------
##  get AVERAGE embeddings from objs - given dict of embedding tags,
##   return dictionay
##   of [label, emtpy_embed_file, av_embed_floats, empty_img_file, empty_chip_file]
##------------------------------------------------------------
def get_av_embedding_dict_from_objs (embeds_d) :
	embedding_d = defaultdict (list)
	for label, embeds in list (embeds_d.items ()) :
		embed_array = []
		for embed_tag in embeds :
			embed_val = embed_tag.find ('./embed_val')
			# pdb.set_trace ()
			vals_str = embed_val.text.split ()
			embed_floats = [float (i) for i in vals_str]
			embed_array.append (embed_floats)
		# do average here
		e_array = np.array (embed_array)
		e_mean = np.mean (e_array, axis=0, dtype=np.float64)
		e_average = e_mean.tolist ()
		embed_file = ''
		img_file = ''
		chip_file = ''
		embedding = [label, embed_file, e_average, img_file, chip_file]
		embedding_d[label].append (embedding)
	return embedding_d

##------------------------------------------------------------
##  return list of AVERAGE embeddings from vals- given dict of 
##   average embeddings, orig embed dict,  and probe_inof. 
##   get new average w/o probe value as: ((av * n) - probe)/(n-1)
##   return flattened list
##   of [label, emtpy_embed_file, av_embed_floats, empty_img_file, empty_chip_file]
##------------------------------------------------------------
def get_mod_av_embedding_list_from_vals (e_val_d, embeds_d, probe_einfo) :
	embedding_list = []
	# extract probe_einfo 
	probe_label = ''
	probe_label = einfo_get_label (probe_einfo)
	probe_vals = einfo_get_vals (probe_einfo)
	probe_vals_ar = np.array (probe_vals)
	# pdb.set_trace ()
	# neg_probe_vals_ar = 0-probe_vals_ar
	for label, e_vals in list (e_val_d.items ()) :
		if label != probe_label : 
			embedding_list.append (e_vals[0])
			continue
		# rm probe val from average
		vals = einfo_get_vals (e_vals[0])
		cnt = len (embeds_d[label])
		if cnt == 1 :
			break
		# pdb.set_trace ()
		e_sum_array = np.array (vals) * cnt
		e_sumnoprobe_array = e_sum_array - probe_vals_ar
		e_mean_array = e_sumnoprobe_array / (cnt-1)
		e_average = e_mean_array.tolist ()
		embed_file = ''
		img_file = ''
		chip_file = ''
		embedding = [label, embed_file, e_average, img_file, chip_file]
		embedding_list.append (embedding)
	return embedding_list

##------------------------------------------------------------
##  get AVERAGE embeddings from objs - given dict of embedding tags,
##   create flattened list
##   of [label, emtpy_embed_file, av_embed_floats, empty_img_file, empty_chip_file]
##------------------------------------------------------------
def get_av_embedding_list_from_objs (embeds_d, probe_einfo='') :
	embedding_list = []
	# extract probe_einfo 
	probe_label = ''
	if probe_einfo :
		probe_label = einfo_get_label (probe_einfo)
		probe_vals = einfo_get_vals (probe_einfo)
		probe_vals_ar = np.array (probe_vals)
		# pdb.set_trace ()
		neg_probe_vals_ar = 0-probe_vals_ar
	for label, embeds in list (embeds_d.items ()) :
		embed_array = []
		for embed_tag in embeds :
			embed_val = embed_tag.find ('./embed_val')
			# pdb.set_trace ()
			vals_str = embed_val.text.split ()
			embed_floats = [float (i) for i in vals_str]
			embed_array.append (embed_floats)
		# do average here
		e_array = np.array (embed_array)
		if label == probe_label : 
			np.append (e_array, neg_probe_vals_ar)
		e_mean = np.mean (e_array, axis=0, dtype=np.float64)
		e_average = e_mean.tolist ()
		embed_file = ''
		img_file = ''
		chip_file = ''
		embedding = [label, embed_file, e_average, img_file, chip_file]
		embedding_list.append (embedding)
	return embedding_list

##------------------------------------------------------------
##  get_embeddings from obj - given dict of embedding tags,
##   embed values and filename to create flattened list
##   of [label, embed_file, embed_floats, img_file, chip_file]
##------------------------------------------------------------
def get_embedding_list_from_objs (embeds_d) :
	embedding_list = []
	for label, embeds in list (embeds_d.items ()) :
		for embed_tag in embeds :
			embed_val = embed_tag.find ('./embed_val')
			embed_filename = embed_tag.attrib.get ('file')
			# pdb.set_trace ()
			embed_file = subpath (embed_filename, 2)
			vals_str = embed_val.text.split ()
			embed_floats = [float (i) for i in vals_str]
			img_file = get_embed_chip_source_file (embed_tag)
			chip_file = get_embed_chip_file (embed_tag)
			embedding = [label, embed_file, embed_floats, img_file, chip_file]
			embedding_list.append (embedding)
	return embedding_list

##------------------------------------------------------------
##  get_embeddings from obj - given dict of embedding tags,
##   embed values and filename to create flattened list
##   of [label, embed_file, embed_floats, img_file, chip_file]
##------------------------------------------------------------
def get_embedding_dict_from_objs (embeds_d) :
	einfo_d = default_dict (list)
	for label, embeds in list (embeds_d.items ()) :
		for embed_tag in embeds :
			embed_val = embed_tag.find ('./embed_val')
			embed_filename = embed_tag.attrib.get ('file')
			# pdb.set_trace ()
			embed_file = subpath (embed_filename, 2)
			vals_str = embed_val.text.split ()
			embed_floats = [float (i) for i in vals_str]
			img_file = get_embed_chip_source_file (embed_tag)
			chip_file = get_embed_chip_file (embed_tag)
			embedding = [label, embed_file, embed_floats, img_file, chip_file]
			einfo_d[labe].append (embedding)
	return einfo_d

##------------------------------------------------------------
##------------------------------------------------------------
def get_embed_chip_source_file (embed_tag) :
	chip_tag = embed_tag.find ('./chip')
	img_filename = get_chip_source_file (chip_tag)
	return img_filename

##------------------------------------------------------------
##------------------------------------------------------------
def get_embed_chip_file (embed_tag) :
	chip_tag = embed_tag.find ('./chip')
	img_filename = obj_get_filename (chip_tag)
	return img_filename

##------------------------------------------------------------
##  from embed info, return embed dist info [embedding, image_date]]
##------------------------------------------------------------
def get_einfo_image_date (einfo, db_df) :
	einfo_imgname = einfo_get_img  (einfo)
	einfo_datetime = get_file_datetime ([einfo_imgname], db_df)
	einfo_date = einfo_datetime [0]
	return einfo_date


##------------------------------------------------------------
##  write stats tested collective labels to file
##  label; # train; # test; # right; label matched/#/label_train#; label matched/#/label_train#;
##------------------------------------------------------------
def edist_write_label_matches_stats (gallery_d, probe_d, matched_label_d, stats_filename) :
	fp_matchstats = open (stats_filename, "w")
	fp_matchstats.write ('label; # train; # test; # correct ; matched1/#/#train; matched2/#/#train; ... \n')
	write_top_match_cnt = 3
	for label, all_matched_labels in list (matched_label_d.items()) :
		# pdb.set_trace ()
		top_common = Counter(all_matched_labels).most_common()
		counter_str = ''
		# creating str for count of labels
		# pdb.set_trace ()
		top_match_str = ''
		max_match = min (write_top_match_cnt, len (top_common))
		extra_str = ''
		true_pos = 0
		for i in range (len (top_common)) :
			match_label = top_common[i][0] 
			match_count = top_common[i][1] 
			if match_label == label :
				true_pos = match_count
			top_match_str += ';' + match_label + '/' + str (match_count) + '/' + str (len (gallery_d[match_label]))
		label_stat = label + ';' + str (len (gallery_d[label])) + ';' + str (len (probe_d[label])) + ';' + str (true_pos) + top_match_str + '\n'
		fp_matchstats.write (label_stat)
	fp_matchstats.close ()

##------------------------------------------------------------
##  write stats top matches of each test to file
##  label; # train; # test; # right; label matched/#; label matched/#;
##------------------------------------------------------------
def edist_write_top_matches_stats (gallery_d, matched_results, stats_filename) :
	fp_matchstats = open (stats_filename, "w")
	fp_matchstats.write ('label; # train; matched ; label matched/#; label matched/#\n')
	write_top_match_cnt = 3
	for results_pair in matched_results :
		# pdb.set_trace ()
		label = results_pair[0]
		matched_label = results_pair[1]
		all_matched_labels = results_pair[2]
		top_common = Counter(all_matched_labels).most_common()
		counter_str = ''
		# creating str for count of labels
		# pdb.set_trace ()
		if matched_label == label :
			matched = '1'
		else :
			matched = '0'
		top_match_str = ''
		max_match = min (write_top_match_cnt, len (top_common))
		for i in range (max_match) :
			match_label = top_common[i][0] 
			match_count = top_common[i][1] 
			top_match_str += ';' + match_label + '/' + str (match_count) + '/' + str (len (gallery_d[match_label]))
		label_stat = label + ';' + str (len (gallery_d[label])) + ';' + matched + top_match_str + '\n'
		fp_matchstats.write (label_stat)
	fp_matchstats.close ()

##------------------------------------------------------------
##  output csv of distances to each train embeddings
##   given dist of test embeddings, dict of train embeddings
##   and filename, write out matrix all train distances from
##   each test embedding
##------------------------------------------------------------
def write_csv_embed_distances (probe_d, gallery_d, csv_file, db, match_n, files_eq, write_stats) :
	e_probe_list = get_embedding_list_from_objs (probe_d)
	if files_eq :
		print ('... probe == gallery\n ')
	if match_n == 0 :   # comparing against average for each label
		e_gallery_list = get_av_embedding_list_from_objs (gallery_d)
		e_val_gallery_list = get_embed_vals_from_list (e_gallery_list)
		if files_eq:  # doing average & vs self so get average values
			e_av_dict = get_av_embedding_dict_from_objs (gallery_d)
	else : # each embedding
		e_gallery_list = get_embedding_list_from_objs (gallery_d)
		e_val_gallery_list = get_embed_vals_from_list (e_gallery_list)
	# pdb.set_trace ()
	fp = open (csv_file, "w")
	closest_file = 'closests_' + csv_file
	filename_datetime = current_datetime () 
	matchinfo_file = 'matchinfo_' + filename_datetime + '.csv'
	fp_closest = open (closest_file, "w")
	fp_matchinfo = open (matchinfo_file, "w")
	matched_label_d = defaultdict (list)
	print ('\n... writing nearest matches to', closest_file)
	# fp_closest.write ('test; idx closest label; closest label; distance; match; test img date; test img time; matched img date; matched img time: same match \n')
	fp_closest.write ('probe; idx closest label; closest label; distance; match\n')
	# write header
	if files_eq :
		for label, objs in list(gallery_d.items()):
			fp.write (';' + label)
	else :
		for i in range (len (e_gallery_list)) :
			fp.write (';' + einfo_get_label (e_gallery_list[i]))
	# fp.write (';' matched)
	fp.write ('\n')
	# write distances
	matched_results = []
	match_count = 0
	db_df = None
	if db is not None:
		db_df = pandas.read_csv (db, sep=';')
	single_cnt = 0
	for i in range (len (e_probe_list)) :
		# write label
		probe_info = e_probe_list[i]
		probe_label = einfo_get_label (probe_info)
		# print (i, ': handling probe label', probe_label)
		probe_embedding = einfo_get_vals (probe_info)
		probe_distinfo = [probe_embedding]
		if db is not None: # get embedding's image's date if has db info
			probe_date = get_einfo_image_date (einfo, db_df)
			probe_distinfo.append (probe_date)
		fp.write (probe_label)

		# if comparing vs (average & self), then change average to 
		# remove self from average
		if files_eq and match_n == 0 :
			if len (gallery_d[probe_label]) == 1 :
				single_cnt += 1
				print ('... ignoring count of 1 for label:', probe_label)
				continue
			e_gallery_list = get_mod_av_embedding_list_from_vals (e_av_dict, gallery_d, probe_info)
			# pdb.set_trace ()
			e_val_gallery_list = get_embed_vals_from_list (e_gallery_list)
		min_indices, min_distances = write_dist_csv (probe_distinfo, e_val_gallery_list, fp, match_n)
		# pdb.set_trace ()
		matched_label, all_matched_labels = write_closests_info (e_gallery_list, fp_closest, min_indices, min_distances, probe_info, db_df, fp_matchinfo)
		matched_label_d[probe_label].append (matched_label)
		if matched_label == probe_label :
			match_count += 1
		matched_results.append ([probe_label, matched_label, all_matched_labels])
	if write_stats :
		match_topstats_file = 'matchTopStats_' + current_datetime () + '.csv'
		match_labelstats_file = 'matchLabelStats_' + current_datetime () + '.csv'
		##  TODO NOW
		edist_write_top_matches_stats (gallery_d, matched_results, match_topstats_file)
		edist_write_label_matches_stats (gallery_d, probe_d, matched_label_d, match_labelstats_file)
	fp.close ()
	fp_closest.close ()
	fp_matchinfo.close ()
	if db is None :
		print ('\n... generated', closest_file)
	else :
		print ('\n... generated', closest_file, 'and', matchinfo_file)
	if write_stats :
		print ('\n... generated', match_topstats_file)
		print ('\n... generated', match_labelstats_file)
	print ('\n\ttest labels   :', str (len (e_probe_list)))
	print ('\tmatched labels:', str (match_count))
	if files_eq :
		print ('\tsingle instances:', str (single_cnt))
	print ('\taccuracy      :', str (match_count / (len (e_probe_list)-single_cnt)))
	print ('\n')


##------------------------------------------------------------
##  write closest neighbors to file.  if match and has file info db,
##    write data to file for viewing and checking for data bias (leak)
##  format: label;distance; date1;time1,date2; time2; 
##			image1, image2, chip1, chip2
## 
##  probe_info & e_gallery_list content:
##       [label, embed_file, embed_floats, img_file, chip_file]
##	  returned from get_embedding_list_from_objs
##------------------------------------------------------------
def write_closests (e_gallery_list, fp, min_indices, 
		min_distances, probe_info, db_df, fp_matchinfo) :
	# pdb.set_trace ()
	label_idx = 0
	img_idx = 3
	chip_idx = 4
	match = 0
	probe_label = probe_info[label_idx]
	probe_image = probe_info[img_idx]
	probe_chip = probe_info[chip_idx]
	if db_df is not None :
		probe_datetime = get_file_datetime ([probe_image], db_df)
		probe_date = probe_datetime [0]
		probe_time = probe_datetime [1]
	fp.write (probe_label)
	for i in range (len (min_indices)) :
		probe_min_date_match = 0
		index = min_indices[i]
		dist = min_distances[i]
		min_label = e_gallery_list[index][label_idx]
		min_image = e_gallery_list[index][img_idx]
		min_chip = e_gallery_list[index][chip_idx]
		# pdb.set_trace ()
		if min_label == probe_label :
			match = 1
			# write out info if labels match and dates match i.e. potential bias
			if db_df is not None :
				# pdb.set_trace ()
				min_datetime = get_file_datetime ([min_image], db_df)
				min_date = min_datetime [0]
				min_time = min_datetime [1]
				if min_date[0] == probe_date[0] :
					probe_min_date_match = 1
				fp_matchinfo.write (min_label + ';' + str (dist)
					+ ';' + str (probe_date[0]) 
					+ ';' + str (probe_time[0])
					+ ';' + str (min_date[0])
					+ ';' + str (min_time[0])
					+ ';' + probe_image
					+ ';' + min_image
					+ ';' + probe_chip
					+ ';' + min_chip
					+ ';' + str (probe_min_date_match)
					+ '\n')
		fp.write ('; ' + str (i) + '; ' + min_label + '; ' + str (dist))
		# fp.write (';' + min_image + ';' + str (min_date[0]) + ';' + str (min_time[0]))
		# fp.write (';' + probe_image + ';' + str (probe_date[0]) + ';' + str (probe_time[0]))
	fp.write ('; ' + str (match) + '\n')
	return match

##------------------------------------------------------------
##  write closest info to file.  if match and has file info db,
##    write data to file for viewing and checking for data bias (leak)
##  format: label;distance; date1;time1,date2; time2; 
##			image1, image2, chip1, chip2
## 
##  probe_info & e_gallery_list content:
##       [label, embed_file, embed_floats, img_file, chip_file]
##	  returned from get_embedding_list_from_objs
##------------------------------------------------------------
def write_closests_info (e_gallery_list, fp, min_indices, 
		min_distances, probe_info, db_df, fp_matchinfo) :
	pdb.set_trace ()
	label_idx = 0
	img_idx = 3
	chip_idx = 4
	match = 0
	probe_label = probe_info[label_idx]
	probe_image = probe_info[img_idx]
	probe_chip = probe_info[chip_idx]
	matched_labels = []
	fp.write (probe_label)
	match_str = ''
	for i in range (len (min_indices)) :
		index = min_indices[i]
		matched_dist = min_distances[i]
		matched_label = e_gallery_list[index][label_idx]
		# pdb.set_trace ()
		match_str += '; ' + str (i) + '; ' + matched_label + '; ' + str (matched_dist)
		matched_labels.append (matched_label)
	top_common = Counter(matched_labels).most_common()
	counter_str = ''
	# creating str for count of labels
	# pdb.set_trace ()
	for i in range (len (top_common)) :
		counter_str += '{' + top_common[i][0] + ':' + str (top_common[i][1]) + '} '
		
	match = 0
	# need to check for zero top??
	if len (top_common) == 1 or top_common[0][1] > top_common[1][1] :  # majority
		matching_label = top_common[0][0]
		if matching_label == probe_label :
			match = 1
	else :  # no majority
		matching_label = '---'
	fp.write ('; ' + matching_label + ';' + str (match) + ';' + counter_str + '\n')
	return matching_label, matched_labels
##------------------------------------------------------------
##  output csv of distances to each train embeddings
##   given filename of test embeddings, filename of train embeddings
##   and csv output filename, write out matrix all train distances from
##   each test embedding
##------------------------------------------------------------
def gen_embed_dist_csv (test_files, train_files, csv_file, db, match_n, write_stats=False, filetype="embeds") :
	# pdb.set_trace ()
	e_test_d = defaultdict (list)
	e_train_d = defaultdict (list)
	load_objs_from_files (test_files, e_test_d, filetype)
	load_objs_from_files (train_files, e_train_d, filetype)
	
	# pdb.set_trace ()
	# with open (csv_file, 'w') as fp:
		# for i in range (len (e_test_list)) :
			# write train label across top
			# fp.printf (e_train_list)
			# write_csv (e_test_list[i], e_train_list, fp)
	test_files_sort = sorted (test_files)
	train_files_sort = sorted (train_files)
	# pdb.set_trace ()
	files_eq = test_files_sort == train_files_sort
	write_csv_embed_distances (e_test_d, e_train_d, csv_file, db, match_n, files_eq, write_stats)

##------------------------------------------------------------
##  write_dist_csv - given emedding, list of embeddings,
##     and file pointer, write out embedding distances into file
##	   separated by ';'
##     also include min distance and index to its label
##	   returns index of nearest neighbor and distance to nearest neighbor
##------------------------------------------------------------
def write_dist_csv (probe_distinfo, e_gallery, fp, nearest_n) :
	# pdb.set_trace ()
	e_probe = probe_distinfo[0]
	if np.isnan(np.sum(e_probe)) :
		print ('NaN in probe')
		pdb.set_trace ()
	if np.isnan(np.sum(e_gallery)) :
		print ('NaN in gallery')
		pdb.set_trace ()
	e_distance_list = get_embed_distances_e_elist (e_probe, e_gallery)
	for i in range (len (e_distance_list)) :
		fp.write ('; ' + str (e_distance_list[i]))
	index = range (len (e_distance_list))
	index_list = [list(x) for x in zip(index, e_distance_list)]
	index_list.sort(key=lambda x:x[1])
	n = 0
	min_distances = []
	min_indices = []
	probe_date = 0
	if len (probe_distinfo) > 1 :
		probe_date = probe_distinfo[1]
	for index_dist in index_list :
		# pdb.set_trace ()
		if index_dist[1] == 0.0 :
			continue
		dist = index_dist[1]
		index = index_dist[0]
		min_distances.append (dist)
		min_indices.append (index)
		n += 1
		if n == nearest_n :
			break
		fp.write ('; ' + str (dist) + '; ' + str (index))
	fp.write ('\n')
	return min_indices, min_distances

##------------------------------------------------------------
##  get_count_list
##------------------------------------------------------------
def get_count_list (counts_file) :
	nums = []
	with open (counts_file) as fp:
		counts = fp.readlines ()
		for count_str in counts:
			if not count_str.strip() :
				continue
			count = int (count_str)
			nums.append (count)
	return nums

##------------------------------------------------------------
##  Generate a new xml file with matching count of labels as
##    specified in count list.  Used to create new data set.
##------------------------------------------------------------
def xml_match_cnt (xml_files, counts_file, xml_out, filetype) :
	objs_d = defaultdict(list)
	obj_files = load_objs_from_files (xml_files, objs_d, filetype)
	if len (objs_d) == 0 :
		return
	match = []
	counts = get_count_list (counts_file)
	counts.sort (reverse=True)
	found = False
	for count in counts:
		print ("..... searching for", count, "images.")
		random.shuffle (list(objs_d.items()))
		for label, objs in list(objs_d.items()):
			found = False
			if len (objs) < count :
				print ("...... label", label, "too few (0).")
				continue
			found = True
			print ("...... label", label, "matches at ", len (objs), ", needed ", count)
			random.shuffle (objs)
			match.extend (objs[:count])
			objs_d.pop(label)
			break
		# here if unable to find enough images for current count
		if not found :
			print ("*** Error: unable to find match for ", count, " images.")
	write_xml_file (xml_out, match, filetype)
	print ("... wrote xml to file: ", xml_out)

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
##                   -pattern <pattern_file>
##                   -list <list_file>
##                   -years <start_year> <end_year>
##                   -label_minmax <min> <max> 
##                   -label_video_minmax <min> <max> 
##                   -video_image_percent <percent_per_video>
##                   -video_image_count <count_per_video>
##                   -labels <list>
## now:
##------------------------------------------------------------
def extract_subsets  (files, output, extract_type, extract_arg, db, parent_path, filetype="chips") :
	# pdb.set_trace ()
	chips_d = defaultdict(list)
	if extract_type == 'pattern' :
		xml_split_by_patterns (files, extract_arg, output, filetype)
	elif extract_type == 'list' :
		xml_split_by_files (files, extract_arg, output, filetype)
	elif extract_type == 'years' :
		xml_split_by_years (files, extract_arg, output, filetype)
	elif extract_type == 'label_minmax' :
		label_min = extract_arg[0]
		label_max = extract_arg[1]
		extract_labels_minmax (files, db, label_min, label_max, output, filetype)
	elif extract_type == 'label_video_minmax' :
		video_min = extract_arg[0]
		video_max = extract_arg[1]
		# TODO code up
		extract_video_labels_minmax (files, db, label_min, label_max, output, filetype)
	elif extract_type == 'video_image_percent' :
		vimage_percent = extract_arg
		extract_video_image_percent (files, db, vimage_percent, parent_path, output)
	elif extract_type == 'video_image_count' :
		vimage_count = extract_arg
		extract_video_image_count (files, db, vimage_count, output)
	elif extract_type == 'labels' :
		labels = extract_arg
		extract_labels (files, labels, output)
	else :
		print ('Error: unrecgnized extract type', extract_type)
		return
	return

##------------------------------------------------------------
##  partition all files into x and y percent
##------------------------------------------------------------
def generate_partitions (files, x, output, split_type, split_arg, db, filetype="chips") :
	# print "partitioning chips into: ", x, " ", y
	# pdb.set_trace ()
	y = x if x < 50 else 100 - x
	x = 100 - y
	chips_d = defaultdict(list)
	# pdb.set_trace ()
	if 0 : ## this should be in extract_subset
		if split_type == 'years' :
			if output is None:
				output = files[0]
			xml_split_by_years (files, split_arg, output, filetype)
			return
		if split_type == 'list' :
			xml_split_by_files (files, split_arg, output, 'chips')
			return
		if split_type == 'pattern' :
			xml_split_by_patterns (files, split_arg, output, 'chips')
			return
	# load_objs_from_files (files, chips_d, filetype)
	# pdb.set_trace ()
	csv_filename = split_arg
	chunks = partition_objs (files, x, y, filetype, split_type, split_arg, db)
	# chunks = partition_xy_with_dates (files, csv_filename, x, y)
	# chunks = partition_objs (chips_d, x, y, shuffle, img_cnt_min, test_min, image_size_min, filetype, day_grouping, csv_filename)
	# pdb.set_trace ()
	file_x = make_new_name (output, '_'+str (x))
	file_y = make_new_name (output, '_'+str (y))
	file_small_img = file_unused = None
	# generate_partition_files (chunks, filenames, filetype)
	if filetype == 'video_chips' :
		filetype = 'chips'
	generate_xml_from_objs (chunks[g_x], file_x, filetype)
	generate_xml_from_objs (chunks[g_y], file_y, filetype)
	total_images = len (chunks[g_x]) + len (chunks[g_y])
	print ('Partitioned', total_images, 'images into', len (chunks[g_x]), ':', len (chunks[g_y]))
	print ('Partition files generated.')
	print ('\t', str (len (chunks[g_x])), 'chips written to', file_x)
	print ('\t', str (len (chunks[g_y])), 'chips written to', file_y)
	print ()

##------------------------------------------------------------
##  partition all files into x and y percent
##------------------------------------------------------------
def generate_partitions_old (files, x, y, output, split_by_label=False, split_by_list_file=None, shuffle=True, img_cnt_min=0, img_cnt_cap=0, test_min=0, image_size_min=0, label_group_minimum=0, filetype="chips", split_by_day_grouping=False, csv_filename=None) :
	# print "partitioning chips into: ", x, " ", y
	# pdb.set_trace ()
	if x < y :
		tmp_x = x
		x = y
		y = tmp_x
	chips_d = defaultdict(list)
	# pdb.set_trace ()
	if split_by_list_file :
		xml_split_by_files (files, split_by_list_file, output, 'chips')
		return
	split_type="chips" 
	if split_by_label :
		split_type = 'by_label'
	elif split_by_day_grouping :
		split_type = 'day_grouping'
	# # load_objs_from_files (files, chips_d, filetype)
	# pdb.set_trace ()
	chunks = partition_objs (files, x, y, shuffle, img_cnt_min, test_min, image_size_min, label_group_minimum, filetype, split_type, csv_filename)
	# chunks = partition_xy_with_dates (files, csv_filename, x, y)
	print ('files partitioned into:', len (chunks[g_x]), ':', len (chunks[g_y]))
	# chunks = partition_objs (chips_d, x, y, shuffle, img_cnt_min, test_min, image_size_min, filetype, day_grouping, csv_filename)
	# pdb.set_trace ()
	file_x = output + "_" + str(x) + ".xml"
	file_y = output + "_" + str(y) + ".xml"
	file_small_img = file_unused = None
	if len (chunks) > g_unused :
		if len (chunks[g_unused]) > 0 :
			file_unused = output + "_unused" + ".xml"
			generate_xml_from_objs (chunks[g_unused], file_unused, filetype)
			print('\t', len (list_unused), 'labels unused, failing minimum # of images, written to file : \n\t', file_unused, '\n')
	if len (chunks) > g_small_img :
		if len (chunks[g_small_img]) > 0 :
			file_small_img = output + "_small_faceMeta" + ".xml"
			generate_xml_from_objs (chunks[g_small_img], file_small_img, filetype)
			print(len (list_small_img), 'unused chips below min size written to file : \n\t', file_small_img, '\n')
	# generate_partition_files (chunks, filenames, filetype)
	generate_xml_from_objs (chunks[g_x], file_x, filetype)
	generate_xml_from_objs (chunks[g_y], file_y, filetype)

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
##  returns true if includig new addition will get closer to nom_count
##------------------------------------------------------------
def new_row_closer_to_nom (nom_count, addition, cur_count, max_count) :
	nom_diff = abs (nom_count - cur_count)
	new_diff = abs (nom_count - (cur_count + addition))
	if cur_count + addition > max_count :
		return False
	if new_diff < nom_diff :
		return True

##------------------------------------------------------------
##   given group_by pandas series index, return list of 
##   [label date]
##------------------------------------------------------------
def	create_label_date_list_from_indices (groups, indices) :
	# pdb.set_trace ()
	subgroup_data = []
	for i in indices : 
		row_tuple = groups.index[i] 
		row = [row_tuple[0], row_tuple[1]]
		subgroup_data.append (row)
	return subgroup_data

##------------------------------------------------------------
##  given panda series with label-date group counts, split rows to match
##  x and y partitions. return list of df row indices 
##  iterate through table, looking for common label, then split 
##------------------------------------------------------------
def partition_df_rows_x  (grouped, num_images, x, y) :
	pdb.set_trace ()
	partition_margin = .5
	min_count, nom_count, max_count = get_min_nom_max (num_images, x, y, partition_margin)
	print ('min:', min_count, '\tnom:', nom_count, '\tmax:', max_count)
	y_count = x_count = 0
	x_done = False
	group_x = []
	group_y = []
	# keep adding to x until above min count
	for i in range (len (grouped)) :
		row_count = grouped[i]
		if x_done :
			y_count += row_count
			group_y.append (i)
			continue
		if new_row_closer_to_nom (nom_count, row_count, x_count, max_count) :
			x_count += row_count
			group_x.append (i)
		else :
			y_count += row_count
			group_y.append (i)
		if x_count >= nom_count :
			x_done = True
	if x_count < min_count or x_count > max_count :
		print ('\n\tWarning: x partition outside goal of ', min_count, 'and', max_count, '\n')
	print ('splitting', num_images, 'images into ratios of', x, 'and', y)
	print ('partition x:', x_count, 'images in ', len (group_x), 'groups.')
	print ('partition y:', y_count, 'images in ', len (group_y), 'groups.')
	return group_x, group_y

##------------------------------------------------------------
##  given panda series of label-date group counts, split rows to match
##  x and y partitions. return list of df row indices 
##  iterate through list of label-day table. for each newly encountered
##    label, get all the counts of that label (e.g. bc_bella [2,4,1,5,6,3,2])
##    split into x, y groups ([6,5,4,3],[2,2,1])

##------------------------------------------------------------
def partition_df_rows (grouped, num_images, x, y) :
	# pdb.set_trace ()
	v = grouped.values 
	v_list = v.tolist ()
	n_images = sum (v_list)
	# end debug

	partition_margin = .5
	group_x = []
	group_y = []
	current_label = None
	processed_labels = []
	# pdb.set_trace ()
	y_count = 0
	x_count = 0
	x_group_label = []
	y_group_label = []
	label_y_count = label_x_count = 0
	group_sum_x = 0
	group_sum_y = 0
	for i in range (len (grouped)) :
		label = grouped.index[i][0]
		if label != current_label :
			# pdb.set_trace ()
			# ensure that x_group_label and y_group_label is empty
			if len (x_group_label) > 0 :
				print ('Error: switching labels but x group not empty')
			if len (y_group_label) > 0 :
				print ('Error: switching labels but y group not empty')
			if label in processed_labels :
				print ('Error: Already processed label', label)
				continue  # maybe do something more?
			if current_label is not None :
				processed_labels.append (current_label)
			# wrap up current label
			if get_verbosity () > 1 :
				print ('x_count2:', label_x_count, '\ty_count:', label_y_count)
			if label_x_count != group_sum_x :
				print ('Error: Partition for', label, 'expects x : ', group_sum_x, ', got', label_x_count)
			if label_y_count != group_sum_y :
				print ('Error: Partition for', label, 'expects y : ', group_sum_y, ', got', label_y_count)
			x_count += label_x_count
			y_count += label_y_count
			label_y_count = label_x_count = 0
			group_sum_x = group_sum_y = 0
			# init new label
			current_label = label
			# get all groups of that label
			label_groups = grouped [label]
			# pdb.set_trace ()
			if len (label_groups) < 3 and get_verbosity () > 1 :
				print ('label[0]:', label, ':', label_groups.index[0], 
						':', label_groups.iloc[0])
				if len (label_groups) == 2 :
					print ('label[1]:', label, ':', label_groups.index[1],
						   ':', label_groups.iloc[1])
			# get partitions
			if get_verbosity () > 1 :
				print (current_label, end=' ')
			x_group_label, y_group_label = get_label_x_y_counts (label_groups, x, y, partition_margin)
			group_sum_x = sum (x_group_label)
			group_sum_y = sum (y_group_label)
			# pdb.set_trace ()
		row_count = grouped[i]
		if row_count in x_group_label : 
			label_x_count += row_count
			group_x.append (i)
			x_group_label.remove (row_count)
		else :
			if row_count not in y_group_label :
				print ('Error: group count on found in x nor y')
			label_y_count += row_count
			group_y.append (i)
			y_group_label.remove (row_count)
	x_count += label_x_count
	y_count += label_y_count
	# pdb.set_trace ()
	min_count, nom_count, max_count = get_min_nom_max (num_images, x, y, partition_margin)
	if x_count < min_count or x_count > max_count :
		print ('\n\tWarning: Unable to partition within ', partition_margin, '% of ', x, 'between', min_count, 'and', max_count, '\n')
	print ('splitting', num_images, 'images into ratios of', x, 'and', y)
	print ('partition x:', x_count, 'images in ', len (group_x), 'groups.')
	print ('partition y:', y_count, 'images in ', len (group_y), 'groups.')
	return group_x, group_y

##------------------------------------------------------------
##  given list of dates for a label and count of images
##     for each date, return list of numbers that make
##     up partitions x and y
##  e.g. [5,3,6,1,2,1,2,2,1] -> [6,5,3,2,2,2,1,1,1]
##     returns [6,5,3,2,2] [2,1,1,1]
##------------------------------------------------------------
def get_label_x_y_counts (label_groups, x, y, partition_margin) :
	# get all values of the groups
	group_values = label_groups.values 
	vals_list = group_values.tolist ()
	vals_list.sort (reverse=True)
	num_label_images = sum (group_values)
	min_count, nom_count, max_count = get_min_nom_max (num_label_images, x, y, partition_margin)
	if get_verbosity () > 1 :
		print ('total:', num_label_images, '\tmin:', min_count, '\tnom:', 
			nom_count, '\tmax:', max_count)
	label_y_count = label_x_count = 0
	x_group = []
	y_group = []
	x_done = False
	# pdb.set_trace ()
	# handle special case of 1 and 2 vals
	if len (vals_list) < 3 :  
		x_group.append (vals_list[0])
		label_x_count += vals_list[0]
		if len (vals_list) == 2 :
			label_y_count += vals_list[1]
			y_group.append (vals_list[1])
	else :
		for i in range (len (vals_list)) :
			row_count = vals_list[i]
			# keep adding to group_x until above min count (x_done == True)
			if not x_done and new_row_closer_to_nom (
					nom_count, row_count, label_x_count, max_count) :
				label_x_count += row_count
				x_group.append (row_count)
			else :
				label_y_count += row_count
				y_group.append (row_count)
			if label_x_count >= nom_count :
				x_done = True
	if get_verbosity () > 1 :
		print ('x_count1:', label_x_count, '\ty_count:', label_y_count)
		if label_x_count > max_count :
			print ('Warning: x_count above max. Values: ', vals_list)
		if label_x_count < min_count :
			print ('Warning: x_count below min. Values: ', vals_list)
	return x_group, y_group 

##------------------------------------------------------------
##  don't need this
##------------------------------------------------------------
def get_num_label_images (grouped, idx, label) :
	count = 0
	for i in range (idx, len (grouped)) :
		cur_label = grouped.index[i][0]
		if label == cur_label :
			count += grouped [i]
		else :
			return count

##------------------------------------------------------------
##  given groupings and label, extract group counts and indices
##------------------------------------------------------------
def get_label_db_info (grouped, label) :
	print ('function get_label_count needs to be implemented ')
	return 0, 0
	# return label_count, groups, group_idxs


##------------------------------------------------------------
##------------------------------------------------------------
def get_min_nom_max (count, x, y, margin=.5) :
	val_nom = int (count * x / 100)
	val_min = int (count * (x-margin) / 100)
	val_max = int (count * (x+margin) / 100)
	return val_min, val_nom, val_max
	
##------------------------------------------------------------
##  image = df.iloc[i]['IMAGE']
##  given grouped dataframe, extract image names
##  e.g. 
##               IMAGE     LABEL      DATE TEST_TRAIN            DATE_TIME
## 637  imageSource...  bc_steve  20150824      train  2015:08:24 14:31:05
## 638  imageSource...  bc_steve  20150824       test  2015:08:24 14:31:06
## 639  imageSource...  bc_steve  20150824      train  2015:08:24 14:31:33
##------------------------------------------------------------
def	get_images_from_group (groups, selected_rows) :
	images = []
	pdb.set_trace ()
	for label_date, group in groups:
		for index, row in group.iterrows () :
			image = row['IMAGE']
			images.append (image)
	return images

	# label = label_date[0]
	# date = label_date[1]
	# groups.get_group ((label, date))



##------------------------------------------------------------
##------------------------------------------------------------
def images_from_label_date (groups, label_dates) :
	images = []
	for label_date in label_dates :
		label = label_date[0]
		date = label_date[1]
		# print ('label_date :', label_date)
		# print ('label      :', label)
		# print ('date       :', date)
		# continue
		group = groups.get_group ((label, date))
		for index, row in group.iterrows () :
			image = row['IMAGE']
			images.append (image)
	pdb.set_trace ()
	return images

##------------------------------------------------------------
##  given indices into table of (label, date), count
##    return list of (label, date) at indices
##------------------------------------------------------------
def get_label_date_from_indices (label_day_group_counts, indices) :
	label_dates = []
	for group_index in indices :
		label_date = label_day_group_counts.index[group_index]
		label_dates.append (label_date)
	return label_dates

##------------------------------------------------------------
#  same?? as def xml_split_by_list (orig_file, new_files, output_file, filetype='faces') :
##------------------------------------------------------------
def split_chips_by_images (chips_d, images_x) :
	return 5


##------------------------------------------------------------
## given dataframe with column name, return all values of 
##    specified column
##------------------------------------------------------------
def	get_image_list_from_df (df, img_column) :
	vals = []
	for col_name, data in df.items () :
		if col_name == img_column :
			for i in range (len (data)) :
				val = data[i] 
				vals.append (val)
				# pdb.set_trace ()
			return vals

##------------------------------------------------------------
##------------------------------------------------------------
def test_utils () :
	pdb.set_trace ()
	print ('hello world!')

##------------------------------------------------------------
##  given list of images, return list of uniq label
##------------------------------------------------------------
def get_all_labels (objs_d) :
	labels = []
	for label, objs in list(objs_d.items ()) :
		labels.append (label)
	return labels

##------------------------------------------------------------
##  given filenames, return list of dates and times.  
##    (how ordered?? )
##------------------------------------------------------------
def get_file_datetime (obj_filenames, df_all) :
	parent_path='/home/data/bears/'
	parent_path='/data/bears/'
	# pdb.set_trace ()
	### fix path to ensure filename will match image field in csv
	filenames = [f.replace (parent_path, '') for f in obj_filenames]
	df_images = pandas.DataFrame (filenames, columns=['IMAGE'])
	# get table from list of images
	df_images_info = pandas.merge (df_all, df_images, on=['IMAGE'], how='inner')
	# get date and time from result
	dates = get_image_list_from_df (df_images_info, 'DATE')
	times = get_image_list_from_df (df_images_info, 'TIME')
	# datetime = [dates, times]
	return [dates, times]

##------------------------------------------------------------
##  given list of image filenames and csv of image info
##  return dataframe of info for specified images
##  if the data is not in db, then no information is returned.
##------------------------------------------------------------
def get_files_info_df (obj_filenames, db_csv_filename, 
	parent_path='/home/data/bears/', filetype='chips') :
	# print ('parent path set to:', parent_path)
	pdb.set_trace ()
	### fix path to ensure filename will match image field in csv
	filenames = [f.replace (parent_path, '') for f in obj_filenames]
	if filetype == 'video_chips' :
		videonames = [f[:-17] for f in filenames] 
		filenames = videonames
	df_all = pandas.read_csv (db_csv_filename, sep=';')
	df_images = pandas.DataFrame (filenames, columns=['IMAGE'])
	# get table from list of images
	df_images_info = pandas.merge (df_all, df_images, on=['IMAGE'], how='inner')
	return df_images_info

##------------------------------------------------------------
##  given a list of images, and csv of image info, 
##  return count of each label-day groups
##------------------------------------------------------------
def get_label_day_groups (obj_filenames, db_csv_filename) :
	df_images_table = get_files_info_df (obj_filenames, db_csv_filename)
	groups_label_date = df_images_table.groupby (['LABEL', 'DATE'])
	# pdb.set_trace ()
	# groups_label_date.get_group (('bc_kwatse', 20110830))
	# create table of count of each label-date group
	label_day_group_counts = groups_label_date.size () 
	return label_day_group_counts

##------------------------------------------------------------
##  given label_date_groups, indices into group_list and image info
##  return list of images from indices label_date_group_list
##------------------------------------------------------------
def get_images_from_indices (label_date_groups, group_indices, df_images_db) :
	# get [label, date] lists of each group
	#     e.g. [['bc_adeane', 20140905], ['bc_also', 20160810]... ]
	label_date_list = create_label_date_list_from_indices (
						label_date_groups, group_indices)
	images = get_images_for_label_dates (label_date_list, df_images_db)
	return images

##------------------------------------------------------------
##  given list of [label date], return images matching those labels and dates
##------------------------------------------------------------
def get_images_for_label_dates (label_date_list, df_images_db) :
	df_label_date = pandas.DataFrame (label_date_list, columns=['LABEL', 'DATE'])
	# join label_date list with images db to get images info
	df_label_date_info = pandas.merge (df_images_db, df_label_date, 
						on=['LABEL', 'DATE'], how='inner')
	# extract images to list
	images = get_image_list_from_df (df_label_date_info, 'IMAGE')
	return images

##------------------------------------------------------------
#  given obj dict, group into x and y with mutually exclusive
#  labels in each group
##------------------------------------------------------------
def partition_files_by_label (filenames, x, y, filetype="chips") :
	objs_d = defaultdict(list)
	obj_filenames = load_objs_from_files (filenames, objs_d, filetype)
	num_images = len (obj_filesname)
	partition_margin = .5
	objs_x = []
	objs_y = []
	min_count, nom_count, max_count = get_min_nom_max (num_images, x, y, partition_margin)
	labels=list(objs_d.keys())
	random.shuffle (labels)
	x_count = 0
	y_count = 0
	label_x_cnt = 0
	for label in labels :
		new_count = len (objs_d[label])
		if new_row_closer_to_nom (nom_count, new_count, x_count, max_count) :
			x_count += new_count
			objs_x.extend (objs_d[label])
			label_x_cnt += 1
		else :
			y_count += new_count
			objs_y.extend (objs_d[label])
	if get_verbosity () > 0 :
		print ('label split of', x, 'and', y, 'results in', str (x_count), 'and', str (y_count), 'images and label count of', str (label_x_cnt), 'and', str (len (labels)-label_x_cnt))
	return [objs_x, objs_y]

##------------------------------------------------------------
##  given list of images, return list of only one image per day per label
##------------------------------------------------------------
def extract_single_label_group_image (chip_file, csv_filename, output_file) :
	objs_d = defaultdict(list)
	obj_filenames = load_objs_from_files ([chip_file], objs_d, 'chips', 'source')
	if get_verbosity () > 0 :
		print ('input number of images:', len (obj_filenames))
	parent_path='/home/data/bears/'
	df_images_info = get_files_info_df (obj_filenames, csv_filename, parent_path)
	groups_label_date = df_images_info.groupby (['LABEL', 'DATE'])
	# [['bc_adeane', 20140905]:1,['bc_also', 20160810],5] .. []]
	pdb.set_trace ()
	label_day_group_counts = groups_label_date.size () 
	if get_verbosity () > 0 :
		print ('number of label-day groups:', len (label_day_group_counts))
	# get list of label-date 
	# [['bc_adeane', 20140905],['bc_also', 20160810] .. []]
	label_date_list = create_label_date_list_from_indices (
				label_day_group_counts, range (len (label_day_group_counts)))
	# for each label-day group, select random image to include
	singles = []
	for label_date in label_date_list :
		images = get_images_for_label_dates ([label_date], df_images_info)
		image = random.choice (images)
		singles.append (image)
	localized_singles = [parent_path+s for s in singles]
	objs_singles, objs_not_singles = obj_split (objs_d, localized_singles, 'source', 'files')
	if get_verbosity () > 0 :
		print ('count of singles images :', len (objs_singles))
		print ('count of extr    images :', len (objs_not_singles))
	generate_xml_from_objs (objs_singles, output_file)
	return

##------------------------------------------------------------
# partition by groups
# if chips_d is None, then input was csv
# 	1. Read CSV
# 	2. Create grouping by label, date, image count
# 	3. partition into x, y
# 	4. generate list of label-dates for each group
# 	5. use label-dates list of label-dates generate two new xml
# 	6. IMAGE;LABEL;DATE;TEST_TRAIN;DATE_TIME
# else 
#	convert chips_d to chips_table
#	read CVS to cvs_df
#   select label, date from join chips with csv_df
#   A2
#	A3
#	A4
# 	use list of label-dates to generate two new xml
#
# 
#
#   
##------------------------------------------------------------
def partition_files_by_group (obj_filenames, objs_d, x, y, csv_filename, label_group_minimum) :
	parent_path='/home/data/bears/'
	# pdb.set_trace ()
	df_images_info = get_files_info_df (obj_filenames, csv_filename, parent_path)
	groups_label_date = df_images_info.groupby (['LABEL', 'DATE'])
	# [['bc_adeane', 20140905]:1,['bc_also', 20160810],5] .. []]
	label_day_group_counts = groups_label_date.size () 
	# group_count_rand = label_day_group_counts.sample (frac=1) # randomize order
	# partition - looking for something like [1,2,3,7 ] [4,5,6,8,9,10]

	dropped_images_cnt = 0
	labels = get_all_labels (objs_d)
	if label_group_minimum > 0 :
		label_day_group_counts, dropped_images_cnt = remove_labels_too_few (labels, 
							label_day_group_counts, label_group_minimum);

	group_idx_x, group_idx_y = partition_df_rows (label_day_group_counts, 
		len (obj_filenames)-dropped_images_cnt, int (x), int (y))

	x_images_list = get_images_from_indices (label_day_group_counts, 
					group_idx_x, df_images_info)
	y_images_list = get_images_from_indices (label_day_group_counts, 
					group_idx_y, df_images_info)
	
	localized_images_x_list = [parent_path+s for s in x_images_list]
	localized_images_y_list = [parent_path+s for s in y_images_list]
	return localized_images_x_list, localized_images_y_list

##------------------------------------------------------------
##  remove labels that have fewer groups than min
##------------------------------------------------------------
def remove_labels_too_few (labels, label_day_group_counts, label_group_minimum) :
	# pdb.set_trace ()
	dropped_labels = []
	dropped_count = []
	for label in labels :
		label_group_counts = label_day_group_counts [label]
		label_group_count_values = label_group_counts.values 
		if len (label_group_count_values) < label_group_minimum :
			# pdb.set_trace ()
			dropped_count.append (sum (label_group_count_values))
			dropped_labels.append (label)
			label_day_group_counts = label_day_group_counts.drop(labels=label)
	print ('--------------------')
	print (sum (dropped_count), 'images and', len (dropped_labels), 'labeld were dropped due to label-date group minimum of', label_group_minimum)
	print ('--------------------')
	if get_verbosity () > 0 and len (dropped_labels) > 0 :
		print ('\nDropped labels and image counts:')
		print ('--------------------')
		for i in range (len (dropped_labels)) :
			print (dropped_labels[i], '; ', dropped_count[i])
	return label_day_group_counts, sum (dropped_count)


##------------------------------------------------------------
##  for each label, extract n random objects across year,season
##   and date.
##------------------------------------------------------------
def select_label_minmax (xml_filenames, db, m, n, filetype='chips') :
	# pdb.set_trace ()
	db_df = pandas.read_csv (db, sep=';')
	return 0


	hier_d_objs = defaultdict (lambda:defaultdict(lambda: defaultdict(lambda: defaultdict(list))))
	hier_load_objs_from_files (filenames, hier_d_objs)
	db_df = pandas.read_csv (db, sep=';')
	count = hier_objs_len (hier_d_objs, [], [], [], [])
	print ('all iamges (18):', count)
	count = hier_objs_len (hier_d_objs, [], ['2014', '2016'], [], [])
	print ('years 2014, 2016 (11):', count)
	count = hier_objs_len (hier_d_objs, [], [], ['spring'], [])
	print ('spring (11):', count)
	count = hier_objs_len (hier_d_objs, ['bf_273', 'bc_toffee'], [], [], [])
	print ('273 & toffee (7):', count)
	

	# hier_objs_print (hier_d_objs, filetype='chips')

	return 0

##------------------------------------------------------------
##   return the most number of 
##     videos of count between m and n, and evenly distributed  
##	   among years, season and days.
##------------------------------------------------------------
def extract_video_labels_minmax (xml_filenames, image_db, m, n, output_file, filetype='chips') :
	print ('empty function extract_video_labels_minmax')
	return

##------------------------------------------------------------
##   return a percent of images in a video
##   now:
##------------------------------------------------------------
def extract_video_image_percent (filenames, vdb, vimage_percent, parent_path, output) :
	print ('in extract_video_image_percent')
	vchips_d = defaultdict (list)  
	df_db = get_video_chips_info_df (filenames, vdb, vchips_d, parent_path)
	videos = df_get_video_list (df_db)
	all_images = []
	matched_cnt = 0
	for video in videos :
		df_video_images = df_get_video_images (df_db, video)
		step = int (100 / vimage_percent)
		indices = list (range (0, len (df_video_images), step))
		# pdb.set_trace ()
		matched_cnt += len (indices)
		print ('... grabbing', len (indices), 'images out of', len (df_video_images), 'in video')
		# TODO : images = [df_video_images.iloc[i]['IMAGE'] for i in indices]
		images = []
		for i in indices :
			images.append (df_video_images.iloc[i]['IMAGE'])
		all_images.extend  (images)
	print ('\n... total selected', matched_cnt, 'images out of', len (df_db), 'total.')
	matched_objs, unmatched_objs = split_objs_by_filenames (vchips_d, all_images)
	matched_filename = make_new_name (output, '_'+str (vimage_percent))
	unmatched_filename = make_new_name (output, '_'+str (100-vimage_percent))
	generate_xml_from_objs (matched_objs, matched_filename, 'chips')
	generate_xml_from_objs (unmatched_objs, unmatched_filename, 'chips')
	print ('Extracted', vimage_percent, 'percent of the video images.')
	print ('\t', str (len (matched_objs)), 'chips written to', matched_filename)
	print ('\t', str (len (unmatched_objs)), 'chips written to', unmatched_filename)
	return

##------------------------------------------------------------
##   return a max number of images in a video
##   same as percent, but for each video percent = max_img / num_images
##------------------------------------------------------------
def extract_video_image_count (filenames, vdb, count, output) :
	print ('in extract_video_image_count')
	vchips_d = defaultdict (list)  
	df_db = get_video_chips_info_df (filenames, vdb, vchips_d)
	videos = df_get_video_list (df_db)
	all_images = []
	for video in videos :
		df_video_images = df_get_video_images (df_db, video)
		num_imgs = len (df_video_images)
		if num_imgs <= count :
			images = df_video_images['IMAGE'].values.tolist ()
			all_images.extend  (images)
			print ('... using all', num_imgs, 'images in video')
			continue
		step = (num_imgs+1)/count
		indices_f = np.arange (0, num_imgs, step)
		indices = [int (round (f)) for f in indices_f]
		if len (indices) != count :
			print ('Expecting', count, 'images, getting', len (indices))
			pdb.set_trace ()
		print ('... grabbing', len (indices), 'images out of', len (df_video_images), 'in video')
		# TODO : images = [df_video_images.iloc[i]['IMAGE'] for i in indices]
		images = []
		# pdb.set_trace ()
		for i in indices :
			images.append (df_video_images.iloc[i]['IMAGE'])
		all_images.extend  (images)
	print ('\n... total selected', len (all_images), 'images out of', len (df_db), 'total.')
	matched_objs, unmatched_objs = split_objs_by_filenames (vchips_d, all_images)
	matched_filename = make_new_name (output, '_max'+str (count))
	unmatched_filename = make_new_name (output, '_max'+str (count)+'_remainder')
	generate_xml_from_objs (matched_objs, matched_filename, 'chips')
	generate_xml_from_objs (unmatched_objs, unmatched_filename, 'chips')
	print ('Extracted max', count, 'of video images.')
	print ('\t', str (len (matched_objs)), 'chips written to', matched_filename)
	print ('\t', str (len (unmatched_objs)), 'chips written to', unmatched_filename)
	return

##------------------------------------------------------------
##   extract all chips with specified labels
##------------------------------------------------------------
def extract_labels (files, labels, output) :
	objs_d = defaultdict(list)
	obj_filenames = load_objs_from_files (files, objs_d, 'chips', 'source')
	matched_objs, unmatched_objs = obj_split (objs_d, labels, 'file', 'labels')
	matched_filename = make_new_name (output, '_matched')
	unmatched_filename = make_new_name (output, '_unmatched')
	generate_xml_from_objs (matched_objs, matched_filename, 'chips')
	generate_xml_from_objs (unmatched_objs, unmatched_filename, 'chips')
	all_labels = list (objs_d.keys())
	matched_labels = set (all_labels) & set (labels)
	print ('Extracted files based on labels.')
	print ('\t', str (len (matched_objs)), 'chips with', len (matched_labels), 'labels written to', matched_filename)
	print ('\t', str (len (unmatched_objs)), 'chips with', len (all_labels) - len (matched_labels), 'labels written to', unmatched_filename)
	return

##------------------------------------------------------------
##   given csv of images and dates, return the most number of 
##     images of count between m and n, and evenly distributed  
##	   among years, season and days.
##------------------------------------------------------------
def extract_labels_minmax (xml_filenames, image_db, m, n, output_file, filetype='chips') :
	objs_d = defaultdict(list)
	obj_filenames = load_objs_from_files (xml_filenames, objs_d, 'chips', 'source')
	df_db = get_files_info_df (obj_filenames, image_db)
	min_cnt = int (m)
	max_cnt = int (n)
	# print ('... -- reading csv:', image_db)
	df_db = pandas.read_csv (image_db, sep=';')
	df_db['MONTH'] = df_db['MONTH'].astype(int)
	# print ('... -- found', df_len (df_db), 'images')
	images = []
	labels = df_get_label_list (df_db)
	labels_selected = 0
	if max_cnt == 0 :
		print ('=== total images in file:', df_len (df_db))
	for cur_label in labels :
		# pdb.set_trace ()
		df_label = df_db_get_label (df_db, cur_label)
		label_img_cnt = df_len (df_label)
		# print ('... -- processing label:', cur_label, ':', label_img_cnt, 'images')
		if label_img_cnt < min_cnt :
			# print ('... -- Ignoring label', cur_label, 'with too few images:', label_img_cnt)
			continue
		label_minmax_images = df_label_get_n (df_label, max_cnt)
		# print ('... -- received ', len (label_minmax_images), 'images.')
		if len (label_minmax_images) > 0 :
			labels_selected += 1
		images.extend (label_minmax_images)
	# pdb.set_trace ()
	objs_selected, objs_not_selected = obj_split (objs_d, images, 'source', 'files')
	generate_xml_from_objs (objs_selected, output_file)
	print ('\nFound', labels_selected, 'labels in', len (images), 'images.')
	print ('\nWriting selected images to:', output_file)

##------------------------------------------------------------
##   given csv of images and dates, return the most number of 
##     images of count between m and n, and evenly distributed  
##	   among years, season and days.
##   if split_day_images == False, x and y are percentages (for
##     partitioning)
##------------------------------------------------------------
def partition_labels_xy (xml_filenames, image_db, x, y, output_file, filetype='chips', split_day_images=False) :
	objs_d = defaultdict(list)
	obj_filenames = load_objs_from_files (xml_filenames, objs_d, 'chips', 'source')
	df_db = get_files_info_df (obj_filenames, image_db)
	file_img_cnt = len (obj_filenames)
	x_percent = int (x)
	y_percent = int (y)
	x_file_img_cnt = int (x_percent / 100 * file_img_cnt)
	y_file_img_cnt = file_img_cnt - x_file_img_cnt
	df_db = pandas.read_csv (image_db, sep=';')
	df_db['MONTH'] = df_db['MONTH'].astype(int)
	debug = True
	if debug :
		print ('... -- found', df_len (df_db), 'images')
	images = []
	labels = df_get_label_list (df_db)
	# TODO: how to fix percent drift
	for cur_label in labels :
		# pdb.set_trace ()
		df_label = df_db_get_label (df_db, cur_label)
		label_img_cnt = df_len (df_label)
		x_label_cnt = int (x_percent / 100 * label_img_cnt)
		if debug :
			print ('... -- processing label:', cur_label, ':', label_img_cnt, 'images')
		label_images = df_label_get_n (df_label, x_label_cnt, split_day_images)
		if debug :
			print ('... -- received ', len (label_images), 'images, expected', x_label_cnt, 'images.')
		images.extend (label_images)
	# pdb.set_trace ()


	objs_selected, objs_not_selected = obj_split (objs_d, images, 'source', 'files')
	if split_day_images is False :
		print ('\nExpected', x_file_img_cnt, 'images, received', len (images), 'images')
	generate_xml_from_objs (objs_selected, output_file)
	generate_xml_from_objs (objs_not_selected, output_file+'y')
	print ('\nWriting selected images to:', output_file)

##------------------------------------------------------------
##   given csv of images and dates, print stats for each label
##------------------------------------------------------------
def print_db_stats  (df_db, filetype='chips',print_years=True, print_seasons=True, print_days=True) :
	print ('\n|-- total images in file:', df_len (df_db))
	# check for columns
	cols = ['IMAGE', 'LABEL', 'DATE', 'YEAR', 'MONTH']
	db_cols = list (df_db)
	missing_cols = []
	# pdb.set_trace ()
	for col in cols :
		if col in db_cols :
			continue
		missing_cols.append (col)
	if len (missing_cols) > 0 :
		print ('... Missing column(s) in CSV:', missing_cols)
		print ('... Aborting.\n')
		return
	df_db['MONTH'] = df_db['MONTH'].astype(int)
	labels = df_get_label_list (df_db)
	total_label_img_cnt = 0
	for cur_label in labels :
		df_label = df_db_get_label (df_db, cur_label)
		label_img_cnt = df_len (df_label)
		total_label_img_cnt += label_img_cnt
		print ('|   |-- ', cur_label, ':', label_img_cnt, '-----------------------------------------------')
		years = df_get_year_list (df_label)
		year_cnt = len (years)
		if not print_years :
			print ('|   |   |-- ', year_cnt, 'years')
		season_cnt = 0
		days_cnt = 0
		day_locs_cnt = 0
		# pdb.set_trace ()
		video_cnt = 0
		if filetype == 'video_chips' :
			dfg_videos = df_label[['IMAGE', 'VIDEO', 'DATE']].groupby (['VIDEO']).count().sort_values('IMAGE')
			video_cnt = len (dfg_videos)
		for year in years:
			df_year = df_label_get_year (df_label, year)
			if print_years :
				year_img_cnt = df_len (df_year)
				print ('|   |   |-- ', year, ':', year_img_cnt)
			df_spring = df_year_get_spring (df_year)
			spring_cnt = len (df_spring)
			if print_seasons :
				print ('|   |   |   |-- spring :', spring_cnt)
			uniq_days, uniq_day_locs = print_season_details (df_spring, print_days, '----', filetype)
			day_locs_cnt += uniq_day_locs
			days_cnt += uniq_days
			df_fall = df_year_get_fall (df_year)
			fall_cnt = len (df_fall)
			print ('|   |   |   |-- fall : ', fall_cnt)
			uniq_days, uniq_day_locs = print_season_details (df_fall, print_days, '++++', filetype)
			day_locs_cnt += uniq_day_locs
			days_cnt += uniq_days
			if spring_cnt : 
				season_cnt += 1
			if fall_cnt : 
				season_cnt += 1
		if not print_seasons :
			print ('|   |   |   |-- ', season_cnt, 'seasons')
		print ('------- ', cur_label, 'summary:', year_cnt, 'years |', season_cnt, 'seasons |', days_cnt, 'days |', day_locs_cnt, 'days-locations |', video_cnt, 'uniq videos |', label_img_cnt, 'image(s)')
		# print ('------- ', cur_label, 'summary:', year_cnt, 'years |', season_cnt, 'seasons |', days_cnt, 'days-locations |', label_img_cnt, 'total|', total_label_img_cnt)
		print ('----------------------------------------------------------------------')

##------------------------------------------------------------
##   given xmls and csv of images and dates, partitioni into x and y
##   get df of chipfiles and date
##   for each label: get years.  for each year: 
##	    partition_season (spring), partition_season (fall)
##   now: TODO partition to support video_chips using (label,date,location)
##------------------------------------------------------------
def partition_xy_with_dates (xml_filenames, image_db, x, filetype='chips', duration=24, ppath=None) :
	# pdb.set_trace ()
	objs_d = defaultdict(list)
	if filetype == 'video_chips' :
		if ppath is None:
			ppath = '/video/bears/videoFrames/britishColumbia/'
		df_db = get_video_chips_info_df (xml_filenames, image_db, objs_d, ppath)
		filename_type = 'file'
	else :
		filename_type = 'source'
		obj_filenames = load_objs_from_files (xml_filenames, objs_d, 'chips', 'source')
		if ppath is None :
			ppath = '/data/bears/'
		df_db = get_files_info_df (obj_filenames, image_db, ppath)
	file_img_cnt = len (df_db)
	x_file_img_cnt = int (x / 100 * file_img_cnt)
	y_file_img_cnt = file_img_cnt - x_file_img_cnt
	# check for columns
	cols = ['LABEL', 'DATE', 'MONTH', 'TIME']
	missing_cols = list (set (cols) - set (df_db))
	if len (missing_cols) > 0 :
		print ('... Unable to locate required column(s) in CSV:', missing_cols)
		print ('... Aborting.\n')
		return
	df_db['MONTH'] = df_db['MONTH'].astype(int)
	df_db['TIME'] = df_db['TIME'].astype(int)
	# pdb.set_trace ()
	df_db['GROUP'] = df_db['TIME'].div(10000).div(int(duration)).astype(int)
	# df_db['GROUP1'] = df_db['TIME'].div(10000)
	# df_db['GROUP2'] = df_db['GROUP1'].div(duration).astype(int)
	labels = g_get_labels ()
	x_files = []
	y_files = []
	x_unused_cnt = x_file_img_cnt
	y_unused_cnt = y_file_img_cnt
	for cur_label in labels :
		df_label = df_db_get_label (df_db, cur_label)
		years = df_get_year_list (df_label)
		for year in years:
			# pdb.set_trace ()
			df_year = df_label_get_year (df_label, year)
			df_spring = df_year_get_spring (df_year)
			if len (df_spring) > 0 :
				x, y = recalc_xy (x_unused_cnt, y_unused_cnt)
				x_partition, y_partition = partition_season_xy (df_spring, x, y, filetype)
				x_files.extend (x_partition)
				y_files.extend (y_partition)
				if get_verbosity () > 2 :
					print_partition_info (len (x_partition), len (y_partition), len (x_files), len (y_files), 'spring')
				x_unused_cnt -= len (x_partition)
				y_unused_cnt -= len (y_partition)
			df_fall = df_year_get_fall (df_year)
			if len (df_fall) > 0 :
				x, y = recalc_xy (x_unused_cnt, y_unused_cnt)
				x_partition, y_partition = partition_season_xy (df_fall, x, y, filetype)
				x_files.extend (x_partition)
				y_files.extend (y_partition)
				if get_verbosity () > 2 :
					print_partition_info (len (x_partition), len (y_partition), len (x_files), len (y_files), 'fall')
				x_unused_cnt -= len (x_partition)
				y_unused_cnt -= len (y_partition)
	# pdb.set_trace ()
	x_chunk, y_chunk = obj_split (objs_d, x_files, filename_type)
	return [x_chunk, y_chunk]

##------------------------------------------------------------
##  print partition info
##------------------------------------------------------------
def print_partition_info (x_cur_len, y_cur_len, x_len, y_len, season) :
	x_got = x_cur_len / (x_cur_len + y_cur_len)
	y_got = 1 - x_got
	x_total = x_len / (x_len + y_len)
	print (cur_label, year, season, 'x:y', x, ':', y, '--', x_len, ':', y_len, '--', "%.2f" % x_got, ':', "%.2f" % y_got, '--', "%.2f" % x_total)

##------------------------------------------------------------
##  get new ratios based on unfulfilled counts
##------------------------------------------------------------
def recalc_xy (x_unused_cnt, y_unused_cnt) :
	x = int (x_unused_cnt / (x_unused_cnt + y_unused_cnt) * 100)
	y = 100 - x
	return x, y
##------------------------------------------------------------
##  partition season.  group into chunks by date, sort largest first
##  option 1: keep largest first, then random the rest
##		 indices = list (range (1,len (dfg_groups)))
##		 random.shuffle (indices)
##		 indices.insert (0, 0)
##  option 2: leave sorted by largest first
##  method:
##    for each chunk put into x if doesn't go over goal, else
##    put in y.
##  option 1 was making test set too large.
##  currently using option 2.  
##  now: TODO partition to support video_chips (consider location)
##------------------------------------------------------------
def partition_season_xy (df_season, x, y, filetype) :
	if filetype == 'video_chips' :
		dfg_groups = df_season[['IMAGE', 'DATE', 'GROUP', 'TIME', 'LOCATION']].groupby (['DATE', 'LOCATION', 'GROUP']).count().sort_values('IMAGE', ascending=False)
	else :
		dfg_groups = df_season[['IMAGE', 'DATE']].groupby (['DATE']).count().sort_values('DATE', ascending=False)
	# df_dates_group_des = df_season[['IMAGE', 'DATE']].groupby (['DATE'], ascending=False).count().sort_values('IMAGE')
	# pdb.set_trace ()
	if len (dfg_groups) == 1 :
		images = df_get_images (df_season)
		return images, []
	# pdb.set_trace ()
	# -- keep largest, random the rest for some diversity of days.  but too
	#  many groups are going into test set. maybe change 
	slack_hyper_param = 1.05
	slack_hyper_param = 1.10
	slack_hyper_param = 1.075
	x_season_images = int (len (df_season) * (x*slack_hyper_param) / 100)
	debug = True
	debug = False
	if debug :
		print ('x:', x, '-- season images:', len (df_season), '-- date/location/time groups:', len (dfg_groups))
	x_unused_cnt = x_season_images
	x_images = []
	y_images = []
	# pdb.set_trace ()
	group_vals = dfg_groups.index.values.tolist ()
	first = True
	for group_val in group_vals :
		df_group = dfg_get_group_df (df_season, group_val)
		images = df_get_images (df_group)
		if debug :
			print ('x_unused_cnt: ', x_unused_cnt)
		if not first and (df_len (images) > x_unused_cnt) : # goes into y
			if debug :
				print ('putting group of', len (images), 'into group y')
			y_images.extend (images)
			first = False
			continue
		if debug :
			print ('putting group of', len (images), 'into group x')
		x_unused_cnt -= len (images)
		x_images.extend (images)
		first = False

	if debug :
		print ('----------------------------------------')
		print ('season x:', len (x_images), '-- season y:', len (y_images))
		print ('----------------------------------------')
	x_new = len (x_images)/len (df_season)*100
	# pdb.set_trace ()
	if x_new > x*1.1 or x_new < x*.9 :
		print ('Warning: partition result outside of expected bounds.  Expected:', x, 'achieved: ', round(x_new))
	return x_images, y_images

##------------------------------------------------------------
##  dfg_get_group_df (df, group_info)
##------------------------------------------------------------
def  dfg_get_group_df(df, group_info) :
	date = group_info[0]
	location = group_info[1]
	group = group_info[2]
	df_group = df[(df.DATE==date) & (df.LOCATION==location) & (df.GROUP==group)]
	return df_group

##------------------------------------------------------------
##  print details of images by date within season
##  if there are multiple locations, print each separately
##------------------------------------------------------------
def print_season_details (df_season, print_days, season_delim=':', filetype='chips') :
	dfg_dates_by_count = df_season[['IMAGE', 'DATE']].groupby (['DATE']).count().sort_values('IMAGE')
	date_location_count = 0
	video_timestr = ''
	is_video_chips = filetype == 'video_chips'
	if not print_days :
		print ('|   |   |   |   |-- ', date, ':', date_img_cnt[0])
		return
	for i in range (len (dfg_dates_by_count)):
		# pdb.set_trace ()
		date = dfg_dates_by_count.index[i]
		date_img_cnt = dfg_dates_by_count.iloc[i]
		df_day = df_season_get_day (df_season, date)
		video_cnt = 0
		if is_video_chips :
			# dfg_videos = df_day.groupby (['VIDEO']).count()

#----------
			video_cnt, video_timestr = df_get_video_time_info (df_day)
#----------

		if int (date) == 0 :
			print ('|   |   |   |   |-- 00000000 ', end='')
		else :
			print ('|   |   |   |   |-- ', date, end='')   
		print ( season_delim, date_img_cnt[0], 'images,', video_cnt, 'videos', end='')
		if video_cnt > 1 :
			print (video_timestr)
		else :
			print ()
		# pdb.set_trace ()
		if not is_video_chips :
			continue
		locations = df_get_location_list (df_day)
		if len (locations) > 1 :
			for location in locations :
				df_location = df_day_get_location (df_day, location)
				df_get_video_time_info ()
				print ('|   |   |   |   |   |-- ', location, season_delim, len (df_location))
				print_videos (df_location)
			date_location_count += len (locations)
		else :
			print_videos (df_day)
			date_location_count += 1
	return len (dfg_dates_by_count), date_location_count

##------------------------------------------------------------
##------------------------------------------------------------
def df_get_video_time_info (df) :
	videos = df_get_video_list (df)
	video_cnt = len (videos)
	if video_cnt > 1 :
		video_timestr = df_day_get_videos_timestr (df, videos)
	return video_cnt, video_times_str

##------------------------------------------------------------
##  print videos
##------------------------------------------------------------
def print_videos (df) :
	if get_verbosity () < 4 :
		return
	dfg_videos = df.groupby (['VIDEO']).count()
	videos = dfg_videos.index.values.tolist ()
	for video in videos :
		# pdb.set_trace ()
		df_video_images = df_get_video_images (df, video)
		vname = video.split ('/')[-1]
		print ('|   |   |   |   |   |   |-- ', vname, ':', len (df_video_images), 'images')
	return

##------------------------------------------------------------
##  partition_hier_obj ()
##   - get years, divide among count.  if any year has too few, 
##  unfinished::
##------------------------------------------------------------
def partition_hier_obj (hier_obj_d, x, y) :
	return 0


##------------------------------------------------------------
##  partition chips into x and y percent
##  will do one of:
##	- put all of a label into one of two parts
##	- split each label into parts , not using dates
##	- split across all labels afer grouping images by specified duration
##  returns two lists of objects
##------------------------------------------------------------
def partition_objs (filenames, x, y, filetype="chips", split_type="chips", split_arg=24, db=None) :
	if get_verbosity () > 1 :
		print ('loading files:', filenames)
		print ("partitioning chips into: ", x, " ", y)
		print ('split type:', split_type)
	chunks = []
	objs_d = defaultdict(list)
	if split_type == 'label' :
		chunks = partition_files_by_label (filenames, x, y, filetype)
		return chunks
	if split_type == 'grouping_duration' : ##  
		chunks = partition_xy_with_dates (filenames, db, x, filetype, split_arg)
		return chunks
	# only here if doing rndom partitioning (no grouping by day)
	chip_files = load_objs_from_files (filenames, objs_d, filetype)
	# pdb.set_trace ()
	chunks_x = []
	chunks_y = []
	chip_cnt = 0
	for label, chips in list(objs_d.items()):
		# remove chips below size minimum
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
def generate_xml_from_objs (obj_list, filename, filetype="chips") :
	root, objs = create_new_tree_w_element (filetype)
	for obj in obj_list :
		objs.append (obj)

	indent (root)
	tree_x = ET.ElementTree (root)
	tree_x.write (filename, encoding='ISO-8859-1')
	# print("\nGenerated xml file: \n\t", filename, "\n")

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
	ET.SubElement (r, 'cwd').text = os.getcwd ()
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
	tree_i = ET.parse (xml_file_in)
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
def get_dirs_images (filenames, exts=['.jpg', '.jpeg', '.png']):
	imgs = []
	# print ('getting images for : ', filenames)
	for filename in filenames :
		if filename[0]=='.' :
			continue
		for ext in exts:
			if filename.lower().endswith (ext.lower()) :
				imgs.append (filename)
				break
	return imgs

##------------------------------------------------------------
##  get_video_chips_info_df:
##  from vdb, save into dictionary by chipname, get
##      list of chip files and video files. Clean video path,
##  	merge with csv info
##  return df with chipfile, location, date, datetime, month, label, video
##  now: TODO check on parent_path
##------------------------------------------------------------
def get_video_chips_info_df (filenames, vdb, vdb_d, parent_path='/data/videos/') :
	chip_filenames, video_filenames, locations, datetimes, labels = \
		load_video_chips_from_files (filenames, vdb_d)
	df_chips = pandas.DataFrame ()
	df_chips['CHIPFILE'] = chip_filenames
	df_chips['LOCATION'] = locations
	# pdb.set_trace ()
	# get date and month
	if vdb :
		df_chips['IMAGE'] = video_filenames
		df_all = pandas.read_csv (vdb, sep=';')
		# get table from list of images
		df_chips_info = pandas.merge (df_all, df_chips, on=['IMAGE'], how='inner')
		df_chips_info['DATE'] = df_chips_info['DATE'].astype(str)
		df_chips_info['TIME'] = df_chips_info['TIME'].astype(str)
		df_chips_info['DATETIME'] = df_chips_info['DATE'].astype(str) + ' ' + df_chips_info['TIME'].astype(str)
		dates = df_chips_info['DATE'].values.tolist ()
		df_chips_info.rename(columns = {'IMAGE':'VIDEO', 'CHIPFILE':'IMAGE'}, inplace = True)

		#----------------
		num_empty = dates.count('00000000')
		if num_empty > 0 :
			print ('Warning:', num_empty, 'empty dates for', len (df_chips_info), 'chips')
		return df_chips_info
	else : ## no db, use dateTime info from chip tag
		# num_empty = datetimes.count('00000000 000000')
		dates = [dt.split()[0] for dt in datetimes]
		times = [dt.split()[1] for dt in datetimes]
		months = [date[4:6] for date in dates]
		years = [date[0:4] for date in dates]
		videos = ['/'.join (name.split('/')[:-1]) for name in chip_filenames]
		df_chips['YEAR'] = years
		df_chips['LABEL'] = labels
		df_chips['MONTH'] = months
		df_chips['DATE'] = dates
		df_chips['TIME'] = times
		df_chips['DATETIME'] = datetimes
		df_chips['VIDEO'] = videos
		dates = df_chips['DATE'].values.tolist ()
		df_chips.rename(columns = {'CHIPFILE':'IMAGE'}, inplace = True)
		num_empty = dates.count('00000000')
		if num_empty > 0 :
			print ('Warning:', num_empty, 'empty dates for', len (df_chips), 'chips')
		return df_chips
	# df_chips = pandas.DataFrame (chip_video_pairs, columns=['CHIPFILES', 'FILENAMES'])

##------------------------------------------------------------
##  load objs from list of files into vdb_d (via load_video_chips_objs)
##  vdb_d is dictionary of <chip_filename><element>
##  ex:  d["Glendale_2018/Glendale25/D03/IMG_0058.MP4"] = <Element 'chip' at 0x12003
##       d["Glendale_2019/Glendale01/D23/IMG_1111.MP4"] = <Element 'chip' at 0x03420
##  returns chip_filenames, video_filename, locations, datetimes, labels
##------------------------------------------------------------
def load_video_chips_from_files (filenames, vchips_d) :
	all_chip_filenames = []
	all_video_filenames = []
	all_locations = []
	all_datetimes = []
	all_labels = []
	for file in filenames:
		# pdb.set_trace()
		root, tree = load_file (file)
		chip_filenames, video_filenames, locations, datetimes, labels =  \
			load_video_chip_objs (root, vchips_d)
		all_chip_filenames.extend (chip_filenames)
		all_video_filenames.extend (video_filenames)
		all_locations.extend (locations)
		all_datetimes.extend (datetimes)
		all_labels.extend (labels)
	# pdb.set_trace()
	return all_chip_filenames, all_video_filenames, all_locations, all_datetimes, all_labels

##------------------------------------------------------------
##  load objs from list of files into objs_d
##    if filename is directory, load all its xml files
##  objs_d is dictionary of <string><element_list>
##  ex:  d["b-032"] = ["<Element 'chip' at 0x123,..,<Element 'chip' at 0x43]
##       d["b-747"] = ["<Element 'chip' at 0x987,..,<Element 'chip' at 0x65]
##  return list of files in metadata
##------------------------------------------------------------
def load_objs_from_files (filenames, objs_d, filetype="chips", filename_type='file'):
	objfiles = []
	# print "in load_objs_from_files"
	## load all chips into objs_d
	# print("\nLoading", filetype, "for files: ")
	for file in filenames:
		print("\nLoading ", file)
		# pdb.set_trace()
		root, tree = load_file (file)
		obj_filenames = load_objs (root, objs_d, filetype, filename_type)
		objfiles.extend (obj_filenames)
	# pdb.set_trace()
	return objfiles

##------------------------------------------------------------
##  hier load objs from list of files into objs_d
##    if filename is directory, load all its xml files
##  objs_d is dictionary of <string><element_list>
##  ex:  d["b-032"] = ["<Element 'chip' at 0x123,..,<Element 'chip' at 0x43]
##       d["b-747"] = ["<Element 'chip' at 0x987,..,<Element 'chip' at 0x65]
##  return list of files in metadata
##------------------------------------------------------------
def hier_load_objs_from_files (filenames, hier_objs_d, filetype="chips", filename_type='file'):
	objfiles = []
	# print "in hier_load_objs_from_files"
	## load all chips into objs_d
	# print("\nLoading", filetype, "for files: ")
	for file in filenames:
		print("\nLoading ", file)
		# pdb.set_trace()
		root, tree = load_file (file)
		obj_filenames = hier_load_objs (root, hier_objs_d, filetype, filename_type)
		objfiles.extend (obj_filenames)
	# pdb.set_trace()
	return objfiles

##------------------------------------------------------------
## tag_get_unpathed_filename (tag)
##------------------------------------------------------------
def tag_get_unpathed_filename (tag) :
	image_file = tag.attrib.get ('file')
	fnames = os.path.split (image_file)
	base = fnames[1]
	path = fnames[0]
	return base

##------------------------------------------------------------
##  given df of one label, return n images spread across years,
##  seasons and dates
##------------------------------------------------------------
def df_label_get_n (df_label, n_images, split_day_images=True) :
	years = df_get_year_list (df_label)
	# print ('.... -- searching for', n_images, 'images across', len (years), 'years.')
	images = []
	label_img_cnt = df_len (df_label)
	if label_img_cnt < n_images :
		# print ('.... -- Return max images:', label_img_cnt)
		images = df_get_images (df_label) # return all images for label.  df -> image list -> objs
		return images
	unused = n_images
	years_len = []
	df_year_d = {}
	# make list of [year,#image] and sort by #image
	#  years with less than quota will allow extras 
	#  to be used in years with more images
	year_num_images = []
	# pdb.set_trace ()
	for year in years:
		df_year = df_label_get_year (df_label, year)
		df_year_d[year] = df_year
		year_num_images.append ([year, len (df_year)])
	# sorted_e = sorted(e_dist_d.items(), key=lambda x: x[1])
	year_num_images.sort(key = lambda x: x[1])
	for i in range (len (years)) : 
		images_per_year = int (unused / (len (years) - i))
		if images_per_year == 0 :
			continue
		year = year_num_images[i][0]
		year_img_cnt = year_num_images[i][1]
		df_year = df_year_d[year]
		if year == 0 :
			year = 'Undated'
		year_images = df_year_get_n (df_year, images_per_year)
		# print ('.... -- found for year', year, ': ', len (year_images), 'images' )
		unused -= len (year_images)
		# pdb.set_trace ()
		images.extend (year_images)
	# print ('.... -- found for all years: ', len (images), '. Unused: ', unused)
	return images

##------------------------------------------------------------
##  given df of one label_year, return n images spread across
##  seasons and dates
##------------------------------------------------------------
def df_year_get_n (df_year, n_images) :
	# print ('...... -- searching for', n_images, 'images a year')
	year_img_cnt = df_len (df_year)
	if year_img_cnt <= n_images : # use all for year
		# print ('...... -- returning max images: ', year_img_cnt)
		year_images = df_get_images (df_year)
		return year_images
	images_per_season = int (n_images / df_year_get_season_cnt (df_year))
	unused = n_images
	spring_cnt = df_year_get_spring_count (df_year)
	fall_cnt = df_year_get_fall_count (df_year)
	images = []
	# pdb.set_trace ()
	if spring_cnt < fall_cnt :
		if spring_cnt > 0 and images_per_season > 0 :
			df_spring = df_year_get_spring (df_year)
			print ('-------- looking for', images_per_season, 'among', len (df_spring), 'spring images')
			spring_images = df_season_get_n (df_spring, images_per_season)
			images.extend (spring_images)
			# print ('..... -- spring: ', len (spring_images), 'images' )
			unused -= len (spring_images)
		df_fall = df_year_get_fall (df_year)
		print ('-------- looking for', images_per_season, 'among', len (df_fall), 'fall images')
		images_per_season = unused  # grab any extra from previous season
		fall_images = df_season_get_n (df_fall, images_per_season)
		images.extend (fall_images)
		# print ('..... -- fall: ', len (fall_images), 'images' )
		unused -= len (fall_images)
	else :
		if fall_cnt > 0 and images_per_season > 0 :
			df_fall = df_year_get_fall (df_year)
			fall_images = df_season_get_n (df_fall, images_per_season)
			images.extend (fall_images)
			# print ('..... -- fall: ', len (fall_images), 'images' )
			unused -= len (fall_images)
		images_per_season = unused  # grab any extra from previous season
		df_spring = df_year_get_spring (df_year)
		spring_images = df_season_get_n (df_spring, images_per_season)
		images.extend (spring_images)
		# print ('..... -- spring: ', len (spring_images), 'images' )
		unused -= len (spring_images)
	# if unused != 0 and n_images != 0 :
		# print ('... -- error:', unused, 'images missing.')
	return images

##------------------------------------------------------------
##  given df of one label_year, return n images spread across
##  seasons and dates
##------------------------------------------------------------
def df_season_get_n (df_season, n_images) :
	# print ('....... -- searching for', n_images, 'season images')
	season_img_cnt = df_len (df_season)
	if season_img_cnt <= n_images : # use all for season
		# print ('...... -- returning max images: ', season_img_cnt)
		season_images = df_get_images (df_season)
		return season_images
	images = []
	unused = n_images
	# pdb.set_trace ()
	# df_dates_by_count = df_season.groupby (['DATE']).count ().sort_values (by='c')
	df_dates_by_count = df_season[['IMAGE', 'DATE']].groupby (['DATE']).count().sort_values('IMAGE')
	for i in range (len (df_dates_by_count)):
		date = df_dates_by_count.index[i]
		date_img_cnt = df_dates_by_count.iloc[i]
		images_per_day = int (unused / (len (df_dates_by_count) - i))
		if images_per_day == 0 :
			continue
		df_day = df_season_get_day (df_season, date)
		day_images = df_day_get_n (df_day, images_per_day)
		# print ('....... -- date ', date, ': ', len (day_images), 'images' )
		unused -= len (day_images)
		images.extend (day_images)
	if unused != 0 and n_images != 0 :
		print ('... error:', unused, 'images missing from season.')
	return images

##------------------------------------------------------------
##  given df of one day, return n random images 
##------------------------------------------------------------
def df_day_get_n (df_day, n_images) :
	# pdb.set_trace ()
	day_image_cnt = df_len (df_day)
	if day_image_cnt <= n_images :
		day_images = df_get_images (df_day)
		return day_images
	indices = random.sample(range(1, day_image_cnt), n_images)
	images = []
	for i in indices :
		image = df_day.iloc[i]['IMAGE']
		images.append (image)
	return images

##------------------------------------------------------------
#  given df, return list of all images
#   df['column name'].values.tolist()
##------------------------------------------------------------
def df_get_images (df) :
	# pdb.set_trace ()
	images_list = df['IMAGE'].values.tolist ()
	return images_list

##------------------------------------------------------------
#  given all images, return list of labels
#    lables = df_all.groupby (['label']).size ()
##------------------------------------------------------------
def df_get_label_list (df_all) :
	df_labels = df_all.groupby (['LABEL']).size ()
	labels = []
	for i in range (len (df_labels)) :
		label = df_labels.index[i]
		labels.append (label)
	return labels

##------------------------------------------------------------
##------------------------------------------------------------
def df_day_get_videos_timestr (df_day, videos) :
	times = []
	for video in videos :
		df_video_images = df_get_video_images (df_day, video)
		if len (df_video_images) > 0 :
			time = df_video_images.iloc[0]['TIME']
			time_str = time[-6:-4] + ':' + time[-4:-2]
			times.append (time_str)
			# pdb.set_trace ()
	times_str = '(' + ' '.join(times) + ')'
	return times_str

##------------------------------------------------------------
#  given df , return list of videos
#  videos = = df.groupby (['VIDEO']).size ()
##------------------------------------------------------------
def df_get_video_list (df_db) :
	videos = []
	dfg_videos = df_db[['VIDEO', 'IMAGE']].groupby (['VIDEO']).count().sort_values('IMAGE')
	videos = dfg_videos.index.values.tolist()
	return videos
		
##------------------------------------------------------------
#  given df for label, return list of years
#  years = df_label.groupby (['year']).size ()
##------------------------------------------------------------
def df_get_year_list (df_label) :
	dfg_years = df_label.groupby (['YEAR']).size ()
	years = dfg_years.index.values.tolist()
	return years
		
##------------------------------------------------------------
#  given df for day for label, return list of locations
#  locations = df_day.groupby (['LOCATION']).size ()
	# dates = df_db['DATE'].values.tolist ()
	# videos = df_videos.index.values.tolist()
##------------------------------------------------------------
def df_get_location_list (df_day) :
	dfg_locations = df_day.groupby (['LOCATION']).size ()
	locations = dfg_locations.index.values.tolist()
	return locations
		
##------------------------------------------------------------
#  given db, return images for label
#	db_df.query ('label == "bf_000")
##------------------------------------------------------------
def df_db_get_label (df_all, label) :
	df_label = df_all[df_all.LABEL == label]
	return df_label

##------------------------------------------------------------
#  given db_label, return df for year
#	db_df.query ('year == "2020")
##------------------------------------------------------------
def df_label_get_year (df_label, year) :
	df_year = df_label[df_label.YEAR == year]
	return df_year

##------------------------------------------------------------
##  given df for year, return df of images in fall
##  fall is August and later
##------------------------------------------------------------
def df_get_video_images (df_db, video) :
	df_video_images = df_db[df_db.VIDEO == video].sort_values('IMAGE')
	return df_video_images

##------------------------------------------------------------
##  given df for year, return df of images in fall
##  fall is August and later
##------------------------------------------------------------
def df_year_get_fall (df_year) :
	# df_fall = df_year.query ('MONTH > 7')
	df_fall = df_year[df_year.MONTH > 7]
	return df_fall

##------------------------------------------------------------
##  given df for year, return df of images in spring
##  spring is July and earlier
##------------------------------------------------------------
def df_year_get_spring (df_year) :
	df_spring = df_year.query ('MONTH < 8')
	return df_spring

##------------------------------------------------------------
#  given db_seaon, return df for day 
#	db_df.query ('day == "20201010")
##------------------------------------------------------------
def df_season_get_day (df_season, image_date) :
	df_day = df_season[df_season.DATE == image_date]
	return df_day

##------------------------------------------------------------
#  given db_seaon, return df for day 
#	db_df.query ('day == "20201010")
##------------------------------------------------------------
def df_season_get_day_location (df_season, image_date, location) :
	df_day = df_season[df_season.DATE == image_date &
		df_season.LOCATION == location]
	return df_day_location

##------------------------------------------------------------
#  given db_day, return df for location
#	db_df.query ('day == "20201010")
##------------------------------------------------------------
def df_day_get_location (df_day, location) :
	df_location = df_day[df_day.LOCATION == location]
	return df_location

##------------------------------------------------------------
#  given df, return count
#	len (df_label)
##------------------------------------------------------------
def df_len (df) :
	return len (df)

##------------------------------------------------------------
##  given df for year, return number of images in fall
##  fall is August and later
##------------------------------------------------------------
def df_year_get_fall_count (df_year) :
	df_fall = df_year_get_fall (df_year)
	return len (df_fall)

##------------------------------------------------------------
##  given df for year, return number of images in spring
##  spring is July and earlier
##------------------------------------------------------------
def df_year_get_spring_count (df_year) :
	df_spring = df_year_get_spring (df_year)
	return len (df_spring)

##------------------------------------------------------------
##  get count of seasons for given df
##------------------------------------------------------------
def df_year_get_season_cnt (df_year) :
	season_cnt = 0
	if df_year_get_fall_count (df_year) > 1 :
		season_cnt += 1
	if df_year_get_spring_count (df_year) > 1 :
		season_cnt += 1
	return season_cnt

##------------------------------------------------------------
##------------------------------------------------------------


##------------------------------------------------------------
## hier_objs_len () return image count for matching years, seasons
##  labels and days.  empty list denotes all.
##------------------------------------------------------------
def hier_objs_len (hier_obj_d, labels, years, seasons, days) :
	count = 0
	for label, year_obj_d in sorted (list (hier_obj_d.items ())) :
		if len (labels) > 0 and label not in labels :
			# print ('skipping label:', label)
			continue
		for year, season_obj_d in sorted (list (year_obj_d.items ())) :
			if len (years) > 0 and year not in years :
				# print ('skipping year:', year)
				continue
			for season, day_obj_d in list (season_obj_d.items ()) :
				if len (seasons) > 0 and season not in seasons :
					# print ('skipping season:', season)
					continue
				for day, objs in sorted (list (day_obj_d.items ())) :
					if len (days) > 0 and day not in days :
						# print ('skipping day:', day)
						continue
					obj_count = len (objs)
					# print ('adding ', obj_count, 'for ', label, 'for day ', day)
					count += len (objs)
	return count

##------------------------------------------------------------
##  print content of hier_obj_d
##------------------------------------------------------------
def hier_objs_print (hier_obj_d, filetype='chips'):
	# for label, tags in list(objs_d.items ()) :
	# image_file = chip_tag.attrib.get ('file')
	# imgfile_base, imgfile_ext = os.path.splitext (image_file)
		# fnames = os.path.split (path)
		# base = fnames[1]
		# path = fnames[0]
	for label, year_obj_d in sorted (list (hier_obj_d.items ())) :
		print ('------ label: ', label)
		for year, season_obj_d in sorted (list (year_obj_d.items ())) :
			print ('-- year: ', year)
			for season, date_obj_d in list (season_obj_d.items ()) :
				print ('---- season: ', season)
				for date, objs in sorted (list (date_obj_d.items ())) :
					print ('-------- date: ', date)
					for obj in objs :
						filename = tag_get_unpathed_filename (obj)
						print ('---------- file :', filename)

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
# def get_face_stats (objs_d, verbose=1, filetype='chips'):
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
	if get_verbosity () > 1 :
		print('------------------------')
		print('--- matched stats:--- ')
		print('------------------------')
		for i in sorted (set (all_labels)):
			print(i, '\t,\t', matched_labels.count (i))
	print('------------------------')
	print('  matched pairs: ', len (matched_labels))

	if get_verbosity () > 1 :
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
	print ('# images: ', len (img_files))
	mpo_file = []
	for i in range (len (img_files)) : 	# all labels
		img = Image.open (img_files[i])
		imgs_d [img.format] += 1
		# if img.format == 'MPO' :
			# mpo_file.append (img_files[i])
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
	print ('\nmin image : ', min_img_file)
	print ('resolution: ', min_img.width, min_img.height)
	print ('min size  : ', min_size)
	print ('max image : ', max_img_file)
	print ('resolution: ', max_img.width, max_img.height)
	print ('max size  : ', max_size)

	for img_format, count in imgs_d.items () :  ## iterate through all chips
		print (img_format, ' : ', count)
	# print ('\n\t MPO : ', mpo_file)
	return

##------------------------------------------------------------
##  get stats for xml
##------------------------------------------------------------
def get_obj_stats (filenames, filename_type='source', image_db=None, parent_path=None, print_files=False, filetype="chips", write_stats=False, print_all=False):
	# pdb.set_trace ()
	objs_d = defaultdict(list)
	if filetype == 'video_chips' :
		parent_path = '/video/bears/videoFrames/britishColumbia/'
		df_db = get_video_chips_info_df (filenames, image_db, objs_d, parent_path)
		# print_video_stats (filenames, image_db, \
		# '/video/bears/videoFrames/britishColumbia/', print_all)
	else :
		objfiles = load_objs_from_files (filenames, objs_d, filetype, 'source')
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
	if get_verbosity () > 1:
		for key, objs in all_objs :
			print (key, ':', len (objs))
	if print_all :
		for label in sorted (set (all_labels)):
			if get_verbosity () > 2 or len (objs_d[label]) > 0 :
				print(label, '	:', len (objs_d[label]))
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
		print(' average', filetype, 'per bear :', "%.2f" % (obj_count / len (chips_count_list)))
		print('  median', filetype, 'per bear :', np.median (img_cnt_per_label))
	# combos = sum ([(n*(n-1)/2) for n in img_cnt_per_label if n > 1])
	# print('  possible matched sets :', combos)
	# print('possible unmatched sets :', u_combos)
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

		# else :
			# print('\n  ***  unable to show histogram: no access to display.  *** \n')

	if get_verbosity () > 2 :
		if not image_db and filetype != 'video_chips' :
			return
		if filetype != 'video_chips' :
			df_db = get_files_info_df (objfiles, image_db, parent_path, filetype)
		# pdb.set_trace ()
		print_db_stats (df_db, filetype)
		
	if filetype == 'faces':
		print_faces_stats (write_stats)
	if print_files :
		objfiles.sort ()
		for objfile in objfiles:
			print('\t', objfile)

##------------------------------------------------------------
##------------------------------------------------------------
def get_csv_stats (db_csv_filename, separator=';') :
	df_db = pandas.read_csv (db_csv_filename, sep=separator)
	print_db_stats (df_db)

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
#  get_YMDT_from_dateTime_str - returns year, month, day and time from string
#     that looks something like: "2014:10:13 13:57:50"
##------------------------------------------------------------
def get_YMDT_from_dateTime_str (image_datetime) :
	# pdb.set_trace ()
	if image_datetime is None:
		return 0, 0, 0, 0
	image_year = image_datetime[:4]
	image_month = image_datetime[5:7]
	image_day = image_datetime[8:10]
	image_time = image_datetime[11:13] + image_datetime[14:16] + image_datetime[17:19]
	return image_year, image_month, image_day, image_time

##------------------------------------------------------------
##------------------------------------------------------------
def image_find_creation_datetime_str (image_file):
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
##  get an alternate image using specified string substitution
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
##  trim path n directories from top level
##  e.g.   /a/b/c/d/e/f/g.ext, 4 -> e/f/g.ext
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
##  leave path with n directories from basename
##  e.g.   /a/b/c/d/e/f/g.ext, 1 -> f/g.ext
##------------------------------------------------------------
def trim_path_end (pathname, dir_depth) :
	path = pathname
	newpath = os.path.basename (path)
	for i in range (dir_depth) :
		path = os.path.dirname (path)
		cur_dir = os.path.basename (path)
		newpath = cur_dir + '/' + newpath
	# pdb.set_trace ()
	return newpath

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
##  return new name using base of file and new postfix
##------------------------------------------------------------
def make_new_name (filename, postfix) :
	basename, ext = os.path.splitext(filename)
	out_file = basename + postfix + ext
	return out_file

##------------------------------------------------------------
##  for given image tag, return string of video creation datetime
##------------------------------------------------------------
def imgtag_find_video_creation_datetime_str (image_tag, vchips_d):
	# pdb.set_trace () 
	image_file = image_tag.attrib.get ('file')

	##  TODO: need to fix filepath
	image_creation_date_str = vchips_d[image_file]

	pdb.set_trace () 
	# FIX: change hard code of directories to original image
	if image_creation_date_str is '' :
		orig_image_file = get_orig_img_by_name (image_file, 'imageSourceSmall', 'imageSource')
		image_creation_date_str = image_find_creation_datetime_str (orig_image_file)
	return image_creation_date_str

##------------------------------------------------------------
##  for given image tag, return string of date of image
##------------------------------------------------------------
def imgtag_find_creation_datetime_str (image_tag):
	# pdb.set_trace () 
	image_file = image_tag.attrib.get ('file')
	image_creation_date_str = image_find_creation_datetime_str (image_file)
	# pdb.set_trace () 
	# FIX: change hard code of directories to original image
	if image_creation_date_str is '' :
		orig_image_file = get_orig_img_by_name (image_file, 'imageSourceSmall', 'imageSource')
		image_creation_date_str = image_find_creation_datetime_str (orig_image_file)
	return image_creation_date_str

##------------------------------------------------------------
##  remove source tag from chips
##------------------------------------------------------------
def remove_chip_source (filename, outfile) :
	if outfile is None :
		outfile = make_new_name (filename, '_nosource')
	# pdb.set_trace()
	root, tree = load_file (filename)
	for chip in root.findall ('./chips/chip') :
		source_tag = chip.find ('source')
		chip.remove (source_tag)
	tree.write (outfile, encoding='ISO-8859-1');
	print ('\nRemoved source tags. New xml file written to:', outfile, '\n')

##------------------------------------------------------------
##  add date str to imgtag
##------------------------------------------------------------
def tag_add_datetime_str (image_tag, dateTime):
	datetime_tag = ET.SubElement (image_tag, 'dateTime')
	datetime_tag.text = dateTime;

##------------------------------------------------------------
##  datetime_empty_inc 
##------------------------------------------------------------
def datetime_empty_inc():
    try:
        datetime_empty_inc.count += 1
    except AttributeError:
        datetime_empty_inc.count = 1

##------------------------------------------------------------
##  get date str of tag
##------------------------------------------------------------
def tag_get_datetime_str (tag, filetype):
	# pdb.set_trace ()
	if filetype in ['chips', 'video_chips'] :
		src_tag = get_chip_source_tag (tag)
		if src_tag :
			tag = src_tag
	datetime_tag = tag.find ('dateTime')
	if datetime_tag is None :
		if filetype == 'video_chips' :
			return '00000000 000000'
		else :
			return '0000:00:00 00:00:00'
	return datetime_tag.text
	# image_year, image_month, image_day, image_time = get_YMDT_from_dateTime_str (image_datetime)

##------------------------------------------------------------
##  add obj to dict by year, season, label, date
##------------------------------------------------------------
def hier_add_obj (hier_objs_d, obj, label, datetime_str) :
	# z = defaultdict (lambda: defaultdict(lambda: defaultdict(list)))
	# z = defaultdict (lambda: defaultdict(list))
	year, month, day, time = get_YMDT_from_dateTime_str (datetime_str)
	if int (month) < 8 :
		season = 'spring'
	elif int (month) == 0 :
		season = 'none'
	else :
		season = 'fall'
	# pdb.set_trace ()
	date = year + month + day
	if len (hier_objs_d[label][year][season][date]) == 0 :
		hier_objs_d[label][year][season][date] = [obj]
	else :
		# pdb.set_trace ()
		hier_objs_d[label][year][season][date].append (obj)
	return
	
##------------------------------------------------------------
##------------------------------------------------------------

##------------------------------------------------------------
##  return string with content:
##    	file, label, date, size, photo_source,
##		nose_xy, nose_source_file, orig_image, permission?, age
##------------------------------------------------------------
def gen_image_csv_str (image_tag):
	# pdb.set_trace () 
	image_label = get_obj_label_text (image_tag)
	image_file = image_tag.attrib.get ('file')
	image_creation_date_str = image_find_creation_datetime_str (image_file)
	image_year, image_month, image_day, image_time = get_YMDT_from_dateTime_str (image_creation_date_str)
	photo_source = get_photo_source (image_file)
	image_size = get_image_size (image_file)
	face_size = get_face_size (image_tag)
	image_date = image_year + image_month + image_day
	if get_verbosity () > 1 :
		print ('file   : ', image_file)
		print ('label  : ', image_label)
		print ('date   : ', image_creation_date_str)
		print ('source : ', photo_source)
		print ('size   : ', image_size)
		print('-----------------------------')
	csv_str = trim_path_start (image_file, 5)
	csv_str += ';' + image_label
	csv_str += ';' + str (image_date)
	csv_str += ';' + str (image_year)
	csv_str += ';' + str (image_month)
	csv_str += ';' + str (image_day)
	csv_str += ';' + str (image_time)
	csv_str += ';' + str (image_size)
	csv_str += ';' + trim_path_start (photo_source, 5)
	csv_str += ';' + str (face_size)
	csv_header = 'IMAGE;LABEL;DATE;YEAR;MONTH;DAY;TIME;SIZE;PHOTO_SOURCE;FACE_SIZE'
	return csv_str, csv_header

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
	csv_header = 'IMAGE;PREDICT;TRUTH_LABEL;MATCH'
	return csv_str, csv_header

##------------------------------------------------------------
##  return string with content:
##    	file, label, size,
##		nose_xy, orig_image
##------------------------------------------------------------
def gen_chip_csv_str (chip_tag):
	image_file = chip_tag.attrib.get ('file')
	image_label = get_obj_label_text (chip_tag)
	image_size = get_image_size (image_file)
	orig_file = get_chip_source_file (chip_tag)
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
	csv_header = 'IMAGE;LABEL;SIZE;ORIG_IMAGE;NOSE_XY;NOSE_X;NOSE_Y'
	return csv_str, csv_header

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
	csv_header = 'IMAGE;LABEL;SIZE_RESIZED;ORIG_IMAGE;FACE_SIZE_RESIZED'
	return csv_str, csv_header

##------------------------------------------------------------
##  write csv file of image info containing:
##    filename, label, date, location??, source (level above label)
##------------------------------------------------------------
def write_image_info_csv (filenames, outfile, filetype):
	objs_d = defaultdict(list)
	objtype = filetype
	# pdb.set_trace ()
	if objtype == 'derived_faces' or objtype == 'svm':
		objtype = 'faces'
	objfiles = load_objs_from_files (filenames, objs_d, objtype)

	csv_fp = open (outfile, "w")

	# images, derived_image: images/image
	# chips: chips/chip
	# pdb.set_trace ()
	header = ''
	first = True
	for label, tags in list(objs_d.items ()) :
		for tag in tags:
			# pdb.set_trace ()
			if filetype == 'faces' :
				image_csv, csv_header = gen_image_csv_str (tag)
			elif filetype == 'derived_faces' :
				image_csv, csv_header = gen_derived_image_csv_str (tag)
			elif filetype == 'chips' :
				image_csv, csv_header = gen_chip_csv_str (tag)
			elif filetype == 'svm' :
				image_csv, csv_header = gen_svm_csv_str (tag)
			if first :
				csv_fp.write (csv_header + '\n')
				first = False
			csv_fp.write (image_csv + '\n')
	csv_fp.close ()
	print("... generated file:", outfile)
	if len (csv_header) :
		print("... header: ", csv_header)

##------------------------------------------------------------
##  add image date time to video chip and source
##------------------------------------------------------------
def add_video_chip_datetime (filenames, vdb, parent_path, outfile):
	vchips_d = defaultdict (list)
	df_chips_info = get_video_chips_info_df (filenames, vdb, vchips_d, parent_path)
	pdb.set_trace ()
	df_image_datetime = df_chips_info[['IMAGE','DATETIME']]
	image_datetime_list = df_image_datetime.values.tolist ()
	# [[chipfile1, '20200202 091213'], ...  [chipfileN, '20190202 184300']] 
	chip_tags = []
	for image_datetime in image_datetime_list :
		chip_filename = image_datetime[0]
		datetime_str = image_datetime[1]
		chip_tag = g_vchipnames_d[chip_filename]
		video_tag = get_chip_source_tag (chip_tag)
		tag_add_datetime_str (chip_tag, datetime_str)
		tag_add_datetime_str (video_tag, datetime_str)
		chip_tags.append (chip_tag)
	write_xml_file (outfile, chip_tags, 'chips')
	print ('New chip file with datetime written to: ', outfile)

##------------------------------------------------------------
##  add image date time to source/image tag
##------------------------------------------------------------
def add_object_datetime (filenames, filetype, outfile, parent_path, vdb=None):
	objs_d = defaultdict(list)
	objtype = filetype
	# pdb.set_trace ()
	if objtype == 'derived_faces' or objtype == 'svm':
		objtype = 'faces'
	if objtype == 'video_chips':
		if vdb is None:
			print ('Error: vdb not available, aborting.')
			return
		add_video_chip_datetime (filenames, vdb, parent_path, outfile)
		return
	objfiles = load_objs_from_files (filenames, objs_d, objtype)
	objs = []
	out_xml_file = make_new_name (filenames[0], "_datetime")
	for label, tags in list(objs_d.items ()) :
		for tag in tags:
			# pdb.set_trace ()
			if filetype == 'faces' :
				image_tag = tag
			elif filetype == 'chips' :
				image_tag = get_chip_source_tag (tag)
			if filetype == 'video_chips' :
				datetime_str = imgtag_find_video_creation_datetime_str (image_tag, vdb_d)
			else :
				datetime_str = imgtag_find_creation_datetime_str (image_tag)
			# pdb.set_trace ()
			tag_add_datetime_str (image_tag, datetime_str)
			objs.append (tag)
	write_xml_file (out_xml_file, objs, filetype)
	print("... added datetime data to :", out_xml_file)

##------------------------------------------------------------
## write html of bear info: image, label/name, date, and dataset
##	 color coded for train (green) vs test (red)
##   expects 4 columns: image, label, date, dataset
##
#    <hr style="width:50%">beatrice 2020<br>
# resulting string for each image:
# <img src="/home/data/bears/imageSource/britishColumbia/melanie_20170828/bc_beatrice/IMG_5056.JPG"
#    width"200" height="300" style="border:5px solid green;" alt="beatrice" >
##------------------------------------------------------------
def html_image_info_from_csv (csv_file, html_outfile, delim=';') :
	with open (csv_file) as csv_file:
		csv_reader = csv.reader (csv_file, delimiter=delim)
		##   expects 4 columns: image, label, date, dataset
		# TODO: open file for writing
		html_fp = open (html_outfile, "w")
		label = ''
		date = ''
		for row in csv_reader:
			# pdb.set_trace ()
			new_label = row[1]
			new_date = row[2]
			border_color = 'green' if row[3] == 'train' else 'red'
			if new_label != label or new_date != date :
				label = new_label
				date = new_date
				html_fp.write ('<hr style="width:50%">' + new_label + ' ' + new_date + ' <br>\n')
			img_tag = '<img src="/home/data/bears/' + row[0] + '" '
			img_tag += 'style="border:5px solid ' + border_color + '; max-width:250px; max-height:250px;" alt="' + label + '" >\n'
			html_fp.write (img_tag)
		html_fp.close ()
		print ("... wrote html to file: ", html_outfile)
	
##------------------------------------------------------------
## write html of embedding and its correct matched 
##	 color coded for train vs test
##  format: label;distance; 
##			date1;time1; date2;time2; 
##			image1;image2; chip1;chip2;
##			match
##
# breaks between matches: 
#    <hr style="width:50%">beatrice 2020<br>
# resulting string for each image:
# <img src="/home/data/bears/imageSource/britishColumbia/melanie_20170828/bc_beatrice/IMG_5056.JPG"
#    width"200" height="300" style="border:5px solid green;" alt="beatrice" >
##------------------------------------------------------------
def html_matched_image_info_from_csv (csv_file, html_outfile, delim=';') :
	with open (csv_file) as csv_file:
		csv_reader = csv.reader (csv_file, delimiter=delim)
		##  format: label;distance; 
		##			date1;time1; date2;time2; 
		##			image1;image2; chip1;chip2
		html_fp = open (html_outfile, "w")
		for row in csv_reader:
			# pdb.set_trace ()
			label = row[0]
			distance = row[1]
			date1 = row[2]
			time1 = row[3]
			date2 = row[4]
			time2 = row[5]
			image1 = row[6]
			image2 = row[7]
			chip1 = row[8]
			chip2 = row[9]
			datematch = row[10]
			border_color = 'green'
			if int (datematch) == 1 :
				border_color = 'red'
			img_close = 'style="border:5px solid ' + border_color + '; max-width:250px; max-height:250px;" alt="' + label + '" >\n'

			html_fp.write ('<hr style="width:50%">' + label + '&emsp; &emsp;' + distance + ' <br>\n')
			html_fp.write ('<hr style="width:50%">' 
				+ date1 + ':' + time1 + '&emsp; &emsp;'
				+ date2 + ':' + time2 + ' <br>\n')
			img_tag = '<img src="' + image1 + '" ' + img_close
			img_tag += '<img src="' + image2 + '" ' + img_close
			img_tag += '<img src="' + chip1 + '" ' + img_close
			img_tag += '<img src="' + chip2 + '" ' + img_close
			html_fp.write (img_tag)
		html_fp.close ()
		print ("... wrote html to file: ", html_outfile)
	
##------------------------------------------------------------
## write html of images in file
##
# resulting string for each image:
# <img src="/home/data/bears/imageSource/britishColumbia/melanie_20170828/bc_beatrice/IMG_5056.JPG"
#    width"200" height="300" style="border:5px solid green;" alt="beatrice" >
##------------------------------------------------------------
def html_images (text_file, html_outfile) :
	html_fp = open (html_outfile, "w")
	with open (text_file) as fp:
		img_files = fp.readlines ()
		border_color = 'green'
		for img_file in img_files:
			if not img_file.strip() :
				continue
			img_tag = '<img src="' + img_file.strip () + '" '
			img_tag += 'style="border:5px solid ' + border_color + '; max-width:250px; max-height:250px;" >\n'
			html_fp.write (img_tag)
	html_fp.close ()
	print ("... wrote html to file: ", html_outfile)
		
##------------------------------------------------------------
##  cur_datetime - returns YYYYMMDDHHMM
##------------------------------------------------------------
def current_datetime () :
	return datetime.datetime.now().strftime("%Y%m%d%H%M")

##------------------------------------------------------------
##
##------------------------------------------------------------
def print_faces_stats (write_unused_images) :
	print("-----------------------------")
	print("....# files with no faces      : ", len (g_stats_zero))
	print("....# files with multiple faces: ", len (g_stats_many))
	# pdb.set_trace ()
	if write_unused_images:
		if len (g_stats_zero) :
			stats_name = datetime.datetime.now().strftime("stats_zero_%Y%m%d_%H%M")
			stats_fp = open (stats_name, "w")
			for face in g_stats_zero:
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
def get_img_files (filenames, abs_path=True) :
	# pdb.set_trace ()
	# print ('getting images for', filenames)
	img_files = []
	pathed_dirs = []
	for filename in filenames :
		if abs_path :
			filename = os.path.abspath (filename)
		for root, dirs, files in os.walk (filename) :
			pathed_dirs = [os.path.join (root, dir) for dir in dirs]
			get_img_files (pathed_dirs)
			matched_imgs = get_dirs_images (files)
			pathed_imgs = [os.path.join (root, img) for img in matched_imgs]
			# pdb.set_trace ()
			img_files.extend (pathed_imgs)
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
	filename1 = obj_get_filename (image1)
	filename2 = obj_get_filename (image2)
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
##  given chip tag, return source tag
##------------------------------------------------------------
def get_chip_source_tag (chip_tag) :
	# pdb.set_trace ()
	source_tag = chip_tag.find ('source')
	return source_tag

##------------------------------------------------------------
##  given chip tag, return name of source file.  if video_chip
##  truncate filename and use middle 4 directories
##------------------------------------------------------------
def get_chip_source_file (chip_tag, filetype='chips') :
	# pdb.set_trace ()
	source_tag = get_chip_source_tag (chip_tag)
	if source_tag is None:
		if filetype == 'video_chips' :
			chip_filename = obj_get_filename (chip_tag)
			dirs = chip_filename.split('/')
			new_name = dirs[-5:-1]
			new_path = '/'.join (new_name)
			return new_path
		else :
			return  ''
	source_file = source_tag.attrib.get ('file')
	if filetype == 'video_chips' : # need to clean 
		dirs = source_file.split('/')
		new_name = dirs[-5:-1]
		new_path = '/'.join (new_name)
		return new_path
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
##  return file for xml tag
##------------------------------------------------------------
def obj_get_filename (xml_tag) :
	filename = xml_tag.attrib.get ('file')
	return filename

##------------------------------------------------------------
##  return label for xml tag
##------------------------------------------------------------
def obj_get_label_text (xml_tag) :
	return get_obj_label_text (xml_tag)

##------------------------------------------------------------
##  remove image_tag from dict
##------------------------------------------------------------
def remove_image_tag (image_file, images_d) :
	for l , image_tags in list(images_d.items ()) :
		# ignores label, which is only accurate during testing
		# look for file name
		for i in range (len (image_tags)) :
			image_file_2 = obj_get_filename (image_tags[i])
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
			image_filename = obj_get_filename (image1)
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

	one_only_filename = 'images_one_only.xml'
	two_only_filename = 'images_two_only.xml'
	mismatch_filename = 'images_mismatch.xml'

	write_xml_file (one_only_filename, images_one_only, filetype)
	write_xml_file (two_only_filename, images_two_only, filetype)
	write_xml_file (mismatch_filename, images_mismatch, filetype)
	print ("writing files:")
	print ("\t", one_only_filename)
	print ("\t", two_only_filename)
	print ("\t", mismatch_filename)

##------------------------------------------------------------
##  xml_to_list - return list of files from xml
##------------------------------------------------------------
def xml_to_list (xml_file, filetype='faces') :
	xml_obj_d = default_dict (list)
	img_files = load_objs_from_files (xml_file, xml_obj_d, filetype)
	return img_files

##------------------------------------------------------------
##  find_files_from_patterns - return list of all matched files (not obj)
##     using pattern from str_list.  
##	NOTE: pattern will match substring of filename, not only full strings
##	   e.g.  pattern bc_n will match bc_neana and bc_no-tail
##	   TODO: can expand to use regex.
##------------------------------------------------------------
def find_files_from_patterns (filenames, patterns, filetype='faces') :
	matched  = []
	for filename in filenames :
		for string in patterns:
			# import re
			# match = re.search (string, filename)
			# if match :
			if string.lower () in filename.lower () :
				matched.append (string)
	return matched

##------------------------------------------------------------
#	given xmls, write out filenames for all objects
##------------------------------------------------------------
def xml_to_files (xml_files, outfile, filetype, filename_type='file') :
	objs_d = defaultdict(list)
	# pdb.set_trace ()
	source_filenames = load_objs_from_files (xml_files, objs_d, filetype, filename_type)
	if not outfile :
		return source_filenames
	outfile_fp = open (outfile, "w")
	for filename in source_filenames :
		outfile_fp.write (filename + '\n')
	outfile_fp.close ()
	return source_filenames

##------------------------------------------------------------
##  xml_split_by_years - write xml file for each year
##------------------------------------------------------------
def	xml_split_by_years (filenames, years, outfile, filetype='faces') :
	# pdb.set_trace ()
	year_d = defaultdict (list)
	year_start = int (years[0])
	year_end = int (years[1])
	year_range = range (year_start, year_end)
	all_years = [str (year) for year in year_range]
	for filename in filenames:
		root, tree = load_file (filename)
		for chip in root.findall ('./chips/chip'):
			filename = chip.attrib.get ('file')
			# print ('filename', filename)
			matched = False
			for year in all_years :
				if year in filename :
					year_d[year].append (chip)
					# print ('matched year:', year)
					matched = True
					break
			if not matched :
				# print ('no year matched, storing under 0000')
				year_d['0000'].append (chip)
		# write to files
	all_years.append ('0000')
	for year in all_years :
		if len (year_d[year]) == 0 :
			continue
		year_filename = make_new_name (outfile, year)
		write_xml_file (year_filename, year_d[year], filetype)
		print(len (year_d[year]), filetype, 'from',  year, 'written to :', year_filename)

##------------------------------------------------------------
##  xml_split_by_files - write matched and unmatched
##     xml files given file of strings for matching 
##------------------------------------------------------------
def	xml_split_by_files (xml_files, split_file, outfile, filetype='faces', type_split='files', multi_ok=True) :
	objs_d = defaultdict(list)
	set_multi_ok (multi_ok)
	source_filenames = load_objs_from_files (xml_files, objs_d, filetype)
	# pdb.set_trace ()
	with open (split_file, 'r') as fp:
		filenames_raw = fp.readlines ()
	filenames = [filename.strip() for filename in filenames_raw]
	filename_type = 'file'
	if filetype == 'chips' :
		filename_type = 'source'
	matched_objs, unmatched_objs = obj_split (objs_d, filenames, filename_type, type_split)
	matched_filename = outfile + '_matched' + '.xml'
	unmatched_filename = outfile + '_unmatched' + '.xml'
	many_filename = outfile + '_multi' + '.xml'
	zero_filename = outfile + '_zero' + '.xml'
	write_xml_file (matched_filename, matched_objs, filetype)
	write_xml_file (unmatched_filename, unmatched_objs, filetype)
	write_xml_file (many_filename, g_objs_many , filetype)
	write_xml_file (zero_filename, g_objs_zero, filetype)
	print('unmatched', filetype, 'written to :', unmatched_filename)
	print('  matched', filetype, 'written to :', matched_filename)
	print('     many', filetype, 'written to :', many_filename)
	print('     zero', filetype, 'written to :', zero_filename)


##------------------------------------------------------------
##  xml_split_by_patterns - write matched and unmatched
##     xml files given file of patterns for matching 
##------------------------------------------------------------
def	xml_split_by_patterns (xml_files, pattern_file, outfile, filetype='chips') :
	objs_d = defaultdict(list)
	source_filenames = load_objs_from_files (xml_files, objs_d, filetype)
	# pdb.set_trace ()
	with open (pattern_file, 'r') as fp:
		filenames_raw = fp.readlines ()
	patterns = [filename.strip() for filename in filenames_raw]
	filename_type = 'file'
	if filetype == 'chips' :
		filename_type = 'source'
	matched_objs, unmatched_objs = obj_split (objs_d, patterns, filename_type, 'patterns')
	matched_filename = outfile + '_matched' + '.xml'
	unmatched_filename = outfile + '_unmatched' + '.xml'
	write_xml_file (matched_filename, matched_objs, filetype)
	write_xml_file (unmatched_filename, unmatched_objs, filetype)
	print('unmatched', filetype, 'written to :', unmatched_filename)
	print('  matched', filetype, 'written to :', matched_filename)

##------------------------------------------------------------
##  xml_split_by_xml - write matched and unmatched
##     	xml given xml file for matching.  filetype of two
##  	input xml must be the same.
##------------------------------------------------------------
def	xml_split_by_xml (xml_file, split_xml_file, outfile, filetype='faces', type_split='files') :
	objs_d = defaultdict(list)
	split_filenames = load_objs_from_files (split_xml_file, objs_d, filetype)
	xml_split_by_files (xml_file, split_filenames, outfile, filetype, type_split)

##------------------------------------------------------------
##  print stats of video_chips
##------------------------------------------------------------
def	print_video_stats (filenames, image_db, parent_path, print_all) :
	pdb.set_trace ()
	objs_d = defaultdict(list)
	df_db = get_video_chips_info_df (filenames, image_db, objs_d, parent_path)
	verbosity = get_verbosity ()
	img_cnt_per_label = []
	for cur_label in g_get_labels () :
		df_label = df_db_get_label (df_db, cur_label)
		label_cnt = len (df_label)
		img_cnt_per_label.append (label_cnt)
		if verbosity > 1 :
			print (cur_label, ':', label_cnt)
	num_vchip = len (df_db)
	num_label = len (g_get_labels ())
	print('-----------------------------')
	print('           total vchips :', num_vchip)
	print('                # bears :', num_label)
	if num_vchip > 0:
		print(' average vchips per bear :', num_vchip / num_label)
		print('  median vchips per bear :', np.median (img_cnt_per_label))
	if image_db or get_verbosity () > 2 :
		# add year for stats
		dates = df_db['DATE'].values.tolist ()
		years = [date[0:4] for date in dates]
		df_db['YEAR'] = years
		print_db_stats (df_db, 'video_chips')

##------------------------------------------------------------
##  split_filename_dicts - return list of matched and unmatched
##     video_chips given chipnames
##  return matched_objs, unmatched_objs
##------------------------------------------------------------
def	split_filename_dicts (objs_d, filehames) :
	matched_objs = []
	matched_objs = []
	unmatched_objs = []
	# pdb.set_trace ()
	for filename in filenames :
		matched_objs.append (objs_d[filename])
		del objs_d[filename]
	return matched_objs, objs_d.values ()

##------------------------------------------------------------
##  obj_split - return list of matched and unmatched
##     objs given type_split.
##  if filename_type == 'source', get the source filename
##		obj to compare against list
##	only matches full strings when spliting by files
##    matches substring when split by pattern.  e.g. pattern '_chip_0'
##    will matching all filenames that contains '_chip_0' like
##    '/data/images/chips/IMG_0001_chip_0'
##  expect dict as keyed by label
##  split_label_dicts - return list of matched and unmatched
##------------------------------------------------------------
def obj_split (objs_d, split_arg, filename_type='file', type_split='files', fix_path=True) :
	matched_objs = []
	unmatched_objs = []
	common_path = 'imageSourceSmall'
	common_path = 'imageSource'
	# pdb.set_trace ()
	if type_split == 'labels' :
		labels = split_arg
		for label, objs in list(objs_d.items ()) :  ## iterate through objs
			if label in labels :
				matched_objs.extend (objs)
			else :
				unmatched_objs.extend (objs)
	elif type_split == 'files':
		filenames = split_arg.copy ()
		for label, objs in list(objs_d.items ()) :  ## iterate through objs
			for obj in objs :
				filename = get_filename (obj, filename_type)
				if common_path and filename.startswith (common_path) :
					filename = filename[len(common_name):]
				if filename in filenames :
					matched_objs.append (obj)
					filenames.remove (filename)
				else :
					unmatched_objs.append (obj)
		if len (filenames) > 0 :

			print ('Warning: splitting by names encountered', len (filenames), 'unmatched files.  Printing first few: ')
			print ('not all files were matched.', len (filenames), 'unmatched files:')
			for filename in filenames[:5]:
				print ('\t', filename)

	## ---------------  need to test ------------
	## TODO: implement pattern match
	elif type_split == 'patterns' :
		# pdb.set_trace ()
		patterns = split_arg
		for label, objs in list(objs_d.items ()) :  ## iterate through objs
			for obj in objs :
				# pdb.set_trace ()
				filename = get_filename (obj, filename_type)
				matched = False
				for pattern in patterns :
					if pattern in filename :
						matched_objs.append (obj)
						matched = True
						break
				if not matched :
					unmatched_objs.append (obj)
		print ('patterns matched   :', len (matched_objs))
		print ('patterns unmatched :', len (unmatched_objs))
	else:
		print ('Error: Unimplemented split option:',  type_split)
	if len (matched_objs) != len (split_arg) and type_split == 'files' :
		print ('Warning: splitting of objects had count of ', type_split, 'is: ', len (filenames), ', but found: ', len (matched_objs))
	return matched_objs, unmatched_objs

##------------------------------------------------------------
##  split_objs_by_filenames - return list of matched and unmatched objs
##	only matches full strings when spliting by files
##------------------------------------------------------------
def	split_objs_by_filenames (objs_d, obj_filenames, common_path=None) :
	matched_objs = []
	unmatched_objs = []
	filenames = obj_filenames.copy ()
	for label, objs in list(objs_d.items ()) :  ## iterate through objs
		for obj in objs :
			filename = get_filename (obj)
			if filename in filenames :
				matched_objs.append (obj)
				filenames.remove (filename)
			else :
				unmatched_objs.append (obj)
	if len (filenames) > 0 :
		print ('Warning: Splitting by file did not match', len (filenames), 'out of the requested', len (obj_filenames), 'filenames.')
		print ('First few unmatched files:')
		for filename in filenames[:5] :
			print ('\t', filename)
	return matched_objs, unmatched_objs

##------------------------------------------------------------
##------------------------------------------------------------
def get_filename (obj, filename_type='file') :
	if filename_type == 'source' :
		obj_filename = get_chip_source_file (obj)
	else :
		obj_filename = obj_get_filename (obj)
	return obj_filename
##------------------------------------------------------------
##  
##  
##  
##------------------------------------------------------------

##------------------------------------------------------------
##  xml_split_by_list  -- same as xml_split_by_files
##------------------------------------------------------------
def xml_split_by_list (xml_filenames, images_file, output_file, filetype='chips') :
	objs_d = defaultdict(list)
	obj_filenames = load_objs_from_files (xml_filenames, objs_d, 'chips', 'source')
	with open (split_file, 'r') as fp:
		images_raw = fp.readlines ()
		images = [filename.strip() for filename in images_raw]
		objs_selected, objs_not_selected = obj_split (objs_d, images, 'source', 'files')
		generate_xml_from_objs (objs_selected, output_file)
		print ('writing objects from images to:', output_file)

##------------------------------------------------------------
##  update_path - create file of same list of images with new data
##------------------------------------------------------------
def update_path (orig_file, new_files, output_file, filetype='faces') :
	faces_orig_d = defaultdict(list)
	faces_new_d = defaultdict(list)
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
#  given list of tf detections in result, extract count of labels for each detection
#	return list of detection count
#-------------------------------------------------------------------------------
def get_obj_count (result, image_np, min_score, labels, do_display=False) :
	have_display = "DISPLAY" in os.environ
	display = have_display and do_display
	dim = image_np.shape
	if display :
		fig,ax = plt.subplots(1)
		ax.imshow(image_np)
	result_cnt = len (result.json()['predictions'])
	matched_detects = []
	for j in range (result_cnt) :
		boxes = result.json()['predictions'][j]['detection_boxes']
		scores = result.json()['predictions'][j]['detection_scores']
		classes = result.json()['predictions'][j]['detection_classes']
		detections = int(result.json()['predictions'][j]['num_detections'])
		obj_cnt = 0
		# pdb.set_trace ()
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
		matched_detects.append (obj_cnt)
		if (display) :
			plt.show()
	return matched_detects

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def img_find_bears (img_file, min_score, labels) :
	image = Image.open(img_file)
	image_np = np.array(image)
	payload = {"instances": [image_np.tolist()]}
	result = requests.post("http://localhost:8080/v1/models/default:predict", json=payload)
	bear_cnts = get_obj_count (result, image_np, min_score, labels, True)
	return bear_cnts

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def imgs_find_bears (img_files, min_score, labels) :
	img_list = []
	for img_file in img_files :
		image = Image.open(img_file)
		image_np = np.array(image)
		img_list.append (image_np.tolist ())
	payload = {"instances": img_list}
	result = requests.post("http://localhost:8080/v1/models/default:predict", json=payload)
	# pdb.set_trace ()
	bear_cnts = get_obj_count (result, image_np, min_score, labels, True)
	return bear_cnts

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def do_find_bears (filename, out_file, min_score, model) :
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

	with open (filename, 'r') as fp:
		img_files = fp.readlines ()
		for img_file in img_files :
			print ('counting bears for ', img_file)
			bear_cnts = img_find_bears (img_file.strip(), min_score, labels)
			bear_cnt = bear_cnts[0]
			# pdb.set_trace ()
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

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def do_find_bears_batch (filename, out_file, min_score, model) :
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
	out_fp0 = open (out_file+'_b_0', "w")
	out_fp1 = open (out_file+'_b_1', "w")
	out_fpmulti = open (out_file+'_b_multi', "w")
	expected_cnt = 1

	with open (filename, 'r') as fp:
		img_files_raw = fp.readlines ()
		img_files = [filename.strip() for filename in img_files_raw]
		bear_cnts = imgs_find_bears (img_files, min_score, labels)
		i = 0
		for img_file in img_files :
			# bear_cnt = img_find_bears (img_file.strip(), min_score, labels)
			# pdb.set_trace ()
			print ('counting bears for ', img_file)
			bear_cnt = bear_cnts[i]
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
			i += 1
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
			# 	if label.text == 'bc_also' or label.text == 'bc_amber' or label.text == 'bc_beatrice' or label.text == 'bc_bella' or label.text == 'bc_flora' or label.text == 'bc_frank' or label.text == 'bc_gc' or label.text == 'bc_hoeya' or label.text == 'bc_kwatse' or label.text == 'bc_lenore' or label.text == 'bc_lillian' or label.text == 'bc_lucky' or label.text == 'bc_river' or label.text == 'bc_steve' or label.text == 'bc_toffee' or label.text == 'bc_topaz' :
			#		bc1_embeds.append (embedding)
			#	else :
			#		bc_embeds.append (embedding)
			if label in bc_labels :
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
def split_objects_by_locales (filenames, output_file, filetype="chips") :
	bc_objs = []
	bf_objs = []
	unknown_objs = []

	objs_d = defaultdict(list)
	objfiles = load_objs_from_files (filenames, objs_d, filetype, 'source')
	# pdb.set_trace ()
	print('')
	for label, objs in list(objs_d.items ()) :
		if label[:3] == 'bc_' : # bc bear
			bc_objs.extend (objs)
		elif label[:3] == 'bf_' : # brooks bear
			bf_objs.extend (objs)
		else :
			unknown_objs.extend (objs)
	# write out bear counts
	print ('\t... # all     bears: ', len (objfiles))
	print ('\t... # bc      bears: ', len (bc_objs))
	print ('\t... # bf      bears: ', len (bf_objs))
	print ('\t... # unknown bears: ', len (unknown_objs))
	# pdb.set_trace ()
	# for locale in [] :

	t_root, t_objs = create_new_tree_w_element (filetype)
	for obj in bc_objs :
		t_objs.append (obj)
	tree = ET.ElementTree (t_root)
	t_name = output_file + '_bc.xml'
	indent (t_root)
	tree.write (t_name)
	print ('wrote bc', filetype, 'file :' , t_name)

	t_root, t_objs = create_new_tree_w_element (filetype)
	for obj in bf_objs :
		t_objs.append (obj)
	tree = ET.ElementTree (t_root)
	t_name = output_file + '_bf.xml'
	indent (t_root)
	tree.write (t_name)
	print ('wrote bf', filetype, 'file :' , t_name)

##------------------------------------------------------------
##  split faces by count (0, 1, multi)
##------------------------------------------------------------
def split_faces_by_count (input_files, output_root) :
	zeros = []
	ones = []
	multis = []
	xml_files = generate_xml_file_list (input_files)
	print ('\nextracting faces from file: ')
	for x_file in xml_files:
		print("\t", x_file)
		# pdb.set_trace()
		root, tree = load_file (x_file)
		# separate out face(box) counts 
		for image in root.findall ('images/image'):
			boxes = image.findall ('box')
			# pdb.set_trace ()
			if len (boxes) == 0 :
				zeros.append (image)
			elif len (boxes) == 1 :
				ones.append (image)
			else :
				multis.append (image)
	# write out bc bears
	print ('\t... # zero faces    : ', len (zeros))
	print ('\t... # single face   : ', len (ones))
	print ('\t... # multiple faces: ', len (multis))
	# pdb.set_trace ()
	t_root, t_images = create_new_tree_w_element ("images")
	for i in range (len (zeros)) :
		image = zeros[i]
		t_images.append (image)
	tree = ET.ElementTree (t_root)
	t_name = output_root + '_0.xml'
	indent (t_root)
	tree.write (t_name)
	print ('------- wrote zero detects to   :', t_name)

	t_root, t_images = create_new_tree_w_element ("images")
	for i in range (len (ones)) :
		image = ones[i]
		t_images.append (image)
	tree = ET.ElementTree (t_root)
	t_name = output_root + '_1.xml'
	indent (t_root)
	tree.write (t_name)
	print ('------- wrote single detects to :', t_name)

	t_root, t_images = create_new_tree_w_element ("images")
	for i in range (len (multis)) :
		image = multis[i]
		t_images.append (image)
	tree = ET.ElementTree (t_root)
	t_name = output_root + '_multi.xml'
	indent (t_root)
	tree.write (t_name)
	print ('------- wrote multi detects to  :', t_name)

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
