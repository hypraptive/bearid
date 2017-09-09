#! /usr/bin/python

import sys
import argparse
import datetime
import pdb
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

##------------------------------------------------------------
##  can be called with:
##    plot_loss <loss_file>
##------------------------------------------------------------
def main (argv) :
	parser = argparse.ArgumentParser(description='\nPlot loss versus setps.\n \t example: plot_loss train.txt',
		formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=50))
    # parser.formatter.max_help_position = 50
	parser.add_argument ('file')
	args = parser.parse_args()
	# print "ls : ", args.ls
	# print "files: ", args.files

	count = 0
	step = []
	loss = []
	loss_file = open(args.file, "r")
	for line in loss_file:
		if line.startswith('Step'):
			##print line
			cols = line.split()
			##print (cols[1], cols[3])
			step.append(cols[1])
			loss.append(cols[3])
			count += 1
		#if count==1000:
			#break;

	plt.plot(step, loss)
	plt.xlabel('Step')
	plt.ylabel('Loss')
	plt.show()

if __name__ == "__main__":
	main (sys.argv)
