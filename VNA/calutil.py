################################################################################
#### calutil.py		--	Common functions for managing VNA calibration 		####
####																		####
####	Usage:																####
####		import calutil													####
####		CAL_ports = [1, 2] # list of ports to be measured on			####
####		CAL_data = calutil.generate_rawDict(CAL_ports, caltype='SOLT')	####
####		...																####
####																		####
####	Author: Abhejit Rajagopal <abhejit@ece.ucsb.edu>					####
####																		####
####	Date: 08.24.2015													####
####																		####
################################################################################
def generate_rawDict(ports, caltype='solt'):
	''' Make a dictionary to store raw signals (e.g. used for VNA calibration)
		~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
		Usage:	ports = [1, 2]
				CAL_data = generate_CALdict(measPorts)

		IN:		ports		--	list of ports to be measured on
				caltype		--	(optional, str) type of structure to create
								choose from:
									- 'solt'	(short, open, load, through
													on each port + crossterms)
									- 'meas'	(custom)

		OUT:	CAL_data		--	dictionary to store raw signals
		~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	'''
	import itertools
	from copy import deepcopy as dcpy
	rawDict = {}

	rawDict['frequencies'] = None

	if caltype.lower()=='solt':

		raw = {'a': None, 'u': None, 'v': None, 'b': None}
		CAL_port = { 's': dcpy(raw), 'o': dcpy(raw), 'l': dcpy(raw) } # short, open, load
		CAL_cross = {'t': dcpy(raw) } # through

		for port in ports:
			rawDict['p'+str(port)] = dcpy(CAL_port) # s-o-l
		#

		crossterms = tuple(itertools.combinations(ports, r=2))
		for term in crossterms:
			rawDict['p'+str(term[0])+'p'+str(term[1])] = dcpy(CAL_cross)
		#
	else:
		print('Sorry, caltype "%s" not supported' % caltype)
		raise('caltypeError')
	#

	return rawDict
####

def catalog_dirpath(dirpath, FILETYPE='csv', CONTEXT=None, DATATYPE='uncal'):
	''' Catalog (VNA) files in a directory, given some filename structure
		~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
		Usage:	dirpath = './8.18_vnaCAL/'
				FILETYPE = 'csv'.lower()	# get csv files
				CONTEXT = None 				# get all contexts
				DATATYPE = 'uncal'.lower()	# get only uncalibrated vals
				catalog = catalog_dirpath(dirpath, FILETYPE, CONTEXT, DATATYPE)

		IN:		dirpath				-- directory to search
				EXTRACT_FILETYPE	-- file-extension to consider
				EXTRACT_CONTEXT		-- comment description in filename
				EXTRACT_DATATYPE	-- type of VNA signals, ('uncal', 'cal')

		OUT:	EXTRACT.files 		-- relative filenames
				EXTRACT.context 	-- file context (comment in filename)
				EXTRACT.ports 		-- ports used
				EXTRACT.terms 		-- termination used
				EXTRACT.datas 		-- signal recorded
		~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	'''
	import os

	EXTRACT_FILETYPE = FILETYPE
	EXTRACT_CONTEXT = CONTEXT
	EXTRACT_DATATYPE = DATATYPE

	EXTRACT_files = []
	EXTRACT_context = []
	EXTRACT_ports = []
	EXTRACT_terms = []
	EXTRACT_datas = []

	files = os.listdir(dirpath)
	for fname in files:
		title = fname.split('.')			# check filetype
		if (len(title)<=1) or (title[len(title)-1].lower()!=EXTRACT_FILETYPE):
			#print('--> wrong filetype')
			continue
		#
		title = title[0]

		description = title.split('_')		# check fileext
		fileCONTEXT = description[0].lower()
		if (EXTRACT_CONTEXT is not None) and (fileCONTEXT!=EXTRACT_CONTEXT):
			#print('--> bad context')
			continue
		#

		if fileCONTEXT=='cal':				# routine for files as "CAL_..."

			pNUM = [int(p) for p in description[1].split('p') if p!=''] # list of ports involved
			pTERM = description[2].lower() # termination of the port (S-O-L-T)
			pDATA = description[3].lower() # which signal was measured

			if EXTRACT_DATATYPE.lower()=='uncal' and pDATA in ['a','u','v','b']:
				pass
			elif EXTRACT_DATATYPE.lower()=='cal' and pDATA in ['s11','s21','s12','s22']:
				pass
			elif EXTRACT_DATATYPE is None:
				pass
			else:
				#print('bad sigfile')
				continue
			#

		EXTRACT_files 	+= [dirpath+fname]
		EXTRACT_context += [fileCONTEXT]
		EXTRACT_ports 	+= [pNUM]
		EXTRACT_terms	+= [pTERM]
		EXTRACT_datas	+= [pDATA]
	#

	from collections import namedtuple
	catalog_files = namedtuple('catalog_files', 'files, context, ports, terms, datas')

	return catalog_files(EXTRACT_files, EXTRACT_context, EXTRACT_ports, EXTRACT_terms, EXTRACT_datas)
