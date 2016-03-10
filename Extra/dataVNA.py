#### exec(open('testvna.py').read())

import faulthandler
faulthandler.enable()


def test_class():

	import VNA
	import logSetup
	logSetup.initLogging()

	DEVICE_IP = '192.168.1.193'
	DEVICE_IPPort = 1234
	vna = VNA.VNA(DEVICE_IP, DEVICE_IPPort)
	print(vna)

	[hoprate, attenuation, freq_N, freq_f] = vna.set_config(VNA.HOP_45K, VNA.ATTEN_0, freq=[1000, 2000, 1024])
	print("freq_N", freq_N)
	print("freq_f", freq_f)

	started, currstate = vna.setup_start()


	paths = [ VNA.PATH_T1R1, VNA.PATH_T1R2, VNA.PATH_T2R1, VNA.PATH_T2R2 ] # measure all paths

	## Read data
	prompt = lambda key='<enter>': 'Press '+key+' to continue...:'

	while 1:
		[measure_check, return_values] = vna.measure_uncal(paths)
		print(return_values)


if __name__ == "__main__":
	test_class()
	# test_raw()
