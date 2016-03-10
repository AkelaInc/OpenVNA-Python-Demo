################################################################################
#### vnaclass.py	--	Common interfacing routines for vnalibrary.py		####
####																		####
####	Author: Abhejit Rajagopal <abhejit@ece.ucsb.edu>					####
####			Connor Wolf <cwolf@akelainc.com>							####
####																		####
####	Date: 07.27.2015													####
####																		####
################################################################################
from . import vnalibrary as vna
from . import vnaexceptions
import collections
import pickle
import time
import logging

##
#  \addtogroup Python-OOP-API
#
#  \section oop-api-brief Higher-Level VNA API Interface
#
# @authors Abhejit Rajagopal <abhejit@ece.ucsb.edu>, Connor Wolf <cwolf@akelainc.com>
#
#  This is the "OOP" API wrapper for the AKELA VNA
#  interface. It seeks to be a more pythonic wrapper for the underlying VNA interface.
#
#
#
#  @{
#

class VNA(vna.RAW_VNA):
	''' Higher-level object-oriented library for interfacing with one or
		more Akela VNAs.

		This class serves as a wrapper for vnalibrary.py, which directly wraps
		the C++ code in vnadll. Functionally, everything here can be implemented
		using only vnalibrary.py.

		Nevertheless, these routines are valuable as they abstract away *some* of the
		lower-level details of dealing with the hardware.

		Note that this inherits from \ref VNA::vnalibrary::RAW_VNA, so you can
		(and actually have to, for normal use) call RAW_VNA
		methods on it directly, without needing to manage two VNA instances.



	'''


	def __init__(self, device_ip, device_ip_port, vna_no=None, loglevel=logging.INFO):
		''' Connect and initialize a remote VNA.

			Sets up logging, creates a task instance to control the VNA,
			establishes connection with VNA on specified IP:port,
			initializes VNA  and downloads hw details,
			queries task state, and emits some info to the logging
			interface at the DEBUG level.

			Args:
				device_ip       -- (str) IP address of VNA hardware
				device_ip_port  -- (int) IP port-number for connection. Typically 1024+
				vna_no          -- (int/str) Number/String inserted into logger path
				                         for the relevant VNA.
				                         The resultant logging path will be: `Main.VNA-API-%%s`, where
				                         `%%s` is the value of `vna_no`.
				                         If not specified, this will default to the ASCII IP for
				                         the VNA.
				loglevel        -- (logging level) Set the log-level for the DLL interface. Defaults
				                         to `logging.INFO` if not specified.

			Returns:
				Nothing

		'''

		# Call the parent-class initializer
		super(VNA, self).__init__()

		#! @cond
		# (cond prevents doxygen from exposing a bunch of internal members)

		self.ip = device_ip

		# setup logging
		if vna_no:
			self.log = logging.getLogger("Main.VNA-API-%s" % vna_no)
		else:
			self.log = logging.getLogger("Main.VNA-API-%s" % device_ip.replace(".", "-"))

		self.log.setLevel(loglevel)


		# Set IP and Port

		self.setIPAddress(device_ip)
		ip_check1 = self.getIPAddress()
		self.log.debug('IP:		set-%s	returned-%s', device_ip, ip_check1)

		self.setIPPort(device_ip_port)
		ipport_check1 = self.getIPPort()
		self.log.debug('Port:	set-%s		returned-%s', device_ip_port, ipport_check1)

		# Open and test connection to VNA
		self.log.debug('Initializing... (downloads details from device, ETC: ~30secs)')
		self.initialize()
		# print(init_vna1)

		state1 = self.getState()
		self.log.debug('Task State:		%s', vna.TaskStateBOOK[state1])

		self.utilPingUnit()

		# Get hardware details
		self.__hwdetails = self.getHardwareDetails()
		self.log.debug('HW Details:	')
		for key, value in self.__hwdetails.items():
			self.log.debug('%s %s', str(key).rjust(30), str(value).rjust(20))


		# read calibration? if not:
		self.__calibration = {}
		self.__calibration['factory'] = None

		#! @endcond



	def set_config(self, hoprate, attenuation, freq=None):
		''' Configure a connected VNA with specified hoprate, attenuation
			and (optional) linear sweep parameters.

			Args:
				hoprate		-- (vna.HOP_x) frequency hop-rate from \ref HopRateSettings-Py
				attenuation	-- (vna.ATTEN_x) Set the tx attenuator to `x` db. Values from \ref AttenuationSettings-Py
				freq		-- (optional) three-tuple of frequencies used to generate
				                    a linear sweep of frequency points.
				                    Structure is `(start_freq, stop_freq, num_points)`,
				                    where `start_freq` and `stop_freq` are frequency
				                    numbers in megahertz, and `num_points` is a simple integer. <br>
				                    The sweep will be modified by \ref utilFixLinearSweepLimits to fit
				                    the requested parameters to the
				                    allowable frequencies on actual hardware

			Returns:
				Nothing
		'''

		# hop rate
		self.setHopRate(hoprate)
		hop_check1 = self.getHopRate()
		self.log.info('Hop:		set-%s	returned-%s', vna.HopRateBOOK[vna.HOP_1K], vna.HopRateBOOK[hop_check1])

		# attenuation
		self.setAttenuation(attenuation)
		atten_check1 = self.getAttenuation()
		self.log.info('Attenuation:	set-%s	returned-%s', vna.AttenuationBOOK[vna.ATTEN_11], vna.AttenuationBOOK[atten_check1])

		if freq is None:
			self.log.info('No frequency specified to `set_config`')
			return

		# frequencies
		assert len(freq) == 3, "You must pass a 3-tuple for the frequencies parameter."
		freqMIN = freq[0]
		freqMAX = freq[1]
		freqNUM = freq[2]
		assert (freqNUM > 0)

		freq_setL = self.utilGenerateLinearSweep(freqMIN, freqMAX, freqNUM)
		freq_checkN = self.getNumberOfFrequencies()
		freq_checkL = self.getFrequencies()
		# self.log.info('Frequencies:')
		# self.log.info('		checkN-%s',freq_checkN)
		# self.log.info('		checkL-%s',freq_checkL)

	# Force the doxygen generator to
	# properly look at the parent class for
	# start/stop methods.
	def start(self):
		''' Proxy for \ref RAW_VNA.start()
		'''
		super(VNA, self).start()

	def stop(self):
		''' Proxy for \ref RAW_VNA.stop()
		'''
		super(VNA, self).stop()


	def measure_uncal(self, verbosity=0):
		''' Routine to measure uncalibrated I-Q using an configured VNA task

		'''

		# Measure each path + ref
		ret = self.measureUncalibrated()

		Scan_Return = collections.namedtuple("Scan_Return", ['T1R1', 'T1R2', 'T2R1', 'T2R2', 'Ref'])
		return Scan_Return(*ret)

		#return [measure_check, dict(Scan_Return(*nparr)._asdict())]

	def measure_cal(self):
		''' Measure S-Parameters using the internal calibration mechanism from the DLL.

		'''
		# Measure each path + ref
		ret = self.measure2PortCalibrated()

		Scan_Return = collections.namedtuple("Scan_Return", ["S11", "S21", "S12", "S22"])
		return Scan_Return(*ret)


	def save_dll_cal_auto(self):
		addr = self.getIPAddress()
		self.save_dll_cal("VNA-Cal-%s.pik" % (addr))

	def load_dll_cal_auto(self):
		addr = self.getIPAddress()
		self.load_dll_cal("VNA-Cal-%s.pik" % (addr))


	def save_dll_cal(self, filepath):
		''' Save the generated cal from the internal DLL calibration mechanism
			to a local file.

			Args:
				filepath	--	(string) Local filesystem path where the cal
										data will be saved. <br>
										Note that if the file exists, it will be overwritten!


			---

			\exceptions \ref VNA_Exception_Bad_Cal if there is no calibration to save.
		'''

		if not self.isCalibrationComplete():
			self.log.error("Calibration is not present! Nothing to save")
			raise vnaexceptions.VNA_Exception_Bad_Cal("No calibration to save!")

		cal_f = self.getCalibrationFrequencies()
		cal_p = self.exportCalibration()

		cal = {
				"time"     : time.time(),
				"address"  : self.getIPAddress(),
				"hardware" : self.getHardwareDetails(),
				"cal_f"    : cal_f,
				"cal_p"    : cal_p,
		}
		with open(filepath, "wb") as fp:
			pickle.dump(cal, fp)

	def load_dll_cal(self, filepath, checkip=True, checkserial=True):
		''' Load a calibration data-set from a save file.

			Args:
				filepath	-- (string) Local filesystem path to where the
										saved calibration is located.
				checkserial -- (bool)   Validate that the serial number from the calibration
										matches the serial number from the VNA.
				checkip		-- (bool)   Validate that the IP of the connected VNA is the same
										as the IP from the calibration.

		'''

		with open(filepath, "rb") as fp:
			cal = pickle.load(fp)

		if checkip and cal['address'] != self.getIPAddress():
			raise vnaexceptions.VNA_Exception_Bad_Cal("Calibration remote IP does not match connected hardware!")
		if checkserial and cal['hardware']['serial_number'] != self.getHardwareDetails()['serial_number']:
			raise vnaexceptions.VNA_Exception_Bad_Cal("Connected VNA serial number does not match calibration serial!")

		cal_f = cal['cal_f']
		cal_p = cal['cal_p']

		self.importCalibration(cal_f, *cal_p)


# end doxygen block
## @}
