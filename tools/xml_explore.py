import json
import sys
import xml.etree.cElementTree as ET
import pdb
import random
import logging
import xml.dom.minidom
import argparse
from xml.dom import minidom
from copy import deepcopy
from collections import namedtuple

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
					print image.text + " has existing label of " + curLabel.text
					continue
				label = ET.SubElement (box, 'label')
				# pdb.set_trace ()
				label.text = label_str;
				label_count += 1
				# print "added label"
	return label_count

#---------------------------------------------------------------------------
#  load file, return root
#---------------------------------------------------------------------------
def load_file (file):
	tree = ET.parse (file)
	root = tree.getroot()
	return root, tree
	
