#! /usr/bin/python

import csv
import sys
import argparse
import xml_utils as u
import datetime
import pdb
from collections import defaultdict


##------------------------------------------------------------
##  write_images
##------------------------------------------------------------
def write_images (images_d, filename) :
	images_fp = open (filename, "w")
	images_fp.write ("<html>\n<body>")
	images_fp.write ("<comment generated by cvs_result_matrix " + u.get_argv() + ">\n")

	for label1, content1 in sorted (images_d.items ()) :
		for label2, content2 in content1.items () :
			for i in range (len (content2)/3) :
				image1 = content2[i*3]
				image2 = content2[i*3+1]
				dist = content2[i*3+2]

				images_fp.write (label1 + " &nbsp;&nbsp; --- ----- --- &nbsp;&nbsp; " + label2 )
				images_fp.write (' &nbsp;&nbsp; --- distance = &nbsp;&nbsp;' + dist + '<br>\n')
				images_fp.write ('<img src="' + image1 + '"><img src="' + image2 + '"><br>\n')
	images_fp.write ("</html>\n</body>")
	images_fp.close ()

##------------------------------------------------------------
##  print matrix - matrix_d is a defaultdict (defaultdict (list))
##    key = label. value = dict of labels, whose value is
##    l1, l2, result, expected result
##  print matrix of alls_labels x all_labels populated with accuracy
##------------------------------------------------------------
def write_matrix (matrix_d, filename) :
	right = 1
	wrong = 0
	labels = []
	matrix_fp = open (filename, "w")
	for label1, l1_content in matrix_d.items() :
		labels.append (label1)
		for label2, l2_content in l1_content.items() :
			labels.append (label2)
	labels_set = set (labels)
	uniq_labels = sorted (list (labels_set))

	matrix_fp.write (' ,')
	for label in uniq_labels :   # write column labels
		matrix_fp.write (label + ',')
	matrix_fp.write ('\n')
	for label1 in uniq_labels :
		matrix_fp.write (label1 + ',')  # row label
		for label2 in uniq_labels :
			if len (matrix_d[label1][label2]) :
				result = matrix_d[label1][label2]
				accuracy = float (result[right]) / float (result[right]+result[wrong])
				accuracy_str = "%1.3f, " % (accuracy)
				matrix_fp.write (accuracy_str)
			else :
				matrix_fp.write ('  ,')
		matrix_fp.write ('\n')
		

##------------------------------------------------------------
##  generate matrix (defaultdict (defaultdict(list)) from list of:
##		label1, label1, result, expected_result, chip1, chip2, distance, max_distance
##------------------------------------------------------------
def gen_matrix (files) :
	right = 1
	wrong = 0
	results = defaultdict (lambda: defaultdict (list))
	images_true_pos = defaultdict (lambda: defaultdict (list))
	images_true_neg = defaultdict (lambda: defaultdict (list))
	images_false_pos = defaultdict (lambda: defaultdict (list))
	images_false_neg = defaultdict (lambda: defaultdict (list))
	for filename in files:
			## with open(file,newline='') as csvfile:
			with open(filename) as csvfile :
				fileContent = csv.reader(csvfile, delimiter=',', quotechar='|')
				# pdb.set_trace ()
				for row in fileContent:
					label1 = row[0]
					label2 = row[1]
					returnValue = row[2]
					expectedValue = row[3]
					image1 = row[4]
					image2 = row[5]
					dist = row[6]
					# pdb.set_trace ()
					if len (results[label1][label2]) == 0 :
						results[label1][label2].append (0)
						results[label1][label2].append (0)
					result = results[label1][label2]
					# pdb.set_trace ()
					if returnValue == expectedValue :  # correct -> true
						result[right] += 1
						if returnValue == '1' : # guessed positive
							images_true_pos[label1][label2].append (image1)
							images_true_pos[label1][label2].append (image2)
							images_true_pos[label1][label2].append (dist)
						else :  # guessed negative
							images_true_neg[label1][label2].append (image1)
							images_true_neg[label1][label2].append (image2)
							images_true_neg[label1][label2].append (dist)
					else: 	# incorrect -> false
						result[wrong] += 1
						if returnValue == '1' : # guessed positive
							images_false_pos[label1][label2].append (image1)
							images_false_pos[label1][label2].append (image2)
							images_false_pos[label1][label2].append (dist)
						else :  # guessed negative
							images_false_neg[label1][label2].append (image1)
							images_false_neg[label1][label2].append (image2)
							images_false_neg[label1][label2].append (dist)
	write_matrix (results, "result_matrix.csv")
	write_images (images_true_pos, "true_pos.html")
	write_images (images_true_neg, "true_neg.html")
	write_images (images_false_pos, "false_pos.html")
	write_images (images_false_neg, "false_neg.html")


##------------------------------------------------------------
##  xml_chip_face_stats *.xml dirs
##    average point of all noses, eye1_x, eye1_y, eye2_x, eye2_y, eye_dist
##
##   
##------------------------------------------------------------
def main (argv) :
	parser = argparse.ArgumentParser(description='\nGenerate matrix of test results.',
		formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=50))
	parser.add_argument ('files', nargs='+')
		# help="increase output verbosity"
	args = parser.parse_args()
	gen_matrix (args.files)

if __name__ == "__main__":
	main (sys.argv)