####

def read_labview_CSV(fname):
	''' Read in CSV files produced Akela VNA v1.4 (LabView application)
		~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
		IN:		fname			-- relative filepath of a single csv file

		OUT:	file.props		-- Stimulus info, a dictionary of props and vals
				file.data		-- Graph data, a list containing MxN np arrays
				file.data_names	-- Labels corresponding to signals in file.data
		~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	'''
	import csv
	import numpy as np
	from collections import namedtuple

	fileprops = {}
	filedata = []
	filedata_names = []

	with open(fname, newline='') as csvfile:
		spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')

		rowNUM = 0
		for row in spamreader:

			if rowNUM==0: ## figure out which positions will have data in them
				infoIDX = []
				dataIDX = []
				for idx in range(0,len(row)):
					if 'Stimulus' in row[idx]:
						infoIDX = idx # there will be only 1 stimulus section
					elif 'Graph' in row[idx]:
						dataIDX += [idx] # but there will be many graph sections
						filedata.append([]) # append an empty list
					#
				#
				rowNUM += 1
				continue
			#

			## The stimulus section will last 2 columns, and 1+6 more rows
			## The graph sections will last 3 columns (1 with SIGNAME, 2 with data)

			elif rowNUM==1: ## for graph section, get signal names
				for each in dataIDX:
					filedata_names += [ row[each] ]
				#
			#
			elif rowNUM in range(2,8): # Stimulus info, Property-->Value assignment
				fileprops[ row[infoIDX] ] = float(row[infoIDX+1])


			## for graph section, get datapoints
			for idx in range(0,len(dataIDX)):
				filedata[idx].append( [ float(row[dataIDX[idx]+1]), float(row[dataIDX[idx]+2]) ] )
			#

			rowNUM += 1
		#
		for idx in range(0,len(filedata)):
			filedata[idx] = np.asarray(filedata[idx])
		#
	#

	file = namedtuple('labview_csv', 'props, data, data_names') # short, open, load

	return file(fileprops, filedata, filedata_names)
####

def catalog_labview_to_CALdict(catalog, CAL_data):
	''' Read a catalog of Akela VNA v1.4 CSV files, and return an organized dict
		~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
		IN:		catalog			-- a catalog of files, output of catalog_dirpath
				CAL_data		-- an (empty) dict, output of generate_CALdict

		OUT:	CAL_data		-- a filled dict, with data read from catalog
		~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	'''
	from collections import namedtuple
	raw_sig = namedtuple('uncalibrated_measurement', 'signal, ref')
	for idx in range(0,len(catalog.files)):
		fname = catalog.files[idx]
		port = catalog.ports[idx]
		term = catalog.terms[idx]
		data = catalog.datas[idx]

		filedat = read_labview_CSV(fname) # read in file
		if len(filedat.data)!=4: # make sure ref is recorded with signal
			raise('FilesAreNotFormattedCorrectly')
		#

		if idx==0: # get measured frequencies just once (files should be freq alligned)
			CAL_data['frequencies'] = filedat.data[0][:,0]
		#

		signal = filedat.data[0][:,1] + 1j*filedat.data[1][:,1] # "data" recorded
		ref = filedat.data[2][:,1] + 1j*filedat.data[3][:,1]	# corresponding "ref"
		if len(port)==1: # then, this is a port measurement
			CAL_data['p'+str(port[0])][term][data] = raw_sig(signal, ref)
		elif len(port)==2 and term.lower()=='t':
			port.sort() # always list ports in numerical order for cross-terms
			CAL_data['p'+str(port[0])+'p'+str(port[1])][term][data] = raw_sig(signal, ref)
		#
	#

	return CAL_data
####

