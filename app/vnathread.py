
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


		self.active_paths = []

		self.start_f = 1000
		self.stop_f  = 2000
		self.npts_s  = 1024

		self.valid_paths = set(('S11', 'S12', 'S21', 'S22', 'S11 FFT', 'S21 FFT', 'S12 FFT', 'S22 FFT'))

	def dispatch(self, command):
		assert isinstance(command, tuple), "All commands must be a (command, params) tuple!"
		assert len(command) == 2, "All commands must be a (command, params) tuple!"

		command, params = command

		if command == "connect":
			if not self.vna_connected:
				try:
					self.log.info("Connecting to VNA. Please wait while the VNA's embedded calibration data is downloaded.")
					self.vna = VNA.VNA(*params, vna_no=self.vna_no)
					self.vna.set_config(VNA.HOP_45K, VNA.ATTEN_0, freq=[self.start_f, self.stop_f, self.npts_s])

					self.response_queue.put(("connect", True))
					self.log.info("VNA Connected, and embedded calibration retreived.")

				except VNA.VNA_Exception:
					self.log.error("Failure connecting to the hardware!")
					self.log.error("Please try again, or power-cycle the VNA.")
					return



				if self.vna.hasFactoryCalibration():
					self.log.info("VNA Has embedded calibration data")


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
					self.runstate = params
				else:
					if self.vna != None:
						self.log.info("Stopping VNA task")
						self.vna.stop()
						self.runstate = params

		elif command == "calibrate":

			if not self.vna:
				self.log.error("You have to connect to a VNA first!")
				return
			if self.vna.getState() != VNA.TASK_STARTED:
				self.log.error("You must have started the VNA to perform that operation!")
				return

			if params == "clear":
				self.vna.clearCalibration()
				return

			reverseCalMap = {}
			for key, value in VNA.CalibrationStepBOOK.items():
				reverseCalMap[value] = key

			if params not in reverseCalMap:
				self.log.error("Unknown cal step: '%s'", params)
				return
			self.log.info("Measuring cal step value: %s -> %s", params, reverseCalMap[params])
			stepVal = reverseCalMap[params]
			self.vna.measureCalibrationStep(stepVal)
			self.log.info("Cal measured!")
			if self.vna.isCalibrationComplete():
				self.log.info("Calibration is complete!")
			else:
				self.log.info("Not all calibration steps finished yet!")

		elif command == "cal_data":

			if not self.vna:
				self.log.error("You have to connect to a VNA first!")
				return
			if params == "CAL_CLEAR":
				self.vna.clearCalibration()
			elif params == 'CAL_FACTORY':
				self.vna.importFactoryCalibration()
			elif params == "CAL_SAVE":
				if not self.vna.isCalibrationComplete():
					self.log.error("You need a calibration to save!")
					return
				self.vna.save_dll_cal_auto()
			elif params == "CAL_LOAD":
				try:
					self.vna.load_dll_cal_auto()
				except Exception:
					self.log.warning("No on-disk calibration for VNA Found.")
			else:
				self.log.error("Unknown 'cal_data' verb: '%s'", params)

		elif command == "path":

			if not self.vna:
				self.log.error("You have to connect to a VNA first!")
				return

			self.active_paths = []
			for pathval in params:
				if not pathval in self.valid_paths:
					self.log.error("The sample path MUST be one of the set: '%s'. Received: '%s'", self.valid_paths, params)
					return

				self.active_paths.append(pathval)
			self.log.info("Actively measured paths: %s", self.active_paths)


		elif command == "stop":
			runstate.run = False
		elif command == "halt" and params == True:
			raise ThreadExit("Exiting VNA process!")
		elif command == "sweep":
			self.npts_s , self.start_f, self.stop_f = params
		else:
			self.log.error("Unknown command: '%s'", command)
			self.log.error("Command parameters: '%s'", params)


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
		fft_data = fft_data[:output_size/2]
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

		if self.vna.isCalibrationComplete():
			return_values = self.vna.measure_cal()
		else:
			return_values = self.vna.measure_uncal()

		compensated_data = {}

		fft_data = {}
		fft_pts  = []
		frequencies = self.vna.getFrequencies()
		# for path in ["S11", "S22", "S12", "S21", "S11 FFT", "S22 FFT", "S12 FFT", "S21 FFT"]:
		for path in self.active_paths:
			base = path.split()[0]
			key, val = get_param_from_ret(base, return_values)
			if "FFT" in path:
				fft_data_tmp, fft_pts = self.get_fft(val, frequencies)
				fft_data[path] = fft_data_tmp
			else:
				compensated_data[path] = log_mag(val)

		response = {
			'comp_data' : compensated_data,
			'pts'       : frequencies,
			'fft_data'  : fft_data,
			'fft_pts'   : fft_pts,
		}
		self.response_queue.put(("sweep", response))


	def process(self):
		try:
			if self.runstate and self.vna:
				self.get_data()

			if self.command_queue.empty():
				return False
			else:
				while not self.command_queue.empty():
					command = self.command_queue.get()
					self.dispatch(command)
				return True
		except ThreadExit as e:
			raise e
		except Exception as e:
			self.log.error("VNA Exception?")
			for line in traceback.format_exc().split("\n"):
				self.log.error(line)
			raise e

	def shutdown(self):
		if self.vna:
			self.vna.free_task()

def threadProcess(vna_no, command_queue, response_queue):
	vnat = VnaThread(vna_no, command_queue, response_queue)
	try:
		while runstate.run:
			try:
				if vnat.process() == False:
					time.sleep(0.1)

			except ThreadExit as e:
				raise e
			except Exception:
				print("Exception in vna interface thread!")
				traceback.print_exc()
	except ThreadExit:
		print("Thread halting")
	vnat.shutdown()
	print("VNA Interface deallocated.")


def create_thread(vna_no):
	command_queue  = queue.Queue()
	response_queue = queue.Queue()

	proc = threading.Thread(target=threadProcess, args=(vna_no, command_queue, response_queue))
	proc.daemon = True
	proc.start()
	return proc, command_queue, response_queue

def halt_threads():
	runstate.run = False

