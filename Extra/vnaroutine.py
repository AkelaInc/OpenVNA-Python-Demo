################################################################################
#### vnaroutine.py	--	Common interfacing routines for vnalibrary.py		####
####																		####
####	Usage:																####
####			import vnalibrary as vna									####
####			import vnaroutine as rt										####
####																		####
####		--> See testvna.py for an example procedure						####
####		--> vnalibrary must be imported externally and passed as param	####
####		--> local vnalibrary imported as vnl for constants only			####
####																		####
####	Author: Abhejit Rajagopal <abhejit@ece.ucsb.edu>					####
####	Date: 07.27.2015													####
####																		####
################################################################################
from VNA import vnalibrary as vnl
import numpy as np

#### Convenience ####
# Printing functions
indent=0; tab = lambda indent=indent: '\t'*indent
#message = lambda x: print(x, flush=True, end="")

# Codebooks
ECB = vnl.ErrCodeBOOK
TSB = vnl.TaskStateBOOK
HRB = vnl.HopRateBOOK
ATB = vnl.AttenuationBOOK
RPB = vnl.RFPathBOOK
SPB = vnl.SParameterBOOK
CTB = vnl.CalibrationStepBOOK
########

def setupVNA(vna, DEVICE_IP, DEVICE_IPPort):
	''' Routine when connecting to a VNA
		~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

		IN:		vna				-- vnalibrary instance (currently a module)
				DEVICE_IP		-- string-formatted IP address of VNA hardware
				DEVICE_IPPort 	-- numeric-type IP Port number for connection

		OUT:	**action**		-- establishes connection with VNA on IP:port,
									initializes VNA (downloads hw details),
									queries task state,
									prints info to screen
				task			-- task handle associated with this VNA, which
									should be used for all subsequent control.
	'''

	## Create virtual task
	task = vna.createTask()
	print('Task:	',task)

	## Set IP and Port
	ip_set1 = vna.setIPAddress(task, DEVICE_IP)
	ip_check1 = vna.getIPAddress(task)
	print('IP:	set-',DEVICE_IP,'	errcode',ECB[ip_set1],'	returned-',ip_check1)

	ipport_set1 = vna.setIPPort(task, DEVICE_IPPort)
	ipport_check1 = vna.getIPPort(task)
	print('Port:	set-',DEVICE_IPPort,'		errcode',ECB[ipport_set1],'	returned-',ipport_check1)

	## Open and test connection to VNA
	print('Initializing... (downloads details from device, ETC: ~30secs)')
	init_vna1 = vna.initialize(task)
	print('Initialized:	',ECB[init_vna1])

	state1 = vna.getState(task)
	print('Task State:	',TSB[state1])

	ping1 = vna.utilPingUnit(task)
	print('Responding?	',ECB[ping1])

	## Get hardware details
	hwdetails1 = vna.getHardwareDetails(task)
	print('HW Details:	')
	for each in hwdetails1._fields_:
		print(tab(3)+each[0]+tab(3)+str(getattr(hwdetails1,each[0])))
	#

	return task
####

def setupVNA_config(vna, task, hoprate, attenuation, freq=None):
	''' Routine when setting configuration parameters
		~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

		IN:		vna			-- vnalibrary instance (currently a module)
				task		-- task handle associated with a Akela VNA device
				hoprate		-- frequency hop-rate (a vna.HOP_x object)
				attenuation	-- attenuation on RX for high power (vna.ATTEN_X)
				freq		-- (optional) if set, generate linear sweep as,
									np.arrange(freq[0], freq[1], freq[2])
									which corresponds to MinF, MaxF, #ofF
								This list is subject to modification by
								allowable frequencies on actual hardware

		OUT:	hop_check	-- string describing if hop-rate was set properly
				atten_check	-- string describing if attenuation was set properly
				freq_Num	-- number of frequencies initialized on VNA
				freq_List	-- actual frequencies initalized on VNA
	'''

	## hop rate
	hop_set1 = vna.setHopRate(task, hoprate)
	hop_check1 = vna.getHopRate(task)
	print('Hop:		set-',HRB[vna.HOP_1K.value],'	errcode',ECB[hop_set1],'	returned-',HRB[hop_check1])

	## attenuation
	atten_set1 = vna.setAttenuation(task, attenuation)
	atten_check1 = vna.getAttenuation(task)
	print('Attenuation:	set-',ATB[vna.ATTEN_11.value],'	errcode',ECB[atten_set1],'	returned-',ATB[atten_check1])

	if freq is None:
		print('--> FREQUENCY INFO NOT SET FOR DDS')
		return [HRB[hop_check1], ATB[atten_check1] ]

	## frequencies
	freqMIN = freq[0]
	freqMAX = freq[1]
	freqNUM = freq[2]
	freq_setL = vna.utilGenerateLinearSweep(task, freqMIN, freqMAX, freqNUM)
	freq_checkN = vna.getNumberOfFrequencies(task)
	freq_checkL = vna.getFrequencies(task, freq_checkN)
	print('Frequencies:	errcode',ECB[freq_setL])
	print('		checkN-',freq_checkN)
	print('		checkL-\n',freq_checkL)

	return [HRB[hop_check1], ATB[atten_check1], freq_checkN, freq_checkL]
####