def generate_CALterms(CAL_data, caltype='solt', rotation=None):
	import numpy as np
	from collections import namedtuple

	if caltype.lower()=='solt':
		#warnings.warn('~~ SOLT-CAL: ONLY 2-PORT NETWORK SUPPORTED~~')
		print('~~ SOLT-CAL: ONLY 2-PORT NETWORK SUPPORTED~~')

		## Extract to 2-port terminology, mimic'ing VNATask.cpp
		tmplist = [	'frequencies',
					'OA', 'OR1', 'OB', 'OR2',
					'SA', 'SR1', 'SB', 'SR2',
					'LA', 'LU', 'LR1',
					'LV', 'LB', 'LR2',
					'TA', 'TU', 'TV', 'TB', 'TR']
		tmplist = ', '.join(tmplist)
		raw_caldata = namedtuple('raw_caldata_SOLT', tmplist)

		frequencies = CAL_data['frequencies']

		# 1-port CAL, OPEN
		OA = CAL_data['p1']['o']['a']['signal']	# port_1
		OR1 = CAL_data['p1']['o']['a']['ref']

		OB = CAL_data['p2']['o']['b']['signal']	# port_2
		OR2 = CAL_data['p2']['o']['b']['ref']

		if rotation and ( 'open' in rotation.keys() ):
			try:
				phaseshift = interpData(rotation['open']['frequencies'], rotation['open']['phase'], frequencies)
				OA = sigutil.phaseshift_signal(OA, -1*phaseshift)
				OB = sigutil.phaseshift_signal(OB, -1*phaseshift)
			except:
				print('oops something went wrong, open--phaseshift generate_CALterms')
			#
		#


		# 1-port CAL, SHORT
		SA = CAL_data['p1']['s']['a']['signal']	# port_1
		SR1 = CAL_data['p1']['s']['a']['ref']

		SB = CAL_data['p2']['s']['b']['signal']	# port_2
		SR2 = CAL_data['p2']['s']['b']['ref']

		if rotation and ( 'short' in rotation.keys() ):
			try:
				phaseshift = interpData(rotation['short']['frequencies'], rotation['short']['phase'], frequencies)
				SA = sigutil.phaseshift_signal(SA, -1*phaseshift)
				SB = sigutil.phaseshift_signal(SB, -1*phaseshift)
			except:
				print('oops something went wrong, short--phaseshift generate_CALterms')
			#
		#


		# 1-port CAL, LOAD
		LA = CAL_data['p1']['l']['a']['signal']	# port_1
		LU = CAL_data['p1']['l']['u']['signal']
		LR1 = CAL_data['p1']['l']['a']['ref']

		LV = CAL_data['p2']['l']['v']['signal']	# port_2
		LB = CAL_data['p2']['l']['b']['signal']
		LR2 = CAL_data['p2']['l']['b']['ref']

		if rotation and ( 'load' in rotation.keys() ):
			try:
				phaseshift = interpData(rotation['load']['frequencies'], rotation['load']['phase'], frequencies)
				LA = sigutil.phaseshift_signal(LA, -1*phaseshift)
				LU = sigutil.phaseshift_signal(LU, -1*phaseshift)
				LV = sigutil.phaseshift_signal(LV, -1*phaseshift)
				LB = sigutil.phaseshift_signal(LB, -1*phaseshift)
			except:
				print('oops something went wrong, load--phaseshift generate_CALterms')
			#
		#


		# 2-port CAL, THROUGH
		TA = CAL_data['p1p2']['t']['a']['signal']	# port_1-2
		TU = CAL_data['p1p2']['t']['u']['signal']
		TV = CAL_data['p1p2']['t']['v']['signal']
		TB = CAL_data['p1p2']['t']['b']['signal']
		TR = CAL_data['p1p2']['t']['a']['ref']

		if rotation and ( 'through' in rotation.keys() ):
			try:
				phaseshift = interpData(rotation['through']['frequencies'], rotation['through']['phase'], frequencies)
				TA = sigutil.phaseshift_signal(TA, -1*phaseshift)
				TU = sigutil.phaseshift_signal(TU, -1*phaseshift)
				TV = sigutil.phaseshift_signal(TV, -1*phaseshift)
				TB = sigutil.phaseshift_signal(TB, -1*phaseshift)
			except:
				print('oops something went wrong, through--phaseshift generate_CALterms')
			#
		#


		# store em!
		caldata = raw_caldata(	frequencies,
								OA, OR1, OB, OR2,
								SA, SR1, SB, SR2,
								LA, LU, LR1,
								LV, LB, LR2,
								TA, TU, TV, TB, TR )


		## Compute the 12 systematic-error terms, like VNATask.cpp
		tmplist = [	'frequencies',
					'EDF', 'EDR', 'ESF', 'ESR',
					'ERF', 'ERR', 'EXF', 'EXR',
					'ELF', 'ELR', 'ETF', 'ETR']
		tmplist = ', '.join(tmplist)
		cal_terms = namedtuple('calterms_SOLT', tmplist)

		# Initial (naive) cal
		S11OpenM = OA / OR1;
		S22OpenM = OB / OR2;

		S11ShortM = SA / SR1;
		S22ShortM = SB / SR2;

		S11LoadM = LA / LR1;
		S21LoadsM = LU / LR1;
		S12LoadsM = LV / LR2;
		S22LoadM = LB / LR2;

		S11ThruM = TA / TR;
		S21ThruM = TU / TR;
		S12ThruM = TV / TR;
		S22ThruM = TB / TR;

		# One-port terms
		EDF = S11LoadM;		#1, fw-directivity
		EDR = S22LoadM;		#7,	rv-directivity

		A = S11ShortM + S11OpenM - EDF - EDF; #2,	fw-portmatch
		B = S11OpenM - S11ShortM;
		ESF = A/B;
		A = S22ShortM + S22OpenM - EDR - EDR; #8,	rv-portmatch
		B = S22OpenM - S22ShortM;
		ESR = A/B;

		A = (S11OpenM - EDF)*(S11ShortM - EDF)*(-2); #3,	fw-reflectiontracking
		B = S11OpenM - S11ShortM;
		ERF = A/B;
		A = (S22OpenM - EDR)*(S22ShortM - EDR)*(-2); #9, 	rv-reflectiontracking
		B = S22OpenM - S22ShortM;
		ERR = A/B;

		# Two-port terms
		EXF = S21LoadsM; #4, 	fw-
		EXR = S12LoadsM; #10, 	rv-

		A = S11ThruM - EDF; #5,	fw-
		B = ERF + ESF*A;
		ELF = A/B;
		A = S22ThruM - EDR; #11, rv-
		B = ERR + ESR*A;
		ELR = A/B;

		A = S21ThruM - EXF; #6,	fw-
		B = ESF*ELF*(-1) + 1;
		ETF = A*B;
		A = S12ThruM - EXR; #12, rv-
		B = ESR*ELR*(-1) + 1;
		ETR = A*B;

		calterms = cal_terms(	frequencies,
								EDF, EDR, ESF, ESR,
								ERF, ERR, EXF, EXR,
								ELF, ELR, ETF, ETR )

		## Make a dictionary, so easy to compare to TDMS files (and to parse)
		calib = {}
		# forward terms
		e00 		= EDF; 	#directivity				reasonable
		e11 		= ESF; 	#portmatch					terrible
		e10e01 		= ERF; 	#reflectiontracking			terrible
		e30 		= EXF; 	#leakage					reasonable
		e22 		= ELF; 	#port2match					terrible
		e10e32 		= ETF; 	#transmissiontracking		terrible

		# reverse terms
		ep33 		= EDR; 	#directivity				reasonable
		ep22 		= ESR; 	#portmatch					terrible
		ep23ep32	= ERR; 	#reflectiontracking			reasonable
		ep03 		= EXR; 	#leakage					reasonable
		ep11 		= ELR; 	#port2match					reasonable
		ep23ep01 	= ETR; 	#transmissiontracking		reasonable

		calib['frequencies']= frequencies
		calib['e00']	 	= e00
		calib['e11'] 		= e11
		calib['e10e01'] 	= e10e01
		calib['e30'] 		= e30
		calib['e22'] 		= e22
		calib['e10e32'] 	= e10e32

		calib['ep33'] 		= ep33
		calib['ep11'] 		= ep11
		calib['ep23ep32'] 	= ep23ep32
		calib['ep03']		= ep03
		calib['ep22'] 		= ep22
		calib['ep23ep01']	= ep23ep01


		#EDF = e00;
		#ESF = e11;
		#ERF = e10e01;
		#EXF = e30;
		#ELF = e22;
		#ETF = e10e32;
		#EDR = ep33;
		#ESR = ep22;
		#ERR = ep23ep32;
		#EXR = ep03;
		#ELR = ep11;
		#ETR = ep23ep01;

	else:
		raise('WrongCALTYPE!!')
	#

	return [caldata, calterms, calib]
####

def read_cal_TDMS(tdms_filename, porttype='2-port'):
	from nptdms import TdmsFile
	tdms_file = TdmsFile(tdms_filename)

	## list groups
	#print(tdms_file.groups())

	## scan properties
	#print(tdms_file.object('Parameters').properties)

	## 2-port data
	twoport = tdms_file.group_channels('2-port')

	cal_paramsR = {}
	cal_paramsI = {}
	for idx in range(0,len(twoport)):
		tmpvar = twoport[idx]
		path = [item.replace('\'', '') for item in tmpvar.path.split('/') if item!='']
		name = path[len(path)-1].split('_')
		term = name[0]
		realORimag = name[1]

		values = tmpvar.data
		bins = tmpvar.time_track()

		if realORimag=='X':
			cal_paramsR[term] = values
		elif realORimag=='Y':
			cal_paramsI[term] = values
		else:
			raise('ParseNameError')
		#
	#

	cal_params = {}
	for each in cal_paramsR.keys():
		cal_params[each] = cal_paramsR[each] + 1j*cal_paramsI[each]
	#

	#from collections import namedtuple
	#return namedtuple('GenericDict', cal_params.keys())(**cal_params)

	return cal_params
####

def interpData(x,y, x_new):
	from scipy.interpolate import interp1d
	from scipy.interpolate import InterpolatedUnivariateSpline as interpUS

	#interpolator = interp1d(x, y, kind='linear')
	interpolator = interpUS(x, y)
	interpolated = interpolator(x_new)

	return interpolated
