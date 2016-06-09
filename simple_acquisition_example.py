#### exec(open('testvna.py').read())

import pprint


def test_class():

	import VNA
	from app import logSetup
	logSetup.initLogging()



	DEVICE_IP = '192.168.1.207'
	DEVICE_IPPort = 1025

	# Connect to the VNA
	print("Connecting to the remote VNA. This can take a while if the network is slow, or you're running in a VM.")
	vna = VNA.VNA(DEVICE_IP, DEVICE_IPPort)
	print("VNA connected and embedded data downloaded.")

	# Communication timeout is 500 milliseconds
	vna.setTimeout(500)

	# 45 KPts/second, attenuator set to 0dB, with a 512 point linear sweep from 375 MHz to 6000 Mhz
	vna.set_config(VNA.HOP_45K, VNA.ATTEN_0, freq=[375, 6000, 512])


	pprint.pprint("Actual sampled frequencies (in MHz):")
	pprint.pprint(vna.getFrequencies())

	# Start the VNA
	vna.start()

	# Load the factory calibration from the embedded memory into the VNA task
	try:
		vna.importFactoryCalibration()
		vna.measure_cal()
		vna.log.info("Factory calibration loaded! Cal complete: %s", vna.isCalibrationComplete())
	except VNA.VNA_Exception:
		print(traceback.format_exc())
		vna.log.info("Failed to load factory cal! %s", vna.isCalibrationComplete())


	for x in range(10):
		# Here is how you measure S-Parameters
		if vna.isCalibrationComplete():
			s_param_return_values = vna.measure_cal()

			# s_param_return_values is a subclass of namedtuple(). You can access the members like this:
			pprint.pprint(("S11: ", s_param_return_values.S11))
			pprint.pprint(("S12: ", s_param_return_values.S12))
			pprint.pprint(("S22: ", s_param_return_values.S22))
			pprint.pprint(("S21: ", s_param_return_values.S21))

		# And raw measurements, if you are interested in doing
		# an external calibration.
		raw_return_values = vna.measure_uncal()
		# raw_return_values is also a namedtuple() subclass.
		pprint.pprint(("T1R1: ", raw_return_values.T1R1))
		pprint.pprint(("T1R2: ", raw_return_values.T1R2))
		pprint.pprint(("T2R1: ", raw_return_values.T2R1))
		pprint.pprint(("T2R2: ", raw_return_values.T2R2))
		pprint.pprint(("Ref:  ", raw_return_values.Ref))


if __name__ == "__main__":
	test_class()
	# test_raw()
