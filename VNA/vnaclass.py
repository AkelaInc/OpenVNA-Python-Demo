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
from . import calutil
import collections
import pickle
import time
import logging

##
#  \addtogroup Python-OOP-API
#  @{
#

class VNA(vna.RAW_VNA):
	''' Higher-level object-oriented library for interfacing with one or
		more Akela VNAs.


		This class serves as a wrapper for vnalibrary.py, which directly wraps
		the C++ code in vnadll. Technically, everything here can be implemented
		using only vnalibrary.py. Nevertheless, these routines are valuable
		as they abstract away the low-level details of dealing with the C++.

		Common usage:	see testVNA.py
			import VNA
			vna = VNA.VNA(DEVICE_IP, DEVICE_IPPort)	#create VNA object
			[...] = vna.set_config(...)				#configure
			[...] = vna.setup_start()				#enable aquisition
			[...] = vna.measure_uncal(...)			#measure paths
	'''


	def __init__(self, DEVICE_IP, DEVICE_IPPort, vna_no=None, loglevel=logging.INFO):
		''' Routine when connecting to an Akela VNA
			Sets up logging, creates a task instance to control the VNA,
			establishes connection with VNA on specified IP:port,
			initializes VNA  and downloads hw details,
			queries task state, and emits some info to the logging
			interface at the DEBUG level.

			Args:
				DEVICE_IP		-- (str) IP address of VNA hardware
				DEVICE_IPPort 	-- (int) IP port-number for connection
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

		self.ip = DEVICE_IP

		# setup logging
		if vna_no:
			self.log = logging.getLogger("Main.VNA-API-%s" % vna_no)
		else:
			self.log = logging.getLogger("Main.VNA-API-%s" % DEVICE_IP.replace(".", "-"))

		self.log.setLevel(loglevel)


		# Set IP and Port

		self.setIPAddress(DEVICE_IP)
		ip_check1 = self.getIPAddress()
		self.log.debug('IP:		set-%s	returned-%s', DEVICE_IP, ip_check1)

		self.setIPPort(DEVICE_IPPort)
		ipport_check1 = self.getIPPort()
		self.log.debug('Port:	set-%s		returned-%s', DEVICE_IPPort, ipport_check1)

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


	def measure_uncal(self, paths, verbosity=0):
		''' Routine to measure uncalibrated I-Q using an configured VNA task

		'''

		# Hacky cheat = sum is a lazy bitwise OR for cases where we can be confident we'll not have
		# duplicates.
		path = sum(set([path for path in paths]))

		# Measure each path + ref
		ret = self.measureUncalibrated(path)

		Scan_Return = collections.namedtuple("Scan_Return", ['T1R1', 'T1R2', 'T2R1', 'T2R2', 'Ref'])
		return Scan_Return(*ret)

		#return [measure_check, dict(Scan_Return(*nparr)._asdict())]

	def measure_cal(self, paths):
		''' Measure S-Parameters using the internal calibration mechanism from the DLL.

		'''
		# Hacky cheat = sum is a lazy bitwise OR for cases where we can be confident we'll not have
		# duplicates.
		path = sum(set([path for path in paths]))

		# Measure each path + ref
		ret = self.measure2PortCalibrated(path)

		Scan_Return = collections.namedtuple("Scan_Return", ["S11", "S21", "S12", "S22"])
		return Scan_Return(*ret)


	def measure_local_cal(self, paths, caltype='solt'):
		''' Measure S-parameters using specified calibration (precomputed)

			General idea:
				calterms = calibration['solt'][1]
				[A, U, V, B, R] = vna.measure_uncal(paths)
				calibrated_params = VNA.calutil.applyCalibration(calterms, A, U, V, B, R)
				[py_S11, py_S21, py_S12, py_S22] = calibrated_params
		'''


		return_values = self.measure_uncal(paths)

		if self.__calibration is None:
			self.log.warning('!!!! WARNING: No calibration data found! Data is raw!')
			return return_values
		else:
			try:
				calterms = self.__calibration[caltype][1]
			except Exception:
				self.log.info('Error loading calibration! Check self.__calibration first. Then check if caltype is valid. Data is raw!')
				return return_values

			try:
				A = return_values.T1R1
				U = return_values.T1R2
				V = return_values.T2R1
				B = return_values.T2R2
				R = dut_R = return_values.Ref
				freq = self.freq_checkL

				[dut_S11, dut_S21, dut_S12, dut_S22] = calutil.applyCalibration(calterms, freq, A, U, V, B, R, caltype=caltype)

			except Exception:
				self.log.error('Error loading data or applying calibration! Data is raw!')
				return return_values


		Scan_Return = collections.namedtuple("Scan_Return", ['S11', 'S21', 'S12', 'S22', 'Ref'])
		return Scan_Return(dut_S11, dut_S21, dut_S12, dut_S22, dut_R)


	def generate_caldata(self, paths, ports=[1,2], caltype='SOLT'):
		''' Generate VNA calibration data from a set of measurements.

			Will prompt the user to execute calibration steps.

			Args:
				paths		--	(list-vna.RFPathBOOK) paths to measure
				caltype		--	(optional, str) type of calibration to perform
				ports		--	(optional, list--int) ports to calibrate

			Returns:
				calDict		--	(dict) holding raw data for calibration
									(produced by calutil.generate_CALdict )
		'''

		print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
		print('~~ VNA Calibration routine ~~')
		print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
		print('~ !! Follow the instructions step-by-step to produce the calibration !!')
		print('~ !! Hit enter after each prompt when you have finished the task !!')
		print('')
		prompt = lambda key='<enter>': 'Press '+key+' to continue...:'

		#					S11	(A)			S21 (U)		S12 (V)		S22 (B)
		pathstr2signal = { 'T1R1': 'a', 'T1R2': 'u', 'T2R1': 'v', 'T2R2': 'b' }

		calDict = calutil.generate_rawDict(ports, caltype=caltype)
		calDict['frequencies'] = self.freq_checkL

		if caltype.lower()=='solt':
			for cal_portconn in sorted(calDict):
				if cal_portconn.lower()=='frequencies':
					continue


				for cal_portterm in sorted(calDict[cal_portconn]):
					print('--> Cal procedure:	PORT-%s		TERM-%s		...' % (cal_portconn,cal_portterm) )
					value = input(prompt())

					[measure_check, return_values] = self.measure_uncal(paths)

					if 'T1R1' in return_values._fields:
						calDict[cal_portconn][cal_portterm]['a'] = {'signal': return_values.T1R1, 'ref': return_values.Ref}
					if 'T1R2' in return_values._fields:
						calDict[cal_portconn][cal_portterm]['u'] = {'signal': return_values.T1R2, 'ref': return_values.Ref}
					if 'T2R1' in return_values._fields:
						calDict[cal_portconn][cal_portterm]['v'] = {'signal': return_values.T2R1, 'ref': return_values.Ref}
					if 'T2R2' in return_values._fields:
						calDict[cal_portconn][cal_portterm]['b'] = {'signal': return_values.T2R2, 'ref': return_values.Ref}

					# measure_values = dict(return_values._asdict())
					# for pt in measure_values.keys():
					# 	if pt!='Ref':
					# 		print('%s	%s	%s	%s' % (cal_portconn, cal_portterm, pathstr2signal[pt], pt))
					# 		reference = measure_values['Ref'] # should update this to record particular path's ref!
					# 		signal = measure_values[pt]
					# 		if calDict[cal_portconn][cal_portterm][pathstr2signal[pt]] is not None:
					# 			value = input('There is something stored here already... are you sure you want to overwrite? (1 or 0)')
					# 			value = int(value)
					# 			if not value:
					# 				continue


					# 		calDict[cal_portconn][cal_portterm][pathstr2signal[pt]] = {'signal':signal, 'ref':reference}
					# 					del pt, reference, signal, return_values, measure_values



		return calDict


	def generate_cal(self, calDict, caltype='solt'):
		''' Generate VNA calibration terms from raw measurements
			Takes a calibration data dictionary, and saves the computed error
			terms into a internal dictinoary which notes
			which type of calibration was performed.

			Args:
				calDict		--	(dict) holding raw data for calibration
									(produced by calutil.generate_CALdict )
				caltype		--	(optional, str) type of calibration data

			Returns:
				calibration	--	(dict) holding calterms for various calibrations
		'''
		if caltype.lower()=='solt':
			[caldata, calterms, calib] = calutil.generate_CALterms(calDict, caltype='solt')
			self.__calibration[caltype] = [caldata, calterms, calib]

		return self.__calibration


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
										Note that if the file exists, it will be
										overwritten!
			---

			\raises \ref VNA_Exception_Bad_Cal if there is no calibration to save.
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