####

def applyCalibration(calterms, freq, A, U, V, B, R, caltype='solt'):
	import numpy as np
	from collections import namedtuple
	calibrated_params = namedtuple('calibrated_params', 'S11, S21, S12, S22')

	if caltype.lower()=='solt':
		[frequencies, EDF, EDR, ESF, ESR, ERF, ERR, EXF, EXR, ELF, ELR, ETF, ETR] = calterms

		# if length of A/U/V/B is different than that of frequencies, then perform interpolation!
		#hint: interpolate using mag/phase separately, then convert back to real+1j*imag!

		t = [A.shape, U.shape, V.shape, B.shape, R.shape, freq.shape]
		if len(set(t))==1: # then input lengths are the same

			#if freq==frequencies:
			#	# good to go!
			#	pass
			#	# but, interpolate for the hell of it!
			#else:
			#	# perform interpolation
			#	pass
			##

			cal_interpolated = []
			cal_interpolated += [freq]
			for term in calterms[1:]: # skip 'frequencies' array
				term_Real_interp = interpData(frequencies, np.real(term), freq)
				term_Imag_interp = interpData(frequencies, np.imag(term), freq)

				term_interpolated = term_Real_interp + 1j*term_Imag_interp
				cal_interpolated += [term_interpolated]
			#
			[frequencies, EDF, EDR, ESF, ESR, ERF, ERR, EXF, EXR, ELF, ELR, ETF, ETR] = cal_interpolated

		else:
			print('Input signals are not of the same shape.')
			print('A: %s,	U: %s	V: %s	B: %s	R: %s	freq: %s' % tuple(t) )
			raise('InputError')
		#

		# the assumption is that all 4 paths are measured.
		S11M = A/R;
		S21M = U/R;
		S12M = V/R;
		S22M = B/R;

		S11N = (S11M - EDF)/ERF;
		S21N = (S21M - EXF)/ETF;
		S12N = (S12M - EXR)/ETR;
		S22N = (S22M - EDR)/ERR;

		D = (S11N*ESF + 1)*(S22N*ESR + 1) - ELF*ELR*S21N*S12N;

		S11 = (S11N*(S22N*ESR + 1) - ELF*S21N*S12N) / D;
		S21 = S21N*(S22N*(ESR - ELF) + 1) / D;
		S12 = S12N*(S11N*(ESF - ELR) + 1) / D;
		S22 = (S22N*(S11N*ESF + 1) - ELR*S21N*S12N) / D;
	#

	return calibrated_params(S11, S21, S12, S21)
####

