


from . import vnalibrary as vnal

import numpy as np
import time
import unittest


class TestVnaNoHardwarePresent(unittest.TestCase):

	def setUp(self):
		self.vna = vnal.RAW_VNA()

	def test_version_string(self):
		tmp = vnal.versionString()
		self.assertTrue(tmp)


	def test_ip_address(self):
		tmp = self.vna.getIPAddress()
		self.assertEqual(tmp, None)
		self.vna.setIPAddress("192.168.123.123")
		tmp = self.vna.getIPAddress()
		self.assertEqual(tmp, "192.168.123.123")

	def test_ip_port(self):
		tmp = self.vna.getIPPort()
		self.assertEqual(tmp, 0)
		self.vna.setIPPort(1234)
		tmp = self.vna.getIPPort()
		self.assertEqual(tmp, 1234)

	def test_freq_num(self):
		tmp = self.vna.getNumberOfFrequencies()
		self.assertEqual(tmp, 0)

	def test_get_hardware_details(self):
		tmp = self.vna.getHardwareDetails()

		# These values are 0 when the hardware is still
		# in TASK_UNINITIALIZED
		self.assertEqual(0, tmp['minimum_frequency'])
		self.assertEqual(0, tmp['maximum_frequency'])
		self.assertEqual(0, tmp['maximum_points'])
		self.assertEqual(0, tmp['serial_number'])
		self.assertEqual([0, 0, 0, 0, 0, 0, 0, 0], tmp['band_boundaries'])
		self.assertEqual(0, tmp['number_of_band_boundaries'])


	def test_calibration_number_of_frequencies(self):
		tmp = self.vna.getCalibrationNumberOfFrequencies()
		tmp = self.assertEqual(tmp, 0)


	def test_calibration_frequencies(self):
		tmp = self.vna.getCalibrationFrequencies()
		tmp = self.assertEqual(tmp.shape, (0, ))



	def test_get_frequencies(self):
		tmp = self.vna.getFrequencies()
		tmp = self.assertEqual(tmp.shape, (0, ))

		# The following lines /work/, but require being in the "TASK_STOPPED" state,
		# which I cannot test at the moment.
		# arr = vnal.DoubleArrayFactory(5)(10, 20, 30, 40, 50)
		# ret = vnal.setFrequencies(arr, len(arr))
		# self.assertEqual(ret, vnal.ERR_OK, "Error! Return code: '%s'" % vnal.ErrCodeBOOK[ret])

		# tmp = vnal.getFrequencies(self.t)
		# self.assertEqual(tmp.shape, (5, ))


	def test_state(self):
		state = self.vna.getState()
		self.assertEqual(state, vnal.TASK_UNINITIALIZED)

	def test_timeout(self):
		val = self.vna.getTimeout()
		self.assertEqual(val, 150)
		self.vna.setTimeout(0)
		val = self.vna.getTimeout()
		self.assertEqual(val, 0)
		self.vna.setTimeout(50000000)
		val = self.vna.getTimeout()
		self.assertEqual(val, 50000000)
		self.vna.setTimeout(155)
		val = self.vna.getTimeout()
		self.assertEqual(val, 155)


class TestVnaCommsHardwarePresent(unittest.TestCase):

	def setUp(self):
		self.vna = vnal.RAW_VNA()

		self.vna.setIPAddress("192.168.1.207")
		self.vna.setIPPort(1026)
		self.vna.setTimeout(150)
		self.vna.initialize()

	def test_basic_comms(self):
		'''
		This just validates the basic communication setup is working.
		'''
		pass


class TestVnaHardwarePresent(unittest.TestCase):

	def setUp(self):
		self.vna = vnal.RAW_VNA()

		self.vna.setIPAddress("192.168.1.207")
		self.vna.setIPPort(1026)
		self.vna.setTimeout(150)
		self.vna.initialize()

	def config(self):
		self.vna.setAttenuation(vnal.ATTEN_0)
		self.vna.setHopRate(vnal.HOP_45K)
		self.vna.utilGenerateLinearSweep(400, 1500, 1024)


	def test_hardware_details(self):
		'''
		This just validates the basic communication setup is working.
		'''
		details = self.vna.getHardwareDetails()
		expect = {
						'band_boundaries':  [3000, 1500, 750, 0, 0, 0, 0, 0],
						'maximum_frequency': 6050,
						'maximum_points': 4001,
						'serial_number': 401,
						'minimum_frequency': 375,
						'number_of_band_boundaries': 3
				}
		self.assertEqual(details, expect)

	def test_get_number_of_frequencies(self):
		self.config()
		val = self.vna.getNumberOfFrequencies()
		self.assertEqual(val, 1024)

	def test_utilGenerateLinearSweep(self):
		self.config()

		self.vna.utilGenerateLinearSweep(400, 1500, 1024)
		val = self.vna.getNumberOfFrequencies()
		self.assertEqual(val, 1024)

		self.vna.utilGenerateLinearSweep(400, 1500, 3)
		val = self.vna.getNumberOfFrequencies()
		self.assertEqual(val, 3)

		freqs = self.vna.getFrequencies()
		expect = [  400.00010515,   949.99971334,  1499.99909569]

		# We have to use isclose() because the constants
		# in this file aren't /quite/ the /EXACT/ value due
		# to issues with printing precision.
		self.assertTrue(all(np.isclose(expect, freqs)))

		self.vna.utilGenerateLinearSweep(400, 1500, 8)
		val = self.vna.getNumberOfFrequencies()
		self.assertEqual(val, 8)


		freqs = self.vna.getFrequencies()
		expect = [
					400.00010515,   557.14175338,   714.28340161,   871.42527569,
					1028.56692392,  1185.70857216,  1342.85022039,  1499.99186862
				]

		# We have to use isclose() because the constants
		# in this file aren't /quite/ the /EXACT/ value due
		# to issues with printing precision.
		self.assertTrue(all(np.isclose(expect, freqs)))

	def test_hop_rate(self):
		self.assertEqual(self.vna.getHopRate(), vnal.HOP_UNDEFINED)
		self.vna.setHopRate(vnal.HOP_15K)
		self.assertEqual(self.vna.getHopRate(), vnal.HOP_15K)


	def test_attenuation(self):
		self.assertEqual(self.vna.getAttenuation(), vnal.ATTEN_UNDEFINED)
		self.vna.setAttenuation(vnal.ATTEN_6)
		self.assertEqual(self.vna.getAttenuation(), vnal.ATTEN_6)

	def test_state(self):
		state = self.vna.getState()
		self.assertEqual(state, vnal.TASK_STOPPED)

	def test_start_stop(self):
		self.config()

		state = self.vna.getState()
		self.assertEqual(state, vnal.TASK_STOPPED)

		self.vna.start()

		state = self.vna.getState()
		self.assertEqual(state, vnal.TASK_STARTED)

		self.vna.stop()

		state = self.vna.getState()
		self.assertEqual(state, vnal.TASK_STOPPED)


	def test_ping_unit(self):
		self.vna.utilPingUnit()