def setupVNA_start(vna, task):
	''' Routine to initialize VNA measurement, after config
		~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

		IN:		vna			-- vnalibrary instance (currently a module)
				task		-- task handle associated with a Akela VNA device

		OUT:	error_code	-- string describing if task started properly
				task_state	-- string describing the state of the VNA
	'''
	# start
	started1 = vna.start(task) # should do when all set up, check ECB[started]
	print('Started?	',ECB[started1])
	state2 = vna.getState(task)
	print('Task State:	',TSB[state2])
	return [ECB[started1], TSB[state2]]
####

def setupVNA_vars(vna, freq_N):
	''' Routine to initialize ComplexData memory objects
		~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

		IN:		vna			-- vnalibrary instance (currently a module)
				freq_N		-- number of frequency bins to store per measurement

		OUT:	T1R1,		-- empty C-type data objects suitable for passing to
				T1R2,			the measurement routines. these will then be
				T2R1,			filled with numpy arrays holding the I-Q values
				T2R3,			produced by the VNA for each frequency in the
				Ref_T1R1,		CW-SF sweep.
				Ref_T2R1,
				Ref_T1R2,
				Ref_T2R2
	'''
	# setup vars
	print('Setting up vars and allocating memory...')
	T1R1 = vna.ComplexData(freq_N)
	T1R2 = vna.ComplexData(freq_N)
	T2R1 = vna.ComplexData(freq_N)
	T2R2 = vna.ComplexData(freq_N)
	Ref_T1R1 = vna.ComplexData(freq_N)
	Ref_T1R2 = vna.ComplexData(freq_N)
	Ref_T2R1 = vna.ComplexData(freq_N)
	Ref_T2R2 = vna.ComplexData(freq_N)

	return [T1R1, T1R2, T2R1, T2R2, Ref_T1R1, Ref_T2R1, Ref_T1R2, Ref_T2R2]
####

def measureVNA_uncal(vna, task, paths, T1R1, T1R2, T2R1, T2R2, Ref_T1R1, Ref_T2R1, Ref_T1R2, Ref_T2R2, verbosity=0):
	''' Routine to measure uncalibrated I-Q using an configured VNA task
		~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

		IN:		vna			-- vnalibrary instance (currently a module)
				task		-- task handle associated with a Akela VNA device
				paths		-- a list of paths to measure (vna.PATH_X objects)
				T1R1,		-- C-type data objects suitable for passing to
				T1R2,			the measurement routines. these will then be
				T2R1,			filled with numpy arrays holding the I-Q values
				T2R3,			produced by the VNA for each frequency in the
				Ref_T1R1,		CW-SF sweep.
				Ref_T2R1,
				Ref_T1R2,
				Ref_T2R2

		OUT:
				T1R1,		-- C-type data objects holding numpy arrays
				T1R2,			filled with I-Q values from the frequency sweep
				T2R1,
				T2R3,
				Ref_T1R1,
				Ref_T2R1,
				Ref_T1R2,
				Ref_T2R2
	'''
	if verbosity >= 0:
		print('Measuring...',flush=True)
	elif verbosity == -1:
		print('.',end='',flush=True)
	#
	measure_check = []
	return_values = []
	indent = 1
	for each in paths:

		# this section depends on your setup vars
		select_path_str = RPB[each.value].replace('PATH_','')
		select_path = locals()[select_path_str]
		select_ref_str = 'Ref_'+select_path_str
		select_ref = locals()[select_ref_str]

		if verbosity >= 2:
			print(tab(indent)+'B4:	'+select_path_str+'-I'+'\n', tab(1),np.asarray(select_path.I.contents),'\n')
			print(tab(indent)+'B4:	'+select_path_str+'-Q'+'\n', tab(1),np.asarray(select_path.Q.contents),'\n')
			print(tab(indent)+'B4:	'+select_ref_str+'-I'+'\n', tab(1),np.asarray(select_ref.I.contents),'\n')
			print(tab(indent)+'B4:	'+select_ref_str+'-Q'+'\n', tab(1),np.asarray(select_ref.Q.contents),'\n')
		#

		tmp_measure = vna.measureUncalibrated(task, each, T1R1,T1R2,T2R1,T2R2,select_ref) # Measure each path + ref

		if verbosity >= 0:
			print(tab(indent)+'Measurement status for '+select_path_str+':'+tab(1)+ECB[tmp_measure]+'\n')
			measure_check.append(ECB[tmp_measure])
		#
		toreturn = [np.asarray(select_path.I.contents), np.asarray(select_path.Q.contents), np.asarray(select_ref.I.contents), np.asarray(select_ref.Q.contents)]
		return_values.append(toreturn)

		if verbosity >= 1:
			print(tab(indent)+'AFTR:	'+select_path_str+'-I'+'\n', tab(1),np.asarray(select_path.I.contents),'\n')
			print(tab(indent)+'AFTR:	'+select_path_str+'-Q'+'\n', tab(1),np.asarray(select_path.Q.contents),'\n')
			print(tab(indent)+'AFTR:	'+select_ref_str+'-I'+'\n', tab(1),np.asarray(select_ref.I.contents),'\n')
			print(tab(indent)+'AFTR:	'+select_ref_str+'-Q'+'\n', tab(1),np.asarray(select_ref.Q.contents),'\n')
		#
	#

	return [measure_check, return_values]
####