def compare_cal(cald, calibration, tdms_filename='/home/abhe/3dsims/VNA/8.18_vnaCAL/cal.tdms', savepath=None):
	import numpy as np
	from matplotlib import pylab as plt

	# python cal
	python_params = calibration['solt'][2]
	frequencies = python_params['frequencies']

	# Load comparison cal
	labview_params = read_cal_TDMS(tdms_filename)

	# Compare calibration (error) terms
	print('	--%s--		--%s--	--%s--		--%s--' % ('me','v1.4','error per f','term'))
	for key in sorted(labview_params.keys()):
		py_term = python_params[key]
		lv_term = labview_params[key]

		error = py_term - lv_term
		avg_error = sum( abs(error) ) / len(error)

		fig = plt.figure()
		plt.plot(frequencies, abs(py_term))
		plt.plot(frequencies, abs(lv_term))
		plt.xlabel('Frequency (Hz)')
		plt.title('%s, with avg error per frequency= %f' % (key, avg_error))
		plt.legend(('computed-py', 'computer-labview'),loc='best')
		if savepath: plt.savefig(savepath+'eterm_'+key+'.svg', format='svg')

		print('power:	%f	%f	%f		%s' % (sum(abs(py_term)), sum(abs(lv_term)), avg_error, key) )
	#
	#plt.show()

	### TESTING
	dirpath = '/home/abhe/3dsims/VNA/8.18_vnaCAL/'
	# get some data first
	test_caldata = generate_rawDict([1, 2], caltype='SOLT')
	test_calibrateddata = catalog_dirpath(dirpath, FILETYPE='csv', CONTEXT=None, DATATYPE='cal')
	test_caldata = catalog_labview_to_CALdict(test_calibrateddata, test_caldata)

	for portconn in test_caldata:
		if portconn=='frequencies':
			continue
		#
		for portterm in test_caldata[portconn]:

			A = cald[portconn][portterm]['a']['signal']
			U = cald[portconn][portterm]['u']['signal']
			V = cald[portconn][portterm]['v']['signal']
			B = cald[portconn][portterm]['b']['signal']
			R = cald[portconn][portterm]['a']['ref']

			print('%s	%s'	% (portconn, portterm))
			[py_S11, py_S21, py_S12, py_S22] = applyCalibration(calibration['solt'][1], frequencies, A, U, V, B, R, caltype='solt')

			try:
				comparison_data = 0
				expected_S11 = test_caldata[portconn][portterm]['s11'].signal
				expected_S21 = test_caldata[portconn][portterm]['s21'].signal
				expected_S12 = test_caldata[portconn][portterm]['s12'].signal
				expected_S22 = test_caldata[portconn][portterm]['s22'].signal
				comparison_data = 1
			except:
				print('--> no comparison data for case:	%s, %s' % (portconn, portterm))
			#

			plt.figure(); plt.title('Measured on %s:%s' % (portconn, portterm))
			plt.subplot(221)
			plt.plot(frequencies, np.log10( abs(py_S11) )); plt.title('%s:%s -- S11' % (portconn, portterm));
			plt.subplot(222)
			plt.plot(frequencies, np.log10( abs(py_S21) )); plt.title('%s:%s -- S21' % (portconn, portterm));
			plt.subplot(223)
			plt.plot(frequencies, np.log10( abs(py_S12) )); plt.title('%s:%s -- S12' % (portconn, portterm));
			plt.subplot(224)
			plt.plot(frequencies, np.log10( abs(py_S22) )); plt.title('%s:%s -- S22' % (portconn, portterm));

			if comparison_data:
				plt.subplot(221)
				plt.plot(frequencies, np.log10( abs(expected_S11) )); plt.title('%s:%s -- S11' % (portconn, portterm));
				plt.subplot(222)
				plt.plot(frequencies, np.log10( abs(expected_S21) )); plt.title('%s:%s -- S21' % (portconn, portterm));
				plt.subplot(223)
				plt.plot(frequencies, np.log10( abs(expected_S12) )); plt.title('%s:%s -- S12' % (portconn, portterm));
				plt.subplot(224)
				plt.plot(frequencies, np.log10( abs(expected_S22) )); plt.title('%s:%s -- S22' % (portconn, portterm));
			#

			if savepath: plt.savefig(savepath+'test_'+portconn+'-'+portterm+'.svg', format='svg')

		#
	#

	return plt
####