class TestVnaAcquisition(unittest.TestCase):

	def setUp(self):
		self.vna = vnal.RAW_VNA()

		self.vna.setIPAddress("192.168.1.207")
		self.vna.setIPPort(1026)
		self.vna.setTimeout(150)
		self.vna.initialize()

		self.vna.setAttenuation(vnal.ATTEN_0)
		self.vna.setHopRate(vnal.HOP_45K)
		self.vna.utilGenerateLinearSweep(400, 1500, 1024)
		self.vna.start()

	def tearDown(self):
		self.vna.stop()



	def test_measure_uncal(self):
		T1R1, T1R2, T2R1, T2R2, Ref = self.vna.measureUncalibrated(vnal.PATH_T1R1 | vnal.PATH_T1R2)
		self.assertTrue(any(T1R1))
		self.assertTrue(any(T1R2))
		self.assertFalse(any(T2R1))
		self.assertFalse(any(T2R2))
		self.assertTrue(any(Ref))

		T1R1, T1R2, T2R1, T2R2, Ref = self.vna.measureUncalibrated(0)
		self.assertFalse(any(T1R1))
		self.assertFalse(any(T1R2))
		self.assertFalse(any(T2R1))
		self.assertFalse(any(T2R2))
		self.assertTrue(any(Ref))

		T1R1, T1R2, T2R1, T2R2, Ref = self.vna.measureUncalibrated(vnal.PATH_T1R1 | vnal.PATH_T1R2 | vnal.PATH_T2R1 | vnal.PATH_T2R2)
		self.assertTrue(any(T1R1))
		self.assertTrue(any(T1R2))
		self.assertTrue(any(T2R1))
		self.assertTrue(any(T2R2))
		self.assertTrue(any(Ref))


	def test_import_cal(self):

		freqs     = [500, 1000, 1500, 2000]
		e00       = np.array([1+5j, 2+6j, 3+7j, 4+8j])
		e11       = np.array([1+5j, 2+6j, 3+7j, 4+8j])
		e10e01    = np.array([1+5j, 2+6j, 3+7j, 4+8j])
		e30       = np.array([1+5j, 2+6j, 3+7j, 4+8j])
		e22       = np.array([1+5j, 2+6j, 3+7j, 4+8j])
		e10e32    = np.array([1+5j, 2+6j, 3+7j, 4+8j])
		ep33      = np.array([1+5j, 2+6j, 3+7j, 4+8j])
		ep22      = np.array([1+5j, 2+6j, 3+7j, 4+8j])
		ep12ep32  = np.array([1+5j, 2+6j, 3+7j, 4+8j])
		ep03      = np.array([1+5j, 2+6j, 3+7j, 4+8j])
		ep11      = np.array([1+5j, 2+6j, 3+7j, 4+8j])
		ep23ep01  = np.array([1+5j, 2+6j, 3+7j, 4+8j])

		self.vna.importCalibration(freqs, e00, e11, e10e01, e30, e22, e10e32, ep33, ep22, ep12ep32, ep03, ep11, ep23ep01)


		r_e00, r_e11, r_e10e01, r_e30, r_e22, r_e10e32, r_ep33, r_ep22, r_ep12ep32, r_ep03, r_ep11, r_ep23ep01 = self.vna.exportCalibration()

		self.assertTrue(all(e00      == r_e00))
		self.assertTrue(all(e11      == r_e11))
		self.assertTrue(all(e10e01   == r_e10e01))
		self.assertTrue(all(e30      == r_e30))
		self.assertTrue(all(e22      == r_e22))
		self.assertTrue(all(e10e32   == r_e10e32))
		self.assertTrue(all(ep33     == r_ep33))
		self.assertTrue(all(ep22     == r_ep22))
		self.assertTrue(all(ep12ep32 == r_ep12ep32))
		self.assertTrue(all(ep03     == r_ep03))
		self.assertTrue(all(ep11     == r_ep11))
		self.assertTrue(all(ep23ep01 == r_ep23ep01))

		self.assertEqual(len(freqs), self.vna.getCalibrationNumberOfFrequencies())




# TODO: MOAR TESTS -
# setFrequencies

# utilNearestLegalFreq
# utilFixLinearSweepLimits
# utilPingUnit


def test():
	unittest.main()


if __name__ == '__main__':
	test()