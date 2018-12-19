###########################
#  TODO : create run comand here
###########################
def get_test_cmd () :
	test_program = '~/dev/bearproj/bearid/build_debug/bearface'
	weights_file = '~/dev/bearproj/bearid/test/weights/mmod_dog_hipsterizer.dat'
	input_file = '~/tmp/imgList.xml'
	cmd = test_program + ' ' + weights_file + ' ' + input_file + ' > test_out.txt\n'
	return cmd

