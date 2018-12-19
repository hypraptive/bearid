#! /usr/bin/python

import os.path
import sys
import regression as re

###################
#   env check     #
###################
# if os.environ.get('DISPLAY') is None:
# 	print "\nNo display available, try again in a different environment.\n"
# 	sys.exit (0)

#######################
#    run testcase     #
#  something like this :  ../build_debug/bearface weights/mmod_dog_hipsterizer.dat ~/tmp/imgList.xml
#######################

print "running test ... "
test_cmd = re.get_test_cmd ()
print '\t' + test_cmd
os.system (test_cmd)

########################
#   validation         #
########################

######  set up #####################
goldc_dir = "gold-c"
golde_dir = "gold-e"
lint_exe = "xmllint --format --exc-c14n "
unpath_chips = '//home/mary/dev/bearproj/bearid/tools/unpath_chips.py -a '
gold_contents = os.listdir (goldc_dir)
gold_exists = os.listdir (golde_dir)
c_errs = 0
e_errs = 0
pass_msg = "\n\n----------------    test PASSED    ---------------- \n"
fail_msg = "\n\n---------------     test FAILED    ---------------- \n"
err_msg = "\n\n------------------\nerrors with file(s)\n------------------ \n"

#########  validate content ########
print '\n--- verifying content of files:' 
print '-------------------------------' 
for g_file in gold_contents:
	print g_file, ": ", 
	xml_lint_file = g_file + "_lint"
	xml_lint_g_file = g_file + "_lint_g"
	xml_lint_unpathed_file = xml_lint_file + "_unpathed"
	xml_lint_unpathed_g_file = xml_lint_g_file + "_unpathed"
	xml_diff_file = "xml_lint_unpathed_diff"
	xmllint_cmd = lint_exe + " " + g_file + " > " + xml_lint_file
	xmllint_cmd_g = lint_exe + " " + goldc_dir + "/" + g_file + " > " + xml_lint_g_file
	# looks something like: "xmllint --format --exc-c14n fileX > fileX_lint"
	# print xmllint_cmd
	# looks something like: "xmllint --format --exc-c14n gold-c/fileX > fileX_lint_g"
	# print xmllint_cmd_g
	os.system (xmllint_cmd)
	os.system (xmllint_cmd_g)
	# remove paths 
	unpath_cmd = unpath_chips + xml_lint_file
	unpath_cmd_g = unpath_chips + xml_lint_g_file
	os.system (unpath_cmd)
	os.system (unpath_cmd_g)

	diff_cmd = "diff " + xml_lint_unpathed_file + " " + xml_lint_unpathed_g_file + " > " + xml_diff_file
	# should look like: "diff xml_lint_file xml_lint_g_file > xml_lint_diff
	# print diff_cmd
	different = os.system (diff_cmd)
	if (different) :
		print " ---different---!!"
		c_errs += 1
		err_msg += g_file + " --- different\n"
	else :
		print ' matched!'
print ''

#########  verify existence of files  ########
if len (gold_exists) :
	print '--- verifying existence of ' + len (gold_exists) + ' files:' 
	print '-----------------------------------' 
	for g_file in gold_exists:
		print g_file,
		if os.path.isfile(g_file):
			print ": found"
		else:
			print ": ---- missing ----"
			e_errs += 1
			err_msg += g_file + " --- missing\n"
else :
	print '\nno files under gold-e, skipping. '

if c_errs+e_errs > 0 :
	print err_msg, "\n"
	print fail_msg, "\n"
else:
	print pass_msg, "\n"
