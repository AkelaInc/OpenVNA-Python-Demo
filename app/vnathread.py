
import threading
import VNA
import time
try:
	import queue
except ImportError:
	import Queue as queue
import runstate
import traceback
import logging

import numpy as np

import os
import os.path

import VNA
import VNA.vnaexceptions


class ThreadExit(Exception):
	pass




def log_mag(inarr):
	return 20 * np.log10(np.absolute(inarr))

def get_param_from_ret(param, scan):

	s_params = {
		'S11' : 'S11',
		'S21' : 'S21',
		'S12' : 'S12',
		'S22' : 'S22'
	}

	t_params = {
		'S11' : 'T1R1',
		'S21' : 'T1R2',
		'S12' : 'T2R1',
		'S22' : 'T2R2'
	}

	if hasattr(scan, "S11"):
		key = "%s" % s_params[param]
		return key, getattr(scan, key)
	elif hasattr(scan, "T1R1"):
		key = "%s" % t_params[param]
		value = getattr(scan, key)
		value = value / scan.Ref
		return key, value
	else:
		raise ValueError("Unknown path: '%s'. Wat?" % param)



class VnaThread():
	def __init__(self, vna_no, command_queue, response_queue):


		self.vna_no = vna_no
		self.vna_connected = False
		self.log = logging.getLogger("Main.VNA-%s" % vna_no)


		self.command_queue  = command_queue
		self.response_queue = response_queue
		self.vna            = None
		self.runstate       = False
		self.log.info("VNA Thread running")


		self.vna_fmax = 6000
		self.vna_fmin = 375


		self.start_f     = 375
		self.stop_f      = 6050
		self.npts_s      = 256

		# self.start_f = 500
		# self.stop_f  = 6000
		# self.npts_s  = 256

		self.connection_params = None

	def tryLoadLocalCal(self):
		fname = "../VNA-Cal-{ip}.csv".format(ip=self.vna.getIPAddress())
		if not os.path.exists(fname):
			self.log.warning("Could not find local CSV cal file '%s'.", fname)
			return False

		self.log.info("Found local cal file! Trying to load.")
		dat = np.genfromtxt(fname, delimiter=",", skip_header=1, dtype=np.float64)

		# Row structure:
		# Freq,
		# EDFi,EDFq,
		# ESFi,ESFq,
		# ERFi,ERFq,
		# EXFi,EXFq,
		# ELFi,ELFq,
		# ETFi,ETFq,
		# EDRi,EDRq,
		# ESRi,ESRq,
		# ERRi,ERRq,
		# EXRi,EXRq,
		# ELRi,ELRq,
		# ETRi,ETRq

		freqs = dat[...,0]
		EDF = dat[..., 1] + 1j* dat[..., 2] # EDF/e00
		ESF = dat[..., 3] + 1j* dat[..., 4] # ESF/e11
		ERF = dat[..., 5] + 1j* dat[..., 6] # ERF/e10e01
		EXF = dat[..., 7] + 1j* dat[..., 8] # EXF/e30
		ELF = dat[..., 9] + 1j* dat[...,10] # ELF/e22
		ETF = dat[...,11] + 1j* dat[...,12] # ETF/e10e32
		EDR = dat[...,13] + 1j* dat[...,14] # EDR/ep33
		ESR = dat[...,15] + 1j* dat[...,16] # ESR/ep22
		ERR = dat[...,17] + 1j* dat[...,18] # ERR/ep12ep32
		EXR = dat[...,19] + 1j* dat[...,20] # EXR/ep03
		ELR = dat[...,21] + 1j* dat[...,22] # ELR/ep11
		ETR = dat[...,23] + 1j* dat[...,24] # ETR/ep23ep01

		# print(freqs, EDF, ESF, ERF, EXF, ELF, ETF, EDR, ESR, ERR, EXR, ELR, ETR )

		self.vna.importCalibration(freqs, EDF, ESF, ERF, EXF, ELF, ETF, EDR, ESR, ERR, EXR, ELR, ETR)

		print("Cal name:", fname)
		return True

	def do_connect(self, connection_params):
		if self.vna:
			try:
				# Try to stop the current acquisition, if any
				self.vna.stop()
			except Exception:
				pass

		self.vna = VNA.VNA(*connection_params, vna_no=self.vna_no)
		self.vna.set_config(VNA.HOP_45K, VNA.ATTEN_0, freq=[self.start_f, self.stop_f, self.npts_s])
		self.vna.setTimeout(500)



		try:
			self.vna.importFactoryCalibration()
			self.log.info("Factory calibration loaded! Cal complete: %s", self.vna.isCalibrationComplete())
		except VNA.VNA_Exception:
			for line in traceback.format_exc().split("\n"):
				self.log.warn("No factory calibration in VNA?")
				self.log.warn(line)

			self.tryLoadLocalCal()

	def running(self):
		return self.vna.getState() == VNA.TASK_STARTED


	def dispatch(self, command):
		assert isinstance(command, tuple), "All commands must be a (command, params) tuple!"
		assert len(command) == 2, "All commands must be a (command, params) tuple!"

		command, params = command

		self.log.info("Command message: '%s' - params: '%s'", command, params)
		if command == "connect":
			if not self.vna_connected:
				try:
					self.log.info("Connecting to VNA")
					self.log.info("Please wait while the embedded calibration data is fetched.")
					self.log.info("This can take up to a minute or two.")
					self.connection_params = params
					self.do_connect(self.connection_params)
					self.response_queue.put(("connect", True))

					self.log.info("VNA Connected.")
				except VNA.VNA_Exception:
					self.log.error("Failure connecting to the hardware!")
					self.log.error("Please try again, or power-cycle the VNA.")
					return

				self.vna_connected = True
			else:
				try:
					self.vna.stop()
				except VNA.VNA_Exception:
					pass

				self.vna = None
				self.log.info("VNA Disconnected")
				self.response_queue.put(("connect", False))
				self.vna_connected = False
				self.runstate      = False


		elif command == "run":
			if not self.vna and params == True:
				self.log.error("You have to connect to a VNA first!")
				return True
			if self.runstate == params and params == True:
				self.log.error("Run command that matches current state?")
			else:

				if params == True:
					self.log.info("Starting VNA task")
					self.vna.set_config(VNA.HOP_45K, VNA.ATTEN_0, freq=[self.start_f, self.stop_f, self.npts_s])
					self.vna.start()
					self.runstate = True
				else:
					if self.vna != None:
						self.log.info("Stopping VNA task")
						self.vna.stop()
						self.runstate = False


		elif command == "halt" and params == True:
			raise ThreadExit("Exiting VNA process!")

		elif command == "sweep":
			self.npts_s , self.start_f, self.stop_f = params
			self.bounds_check()
			if self.vna and self.running():
				self.restart_acq()

		elif command == "npts":
			if params == self.npts_s:
				self.log.warn("Point number didn't change? Nothing to do")
				return
			self.npts_s = params
			self.bounds_check()
			if self.vna and self.running():
				self.restart_acq()
		elif command == "start-stop":
			start, stop = params
			if self.start_f == start and self.stop_f == stop:
				self.log.warn("Start and stop frequency didn't change? Nothing to do")
				return

			self.start_f, self.stop_f = start, stop
			self.bounds_check()

			if self.vna and self.running():
				self.restart_acq()
		elif command == "calibrate":
			self.handle_calibrate(step = params)
		elif command == "cal_data":
			self.calibrate_manage(command = params)
		else:
			self.log.error("Unknown command: '%s'", command)
			self.log.error("Command parameters: '%s'", params)

	def bounds_check(self):

		self.vna_fmin = 375
		self.vna_fmax = 6050


		if self.start_f > self.vna_fmax or self.start_f < self.vna_fmin:
			self.log.error("Start frequency outside hardware supported bounds (%s-%s) - %s. Clamping value", self.vna_fmin, self.vna_fmax, self.start_f)
			self.start_f = max(self.vna_fmin, min(self.start_f, self.vna_fmax))
		if self.stop_f > self.vna_fmax or self.stop_f < self.vna_fmin:
			self.log.error("Stop frequency outside hardware supported bounds (%s-%s) - %s. Clamping value", self.vna_fmin, self.vna_fmax, self.stop_f)
			self.stop_f = max(self.vna_fmin, min(self.stop_f, self.vna_fmax))

		if self.start_f >= self.stop_f:
			if self.start_f - 1 < self.vna_fmin:
				self.stop_f = self.start_f + 1
			elif self.stop_f + 1 > self.vna_fmax:
				self.start_f = self.stop_f - 1
			else:
				self.start_f = self.stop_f - 1

		if self.npts_s < 1:
			self.log.error("You must sample at least one point! Clamping value.")
			self.npts_s = 1

		if self.npts_s > 2048:
			self.log.error("Maximum supported sample points is 2048! Clamping value.")
			self.npts_s = 2048

	def calibrate_manage(self, command):

		if command == 'CAL_LOAD':
			if self.tryLoadLocalCal():
				self.log.info("Found local CSV calibration! Loading....")
			else:
				self.log.info("No local CSV calibration found. Attempting to load a PIK calibration.")
				self.vna.load_dll_cal_auto()

		elif command == 'CAL_FACTORY':
			try:
				self.vna.importFactoryCalibration()
				self.vna.measure_cal()
				self.log.info("Factory calibration loaded! Cal complete: %s", self.vna.isCalibrationComplete())
				return
			except VNA.VNA_Exception:
				print(traceback.format_exc())
				self.log.info("Failed to load factory cal! %s", self.vna.isCalibrationComplete())

		elif command == 'CAL_CLEAR':
			self.vna.clearCalibration()
		elif command == 'CAL_SAVE':
			self.vna.save_dll_cal_auto()


		else:
			raise ValueError("Unknown calibration management command: %s." % command)

	def handle_calibrate(self, step):
		commands = {
			'STEP_P1_OPEN'  : VNA.STEP_P1_OPEN,
			'STEP_P1_SHORT' : VNA.STEP_P1_SHORT,
			'STEP_P1_LOAD'  : VNA.STEP_P1_LOAD,
			'STEP_P2_OPEN'  : VNA.STEP_P2_OPEN,
			'STEP_P2_SHORT' : VNA.STEP_P2_SHORT,
			'STEP_P2_LOAD'  : VNA.STEP_P2_LOAD,
			'STEP_THRU'     : VNA.STEP_THRU,
			}

		if not step in commands:
			raise VNA.VNA_Exception_Bad_Cal("Invalid calibration step: %s" % step)

		self.vna.measureCalibrationStep(commands[step])
		self.log.info("Calibration step complete.")
	def restart_acq(self, check=False):
		if check:
			state = self.vna.getState()
			if state == VNA.TASK_STARTED:
				return

			elif state == VNA.TASK_UNINITIALIZED or state == VNA.TASK_STOPPED:
				self.log.info("Restarting task!")
				self.log.info("Current State: %s", VNA.TaskStateBOOK[state])
			else:
				raise ValueError("Unknown state?")
		else:
			try:
				self.vna.stop()
			except VNA.VNA_Exception_Wrong_State:
				pass
		self.vna.set_config(VNA.HOP_45K, VNA.ATTEN_0, freq=[self.start_f, self.stop_f, self.npts_s])
		self.vna.start()


	def get_fft(self, data, points):


		data_len = data.shape[0]

		# Apply windowing (needs to be an elementwise multiplication)
		data = np.multiply(data, np.hanning(data_len))

		# Pad the start of the array for phase-correctness, and
		# the end to make the calculation a power of N
		step_val = abs(self.start_f - self.stop_f) / self.npts_s
		start_padding = max(int(self.start_f/step_val), 0)

		startsize = start_padding + data_len

		sizes = [128, 256, 512, 1024, 2048, 4096, 8192]
		start_idx   = 0
		output_size = 0
		while output_size < startsize and start_idx < len(sizes):
			output_size = sizes[start_idx]
			start_idx += 1

		end_padding = max(output_size - startsize, 0)

		# Default padding value is "0"
		arr = np.pad(data, (start_padding, end_padding), mode='constant')

		fft_data = np.fft.ifft(arr)

		# Chop off the negative time component (we don't care about it here)
		fft_data = fft_data[:int(output_size/2)]
		fft_data = np.absolute(fft_data)

		if self.start_f == self.stop_f:
			return fft_data, np.array(range(fft_data.shape[0]))

		pts = np.array(range(fft_data.shape[0]))

		# Convert to hertz
		step_val = step_val * 1e6
		pts = pts * (1 / (len(pts) * step_val * 2))

		pts = pts * 1e9
		return fft_data, pts


	def get_data(self):

		self.restart_acq(check=True)

		# if not self.vna.isCalibrationComplete():
		# 	try:
		# 		self.vna.importFactoryCalibration()
		# 		self.vna.measure_cal()
		# 		self.log.info("Factory calibration loaded! Cal complete: %s", self.vna.isCalibrationComplete())
		# 	except VNA.VNA_Exception:
		# 		print(traceback.format_exc())
		# 		self.log.info("Failed to load factory cal! %s", self.vna.isCalibrationComplete())

		try:
			if self.vna.isCalibrationComplete():
				self.log.info("Doing calibrated measurement!")
				return_values = self.vna.measure_cal()
			else:
				return_values = self.vna.measure_uncal()

		except VNA.vnaexceptions.VNA_Exception_No_Response:
			self.log.info("VNA Exception No Response. Attempting to restart acquisition.")
			self.vna.stop()
			self.log.info("VNA Acquisition halted. Restarting...")
			time.sleep(0.1)
			self.vna.set_config(VNA.HOP_45K, VNA.ATTEN_0, freq=[self.start_f, self.stop_f, self.npts_s])

			# Be double plus sure we're stopped.
			try:
				self.vna.stop()
			except VNA.VNA_Exception_Wrong_State:
				pass
			time.sleep(0.1)
			self.vna.start()
			return

		compensated_data = {}



		fft_data = {}
		fft_pts  = []
		frequencies = self.vna.getFrequencies()

		assert frequencies is not None

		for path in ('S11', 'S12', 'S21', 'S22', 'S11-FFT', 'S21-FFT', 'S12-FFT', 'S22-FFT'):
			base = path.split("-")[0]
			key, val = get_param_from_ret(base, return_values)
			if "FFT" in path:
				fft_data_tmp, fft_pts = self.get_fft(val, frequencies)
				fft_data[path] = fft_data_tmp
			else:
				compensated_data[path] = log_mag(val)

		# print([len(compensated_data[path]) for path in compensated_data.keys()])
		# if not any([len(compensated_data[path]) for path in compensated_data.keys()]):

		if not len(compensated_data):
			frequencies = []


		fft_max = {}
		for key, arr in fft_data.items():
			fft_max[key] = np.max(arr)

		data = {
			'comp_data' : compensated_data,
			'pts'       : frequencies,
			'fft_data'  : fft_data,
			'fft_pts'   : fft_pts,
			'fft_max'   : fft_max,
		}


		data['pts'] = list(data['pts'])
		data['fft_pts'] = list(data['fft_pts'])


		# dict_children = [('comp_data', 'pts'), ('fft_data', 'fft_pts')]
		# for child_d, src_k in dict_children:
		# 	for key in data[child_d]:
		# 		data[child_d][key] = list(zip(data[src_k], list(data[child_d][key])))


		self.response_queue.put(("sweep data", data))

	def process(self):
		if self.runstate and self.vna:
			self.get_data()

		if self.command_queue.empty():
			return False
		else:
			while not self.command_queue.empty():
				command = self.command_queue.get()
				self.dispatch(command)
			return True

	def shutdown(self):
		if self.vna:
			print("Stopping current task (if any)")
			try:
				self.vna.stop()
			except VNA.VNA_Exception:
				pass
			print("Freeing current task")
			self.vna.deleteTask()
			print("Task freed")


	def run(self):

		error_count = 0
		try:
			while runstate.run:
				try:
					if self.process() == False:
						error_count = 0
						time.sleep(0.01)
				except Exception:
					self.log.error("Exception in VNA interface thread!")
					for line in traceback.format_exc().split("\n"):
						self.log.error(line)

					traceback.print_exc()
					error_count += 0


					# If we can't seem to recover normally, delete and re-create the
					# VNA interface class.
					if error_count > 5:
						self.do_connect(self.connection_params)


		except ThreadExit:
			self.log.info("Thread halting")
		self.shutdown()


def create_thread(vna_no):
	command_queue  = queue.Queue()
	response_queue = queue.Queue()

	vnat = VnaThread(vna_no, command_queue, response_queue)

	proc = threading.Thread(target=vnat.run)
	proc.daemon = True
	proc.start()
	return proc, command_queue, response_queue

def halt_threads():
	runstate.run = False

