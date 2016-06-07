# ######################################################################### #
#  vnalibrary.py	--	Python module wrapping VNADLL						#
# 																			#
#  	Adapted from /libradar/vnadll/akela_vna_dll.h							#
# 																			#
# 																			#
# 	Author: Abhejit Rajagopal <abhejit@ece.ucsb.edu>						#
# 			Connor Wolf <cwolf@akelainc.com>								#
# 																			#
# 	Date: 07.23.2015														#
# 																			#
# ######################################################################### #
import ctypes as ct
import os.path
import platform
import sys

def get_search_paths():
	''' Build a list of search paths where we should look for the
	VNA DLL.

	'''
	locations = []
	loc = os.path.dirname(os.path.abspath(__file__))
	up = os.path.abspath(os.path.join(loc, "../"))
	build_dir_1 = os.path.abspath(os.path.join(loc, "../../../x64/Debug/"))
	build_dir_2 = os.path.abspath(os.path.join(loc, "../../../x64/Release/"))

	# Scons build dir
	build_dir_3 = os.path.abspath(os.path.join(loc, "../../../build/vnadll/"))

	build_dir_1 = os.path.abspath(os.path.join(loc, "../../../../x64/Debug/"))
	build_dir_2 = os.path.abspath(os.path.join(loc, "../../../../x64/Release/"))
	locations.append(loc)
	locations.append(up)
	locations.append(build_dir_1)
	locations.append(build_dir_2)
	locations.append(build_dir_3)

	split_on = {"Linux" : ":", "Windows" : ";"}
	split = os.environ['PATH'].split(split_on[platform.system()])

	if getattr(sys, 'frozen', False):
		# we are running in a |PyInstaller| bundle
		locations.append(sys._MEIPASS)

	# Validate and canonize the various paths
	split = [os.path.abspath(item) for item in split if os.path.exists(item)]

	return locations+split


def find_dll():
	''' Search both the local working directory, and the
	system environment (`PATH`) for the DLL/SO.
	'''

	dll_lut = {"Linux" : "libvnadll.so", "Windows" : "vnadll.dll"}

	plat = platform.system()

	if plat in dll_lut:
		dll_name = dll_lut[plat]
	else:
		raise RuntimeError("Unknown platform: '%s'" % platform.system())

	locations = get_search_paths()

	for location in locations:
		fq_dll_path = os.path.join(location, dll_name)
		if os.path.exists(fq_dll_path):
			print("Found DLL at path %s" % fq_dll_path)
			return fq_dll_path
	for fpath in locations:
		print("	", fpath)
	raise ValueError("Could not find DLL/SO! Searched paths: '%s'" % locations)

dll = ct.CDLL(find_dll())

import time
import numpy as np

from . import vnaexceptions


## \addtogroup Python-Basic-API
#
#  \section base-api-brief Low-Level VNA API Interface
#
# @authors Abhejit Rajagopal <abhejit@ece.ucsb.edu>, Connor Wolf <cwolf@akelainc.com>
#
#  This is the "basic" API wrapper for the AKELA VNA
#  interface. It's basically a thin layer over the underlying C API, doing
#  only basic type conversion of some of the more involved data-structures.
#
#  Functionally, all calls here act almost identically to how the corresponding
#  functions in the \ref C-API behave.
#
#  If you want a cleaner, more pythonic interface, please use the \ref Python-OOP-API
#  class, which tries to hide the underlying complexity as much as possible.
#
#
# @{


## \addtogroup ErrorCodes-Py
# Proxy values for underlying C values from \ref ErrorCodes.
#
# Values should be treated as immutable, and only used as parameters
# to pass into DLL cals.
#
# While the underlying type is numeric, no assumptions can or should be made about the
# actual integer value, as it may change with DLL updates. Only equality
# operations should be assumed to be valid for any comparisons or
# value checks.
#
# Note that Doxygen incorrectly identifies the type of these values
# as `tuple`, as the ctypes library does some runtime type munging that
# doxygen doesn't understand.
# @{
TaskHandle = ct.c_void_p # anonymous typedef

ErrCode = ct.c_int #typedef
ERR_OK 					= ErrCode.in_dll(dll, "ERR_OK").value
ERR_BAD_ATTEN 			= ErrCode.in_dll(dll, "ERR_BAD_ATTEN").value
ERR_BAD_CAL 			= ErrCode.in_dll(dll, "ERR_BAD_CAL").value
ERR_BAD_HANDLE			= ErrCode.in_dll(dll, "ERR_BAD_HANDLE").value
ERR_BAD_HOP 			= ErrCode.in_dll(dll, "ERR_BAD_HOP").value
ERR_BAD_PATH 			= ErrCode.in_dll(dll, "ERR_BAD_PATH").value
ERR_BAD_PROM 			= ErrCode.in_dll(dll, "ERR_BAD_PROM").value
ERR_BYTES 				= ErrCode.in_dll(dll, "ERR_BYTES").value
ERR_FREQ_OUT_OF_BOUNDS 	= ErrCode.in_dll(dll, "ERR_FREQ_OUT_OF_BOUNDS").value
ERR_INTERRUPTED 		= ErrCode.in_dll(dll, "ERR_INTERRUPTED").value
ERR_NO_RESPONSE 		= ErrCode.in_dll(dll, "ERR_NO_RESPONSE").value
ERR_MISSING_IP 			= ErrCode.in_dll(dll, "ERR_MISSING_IP").value
ERR_MISSING_PORT 		= ErrCode.in_dll(dll, "ERR_MISSING_PORT").value
ERR_MISSING_HOP 		= ErrCode.in_dll(dll, "ERR_MISSING_HOP").value
ERR_MISSING_ATTEN 		= ErrCode.in_dll(dll, "ERR_MISSING_ATTEN").value
ERR_MISSING_FREQS 		= ErrCode.in_dll(dll, "ERR_MISSING_FREQS").value
ERR_PROG_OVERFLOW 		= ErrCode.in_dll(dll, "ERR_PROG_OVERFLOW").value
ERR_SOCKET 				= ErrCode.in_dll(dll, "ERR_SOCKET").value
ERR_TOO_MANY_POINTS 	= ErrCode.in_dll(dll, "ERR_TOO_MANY_POINTS").value
ERR_WRONG_STATE 		= ErrCode.in_dll(dll, "ERR_WRONG_STATE").value

## @}


## \addtogroup ErrorExceptionMap-Py
#
# This maps error return codes to the corresponding python exception.
#
#
# @{

Exception_Map = {
	ERR_BAD_ATTEN          : vnaexceptions.VNA_Exception_Bad_Atten,
	ERR_BAD_CAL            : vnaexceptions.VNA_Exception_Bad_Cal,
	ERR_BAD_HANDLE         : vnaexceptions.VNA_Exception_Bad_Handle,
	ERR_BAD_HOP            : vnaexceptions.VNA_Exception_Bad_Hop,
	ERR_BAD_PATH           : vnaexceptions.VNA_Exception_Bad_Path,
	ERR_BAD_PROM           : vnaexceptions.VNA_Exception_Bad_Prom,
	ERR_BYTES              : vnaexceptions.VNA_Exception_Bytes,
	ERR_FREQ_OUT_OF_BOUNDS : vnaexceptions.VNA_Exception_Freq_Out_Of_Bounds,
	ERR_INTERRUPTED        : vnaexceptions.VNA_Exception_Interrupted,
	ERR_NO_RESPONSE        : vnaexceptions.VNA_Exception_No_Response,
	ERR_MISSING_IP         : vnaexceptions.VNA_Exception_Missing_Ip,
	ERR_MISSING_PORT       : vnaexceptions.VNA_Exception_Missing_Port,
	ERR_MISSING_HOP        : vnaexceptions.VNA_Exception_Missing_Hop,
	ERR_MISSING_ATTEN      : vnaexceptions.VNA_Exception_Missing_Atten,
	ERR_MISSING_FREQS      : vnaexceptions.VNA_Exception_Missing_Freqs,
	ERR_PROG_OVERFLOW      : vnaexceptions.VNA_Exception_Prog_Overflow,
	ERR_SOCKET             : vnaexceptions.VNA_Exception_Socket,
	ERR_TOO_MANY_POINTS    : vnaexceptions.VNA_Exception_Too_Many_Points,
	ERR_WRONG_STATE        : vnaexceptions.VNA_Exception_Wrong_State,

}

def handleReturnCode(code, message = ""):
	''' Given a VNA-DLL return code, raise the corresponding
	python exception if the return-code is not ERR_OK.


	Raises:

	One of the child-classes of \ref VNA_Exception as dictated
	by the value of `code` (if `code` corresponds to an exception).

	Otherwise, it simply returns with no exception thrown.

	Args:
		code - The return code from a DLL-call.
		message - Optional, description added to raised exception.

	Returns:
		Nothing.

	---


	'''


	if code in Exception_Map:
		raise Exception_Map[code](message)


## @}

## \addtogroup ErrorCodes-Py
# Proxy values for underlying C values from \ref ErrorCodes.
#
# Values should be treated as immutable, and only used as parameters
# to pass into DLL cals.
#
# While the underlying type is numeric, no assumptions can or should be made about the
# actual integer value, as it may change with DLL updates. Only equality
# operations should be assumed to be valid for any comparisons or
# value checks.
#
# Note that Doxygen incorrectly identifies the type of these values
# as `tuple`, as the ctypes library does some runtime type munging that
# doxygen doesn't understand.
# @{
## Dictionary for mapping ERR_nnn values to human-readable string representations of the error-code.
ErrCodeBOOK = 	{
					ERR_OK                 : 'ERR_OK',
					ERR_BAD_ATTEN          : 'ERR_BAD_ATTEN',
					ERR_BAD_CAL            : 'ERR_BAD_CAL',
					ERR_BAD_HANDLE         : 'ERR_BAD_HANDLE',
					ERR_BAD_HOP            : 'ERR_BAD_HOP',
					ERR_BAD_PATH           : 'ERR_BAD_PATH',
					ERR_BAD_PROM           : 'ERR_BAD_PROM',
					ERR_BYTES              : 'ERR_BYTES',
					ERR_FREQ_OUT_OF_BOUNDS : 'ERR_FREQ_OUT_OF_BOUNDS',
					ERR_INTERRUPTED        : 'ERR_INTERRUPTED',
					ERR_NO_RESPONSE        : 'ERR_NO_RESPONSE',
					ERR_MISSING_IP         : 'ERR_MISSING_IP',
					ERR_MISSING_PORT       : 'ERR_MISSING_PORT',
					ERR_MISSING_HOP        : 'ERR_MISSING_HOP',
					ERR_MISSING_ATTEN      : 'ERR_MISSING_ATTEN',
					ERR_MISSING_FREQS      : 'ERR_MISSING_FREQS',
					ERR_PROG_OVERFLOW      : 'ERR_PROG_OVERFLOW',
					ERR_SOCKET             : 'ERR_SOCKET',
					ERR_TOO_MANY_POINTS    : 'ERR_TOO_MANY_POINTS',
					ERR_WRONG_STATE        : 'ERR_WRONG_STATE'
				}

## @}


## \addtogroup HopRateSettings-Py
# Proxy values for underlying C values from \ref HopRateSettings.
#
# Values should be treated as immutable, and only used as parameters
# to pass into DLL cals.
#
# While the underlying type is numeric, no assumptions can or should be made about the
# actual integer value, as it may change with DLL updates. Only equality
# operations should be assumed to be valid for any comparisons or
# value checks.
#
# Note that Doxygen incorrectly identifies the type of these values
# as `tuple`, as the ctypes library does some runtime type munging that
# doxygen doesn't understand.
# @{
HopRate = ct.c_int #typedef
HOP_UNDEFINED 	= HopRate.in_dll(dll, "HOP_UNDEFINED").value
#HOP_90K		= HopRate.in_dll(dll, "HOP_90K").value # This rate is currently unsupported
HOP_45K			= HopRate.in_dll(dll, "HOP_45K").value
HOP_30K 		= HopRate.in_dll(dll, "HOP_30K").value
HOP_15K 		= HopRate.in_dll(dll, "HOP_15K").value
HOP_7K 			= HopRate.in_dll(dll, "HOP_7K").value
HOP_3K 			= HopRate.in_dll(dll, "HOP_3K").value
HOP_2K 			= HopRate.in_dll(dll, "HOP_2K").value
HOP_1K 			= HopRate.in_dll(dll, "HOP_1K").value
HOP_550 		= HopRate.in_dll(dll, "HOP_550").value
HOP_312 		= HopRate.in_dll(dll, "HOP_312").value
HOP_156 		= HopRate.in_dll(dll, "HOP_156").value
HOP_78 			= HopRate.in_dll(dll, "HOP_78").value
HOP_39 			= HopRate.in_dll(dll, "HOP_39").value
HOP_20 			= HopRate.in_dll(dll, "HOP_20").value

## Dictionary for mapping hop-rate values to human-readable string representations of the value.
HopRateBOOK =	{
				HOP_UNDEFINED : 'HOP_UNDEFINED',
				#HOP_90K       : 'HOP_90K',
				HOP_45K       :  'HOP_45K',
				HOP_30K       :  'HOP_30K',
				HOP_15K       :  'HOP_15K',
				HOP_7K        :  'HOP_7K',
				HOP_3K        :  'HOP_3K',
				HOP_2K        :  'HOP_2K',
				HOP_1K        :  'HOP_1K',
				HOP_550       :  'HOP_550',
				HOP_312       :  'HOP_312',
				HOP_156       :  'HOP_156',
				HOP_78        :  'HOP_78',
				HOP_39        :  'HOP_39',
				HOP_20        :  'HOP_20'
			}

## @}


## \addtogroup AttenuationSettings-Py
# Proxy values for underlying C values from \ref AttenuationSettings.
#
# Values should be treated as immutable, and only used as parameters
# to pass into DLL cals.
#
# While the underlying type is numeric, no assumptions can or should be made about the
# actual integer value, as it may change with DLL updates. Only equality
# operations should be assumed to be valid for any comparisons or
# value checks.
#
# Note that Doxygen incorrectly identifies the type of these values
# as `tuple`, as the ctypes library does some runtime type munging that
# doxygen doesn't understand.
# @{
#
Attenuation = ct.c_int #typedef
ATTEN_UNDEFINED	= Attenuation.in_dll(dll, "ATTEN_UNDEFINED").value
ATTEN_0 		= Attenuation.in_dll(dll, "ATTEN_0").value
ATTEN_1 		= Attenuation.in_dll(dll, "ATTEN_1").value
ATTEN_2 		= Attenuation.in_dll(dll, "ATTEN_2").value
ATTEN_3 		= Attenuation.in_dll(dll, "ATTEN_3").value
ATTEN_4 		= Attenuation.in_dll(dll, "ATTEN_4").value
ATTEN_5 		= Attenuation.in_dll(dll, "ATTEN_5").value
ATTEN_6 		= Attenuation.in_dll(dll, "ATTEN_6").value
ATTEN_7 		= Attenuation.in_dll(dll, "ATTEN_7").value
ATTEN_8 		= Attenuation.in_dll(dll, "ATTEN_8").value
ATTEN_9 		= Attenuation.in_dll(dll, "ATTEN_9").value
ATTEN_10 		= Attenuation.in_dll(dll, "ATTEN_10").value
ATTEN_11 		= Attenuation.in_dll(dll, "ATTEN_11").value
ATTEN_12 		= Attenuation.in_dll(dll, "ATTEN_12").value
ATTEN_13 		= Attenuation.in_dll(dll, "ATTEN_13").value
ATTEN_14 		= Attenuation.in_dll(dll, "ATTEN_14").value
ATTEN_15 		= Attenuation.in_dll(dll, "ATTEN_15").value
ATTEN_16	 	= Attenuation.in_dll(dll, "ATTEN_16").value
ATTEN_17 		= Attenuation.in_dll(dll, "ATTEN_17").value
ATTEN_18 		= Attenuation.in_dll(dll, "ATTEN_18").value
ATTEN_19 		= Attenuation.in_dll(dll, "ATTEN_19").value
ATTEN_20 		= Attenuation.in_dll(dll, "ATTEN_20").value
ATTEN_21 		= Attenuation.in_dll(dll, "ATTEN_21").value
ATTEN_22 		= Attenuation.in_dll(dll, "ATTEN_22").value
ATTEN_23 		= Attenuation.in_dll(dll, "ATTEN_23").value
ATTEN_24 		= Attenuation.in_dll(dll, "ATTEN_24").value
ATTEN_25 		= Attenuation.in_dll(dll, "ATTEN_25").value
ATTEN_26 		= Attenuation.in_dll(dll, "ATTEN_26").value
ATTEN_27 		= Attenuation.in_dll(dll, "ATTEN_27").value
ATTEN_28 		= Attenuation.in_dll(dll, "ATTEN_28").value
ATTEN_29 		= Attenuation.in_dll(dll, "ATTEN_29").value
ATTEN_30 		= Attenuation.in_dll(dll, "ATTEN_30").value
ATTEN_31 		= Attenuation.in_dll(dll, "ATTEN_31").value

## Dictionary for mapping attenuation values to human-readable string representations of the value.
AttenuationBOOK = 	{
					ATTEN_UNDEFINED :'ATTEN_UNDEFINED',
					ATTEN_0         :'ATTEN_0',
					ATTEN_0         :'ATTEN_0',
					ATTEN_1         :'ATTEN_1',
					ATTEN_2         :'ATTEN_2',
					ATTEN_3         :'ATTEN_3',
					ATTEN_4         :'ATTEN_4',
					ATTEN_5         :'ATTEN_5',
					ATTEN_6         :'ATTEN_6',
					ATTEN_7         :'ATTEN_7',
					ATTEN_8         :'ATTEN_8',
					ATTEN_9         :'ATTEN_9',
					ATTEN_10        :'ATTEN_10',
					ATTEN_11        :'ATTEN_11',
					ATTEN_12        :'ATTEN_12',
					ATTEN_13        :'ATTEN_13',
					ATTEN_14        :'ATTEN_14',
					ATTEN_15        :'ATTEN_15',
					ATTEN_16        :'ATTEN_16',
					ATTEN_17        :'ATTEN_17',
					ATTEN_18        :'ATTEN_18',
					ATTEN_19        :'ATTEN_19',
					ATTEN_20        :'ATTEN_20',
					ATTEN_21        :'ATTEN_21',
					ATTEN_22        :'ATTEN_22',
					ATTEN_23        :'ATTEN_23',
					ATTEN_24        :'ATTEN_24',
					ATTEN_25        :'ATTEN_25',
					ATTEN_26        :'ATTEN_26',
					ATTEN_27        :'ATTEN_27',
					ATTEN_28        :'ATTEN_28',
					ATTEN_29        :'ATTEN_29',
					ATTEN_30        :'ATTEN_30',
					ATTEN_31        :'ATTEN_31'
				}

## @}


## \addtogroup TaskState-Py
# Proxy values for underlying C values from \ref TaskState.
#
# Values should be treated as immutable, and only used as parameters
# to pass into DLL cals.
#
# While the underlying type is numeric, no assumptions can or should be made about the
# actual integer value, as it may change with DLL updates. Only equality
# operations should be assumed to be valid for any comparisons or
# value checks.
#
# Note that Doxygen incorrectly identifies the type of these values
# as `tuple`, as the ctypes library does some runtime type munging that
# doxygen doesn't understand.
# @{
TaskState = ct.c_int #typedef
TASK_UNINITIALIZED	= TaskState.in_dll(dll, "TASK_UNINITIALIZED").value
TASK_STOPPED		= TaskState.in_dll(dll, "TASK_STOPPED").value
TASK_STARTED 		= TaskState.in_dll(dll, "TASK_STARTED").value

## Dictionary for mapping task-rates values to human-readable string representations of the value.
TaskStateBOOK =	{
					TASK_UNINITIALIZED : 'TASK_UNINITIALIZED',
					TASK_STOPPED       : 'TASK_STOPPED',
					TASK_STARTED       : 'TASK_STARTED'
				}

## @}


## CTypes proxy for the \ref HardwareDetails struct
#
# Members:
#
#    Member Name                |            Member Function                                  |
#   ----------------------------|-------------------------------------------------------------|
#   `minimum_frequency`         | ct.c_int proxy for eponymous member in \ref HardwareDetails |
#   `maximum_frequency`         | ct.c_int proxy for eponymous member in \ref HardwareDetails |
#   `maximum_points`            | ct.c_int proxy for eponymous member in \ref HardwareDetails |
#   `serial_number`             | ct.c_int proxy for eponymous member in \ref HardwareDetails |
#   `band_boundaries`           | ct.c_int proxy for eponymous member in \ref HardwareDetails |
#   `number_of_band_boundaries` | ct.c_int proxy for eponymous member in \ref HardwareDetails |
#
#
class HardwareDetails(ct.Structure):
	_fields_ = 	[
					("minimum_frequency", ct.c_int),
					("maximum_frequency", ct.c_int),
					("maximum_points", ct.c_int),
					("serial_number", ct.c_int),
					("band_boundaries", ct.c_int*8), #Highest frequency first
					("number_of_band_boundaries", ct.c_int)
				]

	def to_dict(self):
		ret = {}

		ret["minimum_frequency"]         = self.minimum_frequency
		ret["maximum_frequency"]         = self.maximum_frequency
		ret["maximum_points"]            = self.maximum_points
		ret["serial_number"]             = self.serial_number
		ret["band_boundaries"]           = self.band_boundaries[:]
		ret["number_of_band_boundaries"] = self.number_of_band_boundaries

		return ret



## \addtogroup CalibrationStepSelector-Py
# Proxy values for underlying C values from \ref CalibrationStep.
#
# Values should be treated as immutable, and only used as parameters
# to pass into DLL cals.
#
# While the underlying type is numeric, no assumptions can or should be made about the
# actual integer value, as it may change with DLL updates. Only equality
# operations should be assumed to be valid for any comparisons or
# value checks.
#
# Note that Doxygen incorrectly identifies the type of these values
# as `tuple`, as the ctypes library does some runtime type munging that
# doxygen doesn't understand.
# @{


CalibrationStep = ct.c_int #typedef
STEP_P1_OPEN  = CalibrationStep.in_dll(dll, "STEP_P1_OPEN").value
STEP_P1_SHORT = CalibrationStep.in_dll(dll, "STEP_P1_SHORT").value
STEP_P1_LOAD  = CalibrationStep.in_dll(dll, "STEP_P1_LOAD").value
STEP_P2_OPEN  = CalibrationStep.in_dll(dll, "STEP_P2_OPEN").value
STEP_P2_SHORT = CalibrationStep.in_dll(dll, "STEP_P2_SHORT").value
STEP_P2_LOAD  = CalibrationStep.in_dll(dll, "STEP_P2_LOAD").value
STEP_THRU     = CalibrationStep.in_dll(dll, "STEP_THRU").value
CalibrationStepBOOK =	{
							STEP_P1_OPEN  : 'STEP_P1_OPEN',
							STEP_P1_SHORT : 'STEP_P1_SHORT',
							STEP_P1_LOAD  : 'STEP_P1_LOAD',
							STEP_P2_OPEN  : 'STEP_P2_OPEN',
							STEP_P2_SHORT : 'STEP_P2_SHORT',
							STEP_P2_LOAD  : 'STEP_P2_LOAD',
							STEP_THRU     : 'STEP_THRU'
						}


## @}

__doubleArrayDefinitions = {}
__complexDataDefinitions = {}


# The following two-## comment has to be present.
# it works around a bug in doxypypy
##
def ComplexDataFactory(data_len):
	''' Factory function for creating ctypes-compatible
	\ref ComplexData array class definitions.

	Due to some vagaries of how the parameter-type validation works in
	ctypes, this must be a factory function rather then a class definition.

	This factory uses some global-state tricks to ensure that only one
	instance of each array-length-n class definition exists, which is required
	to keep ctypes happy.

	This function is idempotent.

	Args:
		data_len - Length of complex data array (integer)

	Returns:
		Class definition instance for a ComplexData() class
		with length `data_len`

	This function will generally be chain-called, e.g.:

	`ComplexDataFactory(5)()`

	The first call `(5)` creates the class definition
	for a ComplexData array with a length of 5. The second
	call `()` instantiates a instance of that class definition.

	Idempotency guarantees that `ComplexDataFactory(5) == ComplexDataFactory(5)`,
	as if there was not some internal state, it would construct two *different*
	class defintions with the same properties, and then the parameter/return
	type checking in `ctypes` would throw errors as the classes would not
	compare as equal.

	'''

	if data_len in __complexDataDefinitions:
		return __complexDataDefinitions[data_len]

	assert (data_len > 0), "Complex data arrays have to have a non-zero length!"
	name = "ComplexData_sz_%s_tm_%s" % (data_len, int(time.time()*1000000))

	class ComplexData(ct.Structure):

		_fields_ =	[
						("I", ct.POINTER( (ct.c_double * data_len))),
						("Q", ct.POINTER( (ct.c_double * data_len)))
					]

		def __init__(self, real=None, imag=None):
			# I/Q Data arrays
			if real is not None:
				bufferI = (ct.c_double * data_len)(*real)
			else:
				bufferI = (ct.c_double * data_len)()

			if imag is not None:
				bufferQ = (ct.c_double * data_len)(*imag)
			else:
				bufferQ = (ct.c_double * data_len)()

			# and pointers to them
			self.I = ct.pointer(bufferI)
			self.Q = ct.pointer(bufferQ)

		def __repr__(self):
			ret = "<Ctypes-compatible ComplexData Array container. I:'%s', Q:'%s'>" % (
				self.I.contents[:], self.Q.contents[:]
				)
			return ret


		def toArray(self):
			# Unpack the ctypes arrays
			arr = np.array([self.I.contents[:], self.Q.contents[:]])

			# And convert the two columns to a complex number
			arr = np.array(arr[0,...] + 1j * arr[1,...])
			return arr


	ComplexData.__name__ = name

	__complexDataDefinitions[data_len] = ComplexData
	return ComplexData

def ComplexDataArrayFromNumpyArray(np_arr):
	assert len(np_arr.shape) == 1

	# The len() of a 1-dimentional array is the equivalent of
	# array.shape[0]
	cdat = ComplexDataFactory(len(np_arr))(np_arr.real, np_arr.imag)
	return cdat


# The following two-## comment has to be present.
# it works around a bug in doxypypy
##
def DoubleArrayFactory(data_len):
	''' Factory function for creating ctypes-compatible
	double-array class definitions.

	Due to some vagaries of how the parameter-type validation works in
	ctypes, this must be a factory function rather then a class definition.

	This factory uses some global-state tricks to ensure that only one
	instance of each array-length-n class definition exists, which is required
	to keep ctypes happy.

	This function is idempotent.

	Args:
		data_len - Length of data array (integer)

	Returns:
		Class definition instance for a ctypes.c_double_Array_nnn() class
		with length `data_len`

	This function will generally be chain-called, e.g.:

	`DoubleArrayFactory(5)()`

	The first call `(5)` creates the class definition
	for a double array with a length of 5. The second
	call `()` instantiates a instance of that class definition.

	Idempotency guarantees that `DoubleArrayFactory(5) == DoubleArrayFactory(5)`,
	as if there was not some internal state, it would construct two *different*
	class defintions with the same properties, and then the parameter/return
	type checking in `ctypes` would throw errors as the classes would not
	compare as equal.

	This function, and \ref ComplexDataFactory() are basically identical
	in function, except the type they return.

	'''

	if data_len in __doubleArrayDefinitions:
		return __doubleArrayDefinitions[data_len]

	assert (data_len > 0), "Double arrays have to have a non-zero length!"
	name = "DoubleArray_sz_%s_tm_%s" % (data_len, int(time.time()*1000000))

	doubleArray = ct.c_double*data_len
	doubleArray.__name__ = name

	__doubleArrayDefinitions[data_len] = doubleArray
	return doubleArray





# -------------------------OVERVIEW---------------------------------------
# ------------------------------------------------------------------------
# A Task exists in one of three states:
# 1. Uninitialized (TASK_UNINITIALIZED)
# 2. Stopped (TASK_STOPPED)
# 3. Started (TASK_STARTED)
# When the object is first created, it is in the uninitialized state.
# Here is the state table. The cell content is the new state. Blank cells
# mean the action is ignored.
#                     |--------------------Action-------------------------|
# |---Current state---| initialize() | start() | stop()  | setIPAddress() |
# |-------------------|--------------|---------|---------|----------------|
# | uninitialized     | stopped      |         |         | uninitialized  |
# | stopped           |              | started |         | uninitialized  |
# | started           |              |         | stopped |                |

# The initialize() action ensures that the AVMU unit is online and
# is responding to commands.  It also downloads the hardware details from
# the unit needed to properly program the unit.

# The start() action programs the AVMU unit. At this stage the unit is able
# to respond to measurement commands.

# The stop() action idles the unit.

# The setIPAddress() action puts the state back to uninitialized, because
# the assumption is that a different VNA unit is going to be targeted.
# Hardware details can vary from unit to unit and so those details must be
# re-downloaded prior to programming the new unit.

# NOTE: any calibration data is marked invalid when the state transitions
# to uninitialized. If you would like to use the calibration on a different
# unit (or save it for later), see the exportCalibration() function.
# ------------------------------------------------------------------------
# ------------------------------------------------------------------------


def versionString():
	''' Returns a string describing the version of the DLL and its components.

	Returns:
		String describing the VNA DLL components and version numbers.
	'''
	tmp = dll.versionString
	tmp.argtypes = []
	tmp.restype = ct.c_char_p
	return tmp().decode('ascii')


class RAW_VNA(object):
	''' Minimal wrapper for the VNA Dll.

	Does type-conversion, return-code -> exception translation, and not much else.

	'''

	def __init__(self):
		''' Initialized a handle to the VNA by creating a new Task object.

		The internal state of the VNA task will be TASK_UNINITIALIZED
		upon instantiation of the `RAW_VNA()` object.

		Returns:
			Nothing

		'''
		tmp = dll.createTask
		tmp.argtypes = []
		tmp.restype = TaskHandle
		self.__task = tmp()

	def __del__(self):
		if self.__task:
			self.deleteTask()


	def deleteTask(self):
		''' Deletes the Task object. If the caller does
		not do this, the task-handle memory will leak.

		Note that this will be called automatically by the destructor.

		Args:
			None

		Returns:
			Nothing

		'''
		tmp = dll.deleteTask
		tmp.argtypes = [TaskHandle]
		tmp.restype = None
		tmp(self.__task)

		self.__task = None


	def initialize(self):
		''' Attempts to talk to the unit specified by the Task's IP address, and download
		its details. If it succeeds the Task enters the TASK_STOPPED state.

		Args:
			Nothing

		Returns:
			Nothing

		---

		\exception ERR_MISSING_IP if an IP has not been specified
		\exception ERR_MISSING_PORT if a port has not been specified
		\exception ERR_SOCKET if there was a problem setting up the UDP socket or sending a message
		\exception ERR_NO_RESPONSE if the unit did not respond to commands
		\exception ERR_BAD_PROM if the unit returned hardware details that this DLL doesn't understand
		\exception ERR_WRONG_STATE if the Task is not in the TASK_UNINITIALIZED state
		'''
		tmp = dll.initialize
		tmp.argtypes = [TaskHandle, ct.c_void_p, ct.c_void_p]
		tmp.restype = ErrCode
		ret = tmp(self.__task, 0, 0)
		handleReturnCode(ret)

	def start(self):
		''' Attempts to program the VNA using the settings stored in the Task object. If it
		succeeds the Task enters the TASK_STARTED state.

		Args:
			Nothing

		Returns:
			Nothing

		---


		\exception ERR_SOCKET if there was a problem sending a message
		\exception ERR_NO_RESPONSE if the unit did not respond to commands
		\exception ERR_WRONG_STATE if the Task is not in the TASK_STOPPED state
		\exception ERR_MISSING_HOP if the hop rate has not yet been specified
		\exception ERR_MISSING_ATTEN if the attenuation has not yet been specified
		\exception ERR_MISSING_FREQS if the frequencies have not yet been specified
		\exception ERR_PROG_OVERFLOW if the size of the program is too large for the hardware's memory
				(this can happen if there are too many frequencies)
		'''
		tmp = dll.start
		tmp.argtypes = [TaskHandle]
		tmp.restype = ErrCode
		ret = tmp(self.__task)

		state = TaskStateBOOK[self.getState()]
		handleReturnCode(ret, message="Current state = '%s'" % state)


	def stop(self):
		''' Puts the Task object into the TASK_STOPPED state.

		Args:
			Nothing

		Returns:
			Nothing

		---

		\exception ERR_WRONG_STATE if the Task is not in the TASK_STARTED state

		'''
		tmp = dll.stop
		tmp.argtypes = [TaskHandle]
		tmp.restype = ErrCode
		ret = tmp(self.__task)
		state = TaskStateBOOK[self.getState()]
		handleReturnCode(ret, message="Current state = '%s'" % state)


	def setIPAddress(self, ipv4):
		''' Sets the IPv4 address on which to communicate with the unit. The ipv4 parameter is copied
		into the Task's memory. On success the Task's state will be TASK_UNINITIALIZED.
		Example: `setIPAddress(t, "192.168.1.197");`

		Args:
			ipv4 - VNA IP Address as a ASCII string.

		Returns:
			Nothing

		---

		\exception ERR_MISSING_IP if the pointer is null
		\exception ERR_WRONG_STATE if the Task is not in the TASK_UNINITIALIZED or TASK_STOPPED state

		'''
		tmp = dll.setIPAddress
		tmp.argtypes = [TaskHandle, ct.c_char_p]
		tmp.restype = ErrCode

		# Work on py3k and 2k
		try:
			addr = bytes(ipv4, 'ascii')
		except TypeError:
			addr = bytes(ipv4)

		ret = tmp(self.__task, addr)
		handleReturnCode(ret)


	def setIPPort(self, port):
		''' Sets the port on which to communicate with the unit. Values should be >= 1024.
		On success the Task's state will be TASK_UNINITIALIZED.


		Args:
			port - VNA desired port as an integer.


		Returns:
			Nothing

		---

		\exception ERR_WRONG_STATE if the Task is not in the TASK_UNINITIALIZED or TASK_STOPPED state

		'''
		tmp = dll.setIPPort
		tmp.argtypes = [TaskHandle, ct.c_int]
		tmp.restype = ErrCode
		ret = tmp(self.__task, port)
		handleReturnCode(ret)


	def setTimeout(self, timeout):
		''' Sets the default time to wait, in milliseconds, for a unit to reply to a command
		before giving up and returning an ERR_NO_RESPONSE condition. For the measurement
		functions, this is the amount of time to wait beyond the expected sweep time.
		When a Task is created, the timeout value defaults to 1000.

		A timeout value of 0 results in non-blocking call, where the call will return
		immediately if there is no data in the OS RX Buffer.

		Args:
			timeout - Requested timeout in milliseconds.

		Returns:
			Nothing

		'''
		tmp = dll.setTimeout
		tmp.argtypes = [TaskHandle, ct.c_uint]
		tmp.restype = ErrCode

		# setTimeout ALWAYS returns ERR_OK, Check it anyways
		ret = tmp(self.__task, timeout)
		handleReturnCode(ret)



	def setHopRate(self, rate):
		''' Set the frequency hopping rate. See the values defined above.

		Args:
			rate - An instance of \ref HopRateSettings-Py.

		Returns:
			Nothing

		---

		\exception ERR_BAD_HOP if there was something wrong with the hop rate parameter
		\exception ERR_WRONG_STATE if the Task is not in the TASK_UNINITIALIZED or TASK_STOPPED state

		'''
		tmp = dll.setHopRate
		tmp.argtypes = [TaskHandle, HopRate]
		tmp.restype = ErrCode
		ret = tmp(self.__task, rate)
		handleReturnCode(ret)


	def setAttenuation(self, atten):
		''' Set the attenuation amount. See the values defined above.

		Args:
			t - Task-Handle
			rate - An instance of \ref AttenuationSettings-Py.

		Returns:
			Nothing

		---

		\exception ERR_BAD_ATTEN if there was something wrong with the attenuation parameter
		\exception ERR_WRONG_STATE if the Task is not in the TASK_UNINITIALIZED or TASK_STOPPED state

		'''
		tmp = dll.setAttenuation
		tmp.argtypes = [TaskHandle, Attenuation]
		tmp.restype = ErrCode
		ret = tmp(self.__task, atten)
		handleReturnCode(ret)


	def setFrequencies(self, freqs, N):
		''' Set the frequencies to measure during each sweep. Units are MHz. The freqs parameter
		is an array of length N. Note that the VNA frequency generation hardware has fixed
		precision and so the generated frequency may not be exactly equal to the requested
		frequency. This function silently converts all requested frequencies to frequencies
		that can be exactly generated by the hardware. This has important implications for
		doppler noise when doing a linear sweep. AKELA recommends using the function
		utilFixLinearSweepLimits() to ensure every frequency is exactly generateable and that
		the frequencies are equally spaced. Use the getFrequencies() function to get the
		actual frequencies being generated.

		Args:
			freqs - A ctypes array of frequencies (as doubles, in MHz) to measure
				in a single sweep. The frequency points *to not* have to be linear,
				equally spaced, or follow any sort of ordering. However, due to
				band-change requirements (changing bands takes somewhat longer then changing
				frequencies within a band), grouping frequency points by band can improve
				sweep times.

				Due to type resolution issues, this array **MUST** be constructed using
				the \ref DoubleArrayFactory() call.

			N - The number of items in the array `freqs`


		Returns:
			Nothing

		---

		\exception ERR_WRONG_STATE if the Task is not in the TASK_STOPPED state
		\exception ERR_FREQ_OUT_OF_BOUNDS if a frequency is beyond the allowed min/max. (You can get
			the min and max from the \ref HardwareDetails struct returned by \ref getHardwareDetails())
		\exception ERR_TOO_MANY_POINTS if N is larger than the maximum allowed (see \ref HardwareDetails)

		'''
		tmp = dll.setFrequencies
		tmp.argtypes = [TaskHandle, DoubleArrayFactory(N), ct.c_uint]
		tmp.restype = ErrCode
		ret = tmp(self.__task, freqs, N)
		handleReturnCode(ret)


	def getState(self):
		''' Get the current state of the Task object.

		Args:
			None

		Returns:
			Returns one of the values defined in \ref TaskState-Py.
		'''
		tmp = dll.getState
		tmp.argtypes = [TaskHandle]
		tmp.restype = TaskState
		ret = tmp(self.__task)
		return ret


	def getTimeout(self):
		''' Get the current network timeout setting for communications to the VNA.

		When a Task is first created, the timeout defaults to 1000 milliseconds.

		Args:
			None

		Returns:
			Integer timeout in milliseconds
		'''
		tmp = dll.getTimeout
		tmp.argtypes = [TaskHandle]
		tmp.restype = ct.c_uint
		ret = tmp(self.__task)
		return ret

	def getIPAddress(self):
		''' Get the IP address associated with this Task object.

		Args:
			None

		Returns:
			VNA IP Address or `None` if no IP has been set.

		'''
		tmp = dll.getIPAddress
		tmp.argtypes = [TaskHandle]
		tmp.restype = ct.c_char_p
		ret = tmp(self.__task)
		if ret:
			ret = ret.decode("ascii")
		return ret


	def getIPPort(self):
		''' Get the port associated with this Task object.

		Args:
			None

		Returns:
			Configured communication port. Defaults to 0 if not set.

		'''
		tmp = dll.getIPPort
		tmp.argtypes = [TaskHandle]
		tmp.restype = ct.c_int
		ret = tmp(self.__task)
		return ret

	def getHopRate(self):
		''' Get the frequency hopping rate associated with this Task object.

		Args:
			None

		Returns:
			Returns one of the values defined in \ref HopRateSettings-Py.
			If no rate has yet been set, this function returns HOP_UNDEFINED.

		'''
		tmp = dll.getHopRate
		tmp.argtypes = [TaskHandle]
		tmp.restype = HopRate
		ret = tmp(self.__task)
		return ret

	def getAttenuation(self):
		''' Get the attenuation associated with this Task object.

		Args:
			None

		Returns:
			Returns one of the values defined in \ref AttenuationSettings-Py.
			If no rate has yet been set, this function returns ATTEN_UNDEFINED.

		'''
		tmp = dll.getAttenuation
		tmp.argtypes = [TaskHandle]
		tmp.restype = Attenuation
		ret = tmp(self.__task)
		return ret


	def getNumberOfFrequencies(self):
		''' Get the number of frequencies in the sweep.

		TODO: VALIDATE THIS!

		Args:
			None

		Returns:
			the number of frequency points in the currently configured sweep.
			If no frequencies have been set, this function defaults to returning 0.

		'''
		tmp = dll.getNumberOfFrequencies
		tmp.argtypes = [TaskHandle]
		tmp.restype = ct.c_uint
		ret = tmp(self.__task)
		return ret


	def getFrequencies(self):
		''' Get the list of actual frequencies the hardware generates during the sweep.

		TODO: VALIDATE THIS!

		Args:
			None

		Returns:
				If no frequencies have been set, this function returns 0.

		'''
		npts = self.getNumberOfFrequencies()
		retarr = (ct.c_double*npts)()

		tmp = dll.getFrequencies
		tmp.argtypes = [TaskHandle, ct.POINTER(ct.c_double*npts), ct.c_int]

		tmp.restype = ErrCode
		ret = tmp(self.__task, ct.byref(retarr), npts)
		handleReturnCode(ret)

		if retarr:
			retarr = np.array(retarr[:])
		else:
			retarr = np.empty([0])
		return retarr


	def getHardwareDetails(self):
		''' Get the hardware details for the unit associated with this Task.

		TODO: VALIDATE THIS!

		Args:
			None

		Returns:
			An dictionary of the \ref HardwareDetails members -> value mappings.

			If the Task has not yet been initialized, the returned dict has all values set to 0.

		'''
		tmp = dll.getHardwareDetails
		tmp.argtypes = [TaskHandle]
		tmp.restype = HardwareDetails
		ret = tmp(self.__task)
		return ret.to_dict()

	def utilNearestLegalFreq(self, target_freq):
		''' Adjusts a requested frequency, in MHz, to the nearest able to be generated by the
		VNA hardware. This is not available in the TASK_UNINITIALIZED state.

		TODO: VALIDATE THIS!

		Args:
			target_freq - Target frequency to be adjusted

		Returns:
			Adjusted `target_freq` Frequency value as a float

		---


		\exception ERR_WRONG_STATE if the Task is in the TASK_UNINITIALIZED state
		\exception ERR_FREQ_OUT_OF_BOUNDS if the frequency is beyond the allowed min/max. (You can get
			the min and max from the HardwareDetails struct returned by getHardwareDetails())
		\exception VNADLL_API ErrCode utilNearestLegalFreq(TaskHandle t, double& freq);
		'''

		freq = ct.c_double(target_freq)
		tmp = dll.utilNearestLegalFreq
		tmp.argtypes = [TaskHandle, ct.POINTER(ct.c_double)]
		tmp.restype = ErrCode
		ret = tmp(self.__task, ct.pointer(freq) )
		handleReturnCode(ret)

		return freq.val

	def utilFixLinearSweepLimits(self, target_start_freq, target_end_freq, N):
		''' Adjusts the start and end of a requested linear sweep with N points such that all
		frequencies in the sweep will land on exactly generateable values, and the inter-point
		spacing is constant across the entire scan. Unequal spacing can	cause doppler noise in
		your data.

		This may move the start and end frequencies of your scan slightly (<1 MHz).

		If the input frequencies are equal, or N is 0 or 1, the frequencies are each
		simply adjusted to exactly generateable values.

		TODO: VALIDATE THIS!

		Args:
			target_start_freq - Target Start-frequecny for linear sweep, in Mhz.
			target_end_freq - Target End-frequency for linear-sweep, in Mhz.
			N - Number of points to sample, spaced linearly between startFreq and endFreq

		Returns:
			Adjusted start and stop frequencies as a 2-tuple

		---


		\exception ERR_WRONG_STATE if the Task is in the TASK_UNINITIALIZED state
		\exception ERR_FREQ_OUT_OF_BOUNDS if one of the bounds is beyond the allowed min/max. (You can get
			the min and max from the HardwareDetails struct returned by getHardwareDetails())
		\exception ERR_TOO_MANY_POINTS if N is larger than the maximum allowed (see \ref HardwareDetails)
		'''


		start_freq = ct.c_double(target_start_freq)
		end_freq   = ct.c_double(target_end_freq)

		tmp = dll.utilFixLinearSweepLimits
		tmp.argtypes = [TaskHandle, ct.POINTER(ct.c_double), ct.POINTER(ct.c_double), ct.c_uint]
		tmp.restype = ErrCode
		ret = tmp(self.__task, ct.pointer(start_freq), ct.pointer(end_freq), N )
		handleReturnCode(ret)

		return (start_freq.value, end_freq.value)


	def utilPingUnit(self):
		''' Sends an "are you there" message to the unit.

		Note that this function should not be
		called while a frequency sweep is ongoing, because it causes that sweep to prematurely
		halt and respond to this message instead. This is only an issue in multithreaded code,
		since the data acquisition functions are blocking. This function waits for a reply for
		the length of time specified by getTimeout() before giving up.

		Note that this can be called from any state, provided an IP and port are present.

		Raises an exception if the unit did not respond, returns nothing otherwise.

		Args:
			None

		Returns:
			Nothing

		---


		\exception ERR_SOCKET if there was a problem sending a message
		\exception ERR_NO_RESPONSE if the unit did not respond to commands
		\exception ERR_MISSING_IP if no IP address has been set
		\exception ERR_MISSING_PORT if no port has been set

		'''
		tmp = dll.utilPingUnit
		tmp.argtypes = [TaskHandle]
		tmp.restype = ErrCode
		ret = tmp(self.__task)
		handleReturnCode(ret)


	def utilGenerateLinearSweep(self, startFreq, endFreq, N):
		''' Generates a linear sweep with the requested parameters.

		Note that the start and end
		frequency will be adjusted as documented in utilFixLinearSweepLimits() so that all
		frequency points fall on exactly generateable values. This function internally calls
		setFrequencies() with the resulting array. The caller can retrieve the frequency list
		with the getFrequencies() function. Since it changes the frequencies this function
		is only available in the TASK_STOPPED state.

		Args:
			startFreq - Target Start-frequecny for linear sweep, in Mhz.
			endFreq - Target End-frequency for linear-sweep, in Mhz.
			N - Number of points to sample, spaced linearly between startFreq and endFreq

		Returns:
			Nothing

		---

		\exception ERR_WRONG_STATE if the Task is not in the TASK_STOPPED state
		\exception ERR_FREQ_OUT_OF_BOUNDS if one of the bounds is beyond the allowed min/max. (You can get
			the min and max from the HardwareDetails struct returned by getHardwareDetails())
		\exception ERR_TOO_MANY_POINTS if N is larger than the maximum allowed (see HardwareDetails)

		'''
		tmp = dll.utilGenerateLinearSweep
		tmp.argtypes = [TaskHandle, ct.c_double, ct.c_double, ct.c_uint]
		tmp.restype = ErrCode
		ret = tmp(self.__task, startFreq, endFreq, N)
		handleReturnCode(ret)


	def measureUncalibrated(self):
		''' Measures the paths through the VNA, without applying calibration.

		All 5 paths are always measured.

		Note that this function blocks while the measurement is being performed. Use the
		interruptMeasurement() function to prematurely halt a slow measurement. The automatic
		timeout value is the length of the measurement plus getTimeout().

		Args:
			None
		Returns:
			(T1R1, T1R2, T2R1, T2R2, Ref) - numpy complex arrays as a 5-tuple. Each
			array is a 1-dimentional numpy array of complex numbers, with a length of
			\ref getNumberOfFrequencies(). Each value in the array corresponds to a single
			frequency measurement. The measurement points can be retreived by calling
			\ref getFrequencies(), where the [n]th \ref getFrequencies() value corresponds
			to the frequency for the [n]th measureUncalibrated() entry.


		---

		\exception ERR_SOCKET if there was a problem sending a message
		\exception ERR_NO_RESPONSE if the unit did not respond to commands
		\exception ERR_WRONG_STATE if the Task is not in the TASK_STARTED state
		\exception ERR_BAD_PATH if there is something wrong with the paths parameter
		\exception ERR_BYTES if the wrong number of bytes were received
		\exception ERR_INTERRUPTED if the measurement was interrupted

		'''

		N = self.getNumberOfFrequencies()

		T1R1 = ComplexDataFactory(N)()
		T1R2 = ComplexDataFactory(N)()
		T2R1 = ComplexDataFactory(N)()
		T2R2 = ComplexDataFactory(N)()
		Ref  = ComplexDataFactory(N)()


		tmp = dll.measureUncalibrated
		tmp.argtypes = [
							TaskHandle,
							ComplexDataFactory(N),
							ComplexDataFactory(N),
							ComplexDataFactory(N),
							ComplexDataFactory(N),
							ComplexDataFactory(N)
						]
		tmp.restype = ErrCode

		ret = tmp(self.__task, T1R1, T1R2, T2R1, T2R2, Ref)

		state = TaskStateBOOK[self.getState()]
		handleReturnCode(ret, message="Current state = '%s'" % state)
		return (T1R1.toArray(), T1R2.toArray(), T2R1.toArray(), T2R2.toArray(), Ref.toArray())



	def measure2PortCalibrated(self):
		''' Measures the S-parameter of the connected device, applying the current calibration.

		This command measures all 5 paths, as every path is required to properly apply the
		calibration.

		Note that this function blocks while the measurement is being performed. Use the
		\ref interruptMeasurement() function to prematurely halt a slow measurement.

		Args:
			None

		Returns:
			(S11, S21, S12, S22) - numpy complex arrays as a 4-tuple. Each
			array is a 1-dimentional numpy array of complex numbers, with a length of
			\ref getNumberOfFrequencies(). Each value in the array corresponds to a single
			frequency measurement. The measurement points can be retreived by calling
			\ref getFrequencies(), where the [n]th \ref getFrequencies() value corresponds
			to the frequency for the [n]th measure2PortCalibrated() entry.


		---

		\exception ERR_SOCKET if there was a problem sending a message
		\exception ERR_NO_RESPONSE if the unit did not respond to commands
		\exception ERR_WRONG_STATE if the Task is not in the TASK_STARTED state
		\exception ERR_BAD_PATH if there is something wrong with the paths parameter
		\exception ERR_BAD_CAL if the calibration is missing (i.e. `isCalibrationComplete() == false`)
		\exception ERR_BYTES if the wrong number of bytes were received
		\exception ERR_INTERRUPTED if the measurement was interrupted (generally by \ref interruptMeasurement())

		'''

		N = self.getNumberOfFrequencies()

		S11 = ComplexDataFactory(N)()
		S21 = ComplexDataFactory(N)()
		S12 = ComplexDataFactory(N)()
		S22 = ComplexDataFactory(N)()

		tmp = dll.measure2PortCalibrated
		tmp.argtypes = [TaskHandle, ComplexDataFactory(N), ComplexDataFactory(N), ComplexDataFactory(N), ComplexDataFactory(N)]
		tmp.restype = ErrCode
		ret = tmp(self.__task, S11, S21, S12, S22)

		handleReturnCode(ret)

		return (S11.toArray(), S21.toArray(), S12.toArray(), S22.toArray())



	def measureCalibrationStep(self, step):
		''' Measures the paths necessary to get data for the requested calibration step.

		Note that this function blocks while the measurement is being performed. Use the
		interruptMeasurement() function to prematurely halt a slow measurement.

		Calibration results are written into the local memory of the current task. The
		calibration results can later be retreived by calling \ref exportCalibration().

		Args:
			step  - Instance of \ref CalibrationStepSelector-Py corresponding the calibration
					 step which should be measured.


		---

		\exception ERR_SOCKET if there was a problem sending a message
		\exception ERR_NO_RESPONSE if the unit did not respond to commands
		\exception ERR_WRONG_STATE if the Task is not in the TASK_STARTED state
		\exception ERR_BAD_CAL if the current calibration settings do not match the current
			sweep settings (clear the calibration first before recalibrating)
		\exception ERR_BYTES if the wrong number of bytes were received
		\exception ERR_INTERRUPTED if the measurement was interrupted

		'''
		tmp = dll.measureCalibrationStep
		tmp.argtypes = [TaskHandle, CalibrationStep]
		tmp.restype = ErrCode
		ret = tmp(self.__task, step)

		handleReturnCode(ret)


	def interruptMeasurement(self):
		''' Interrupts one of the measurement functions while it is waiting for data.

		Since the measurement functions are blocking, this function must be called
		from a different thread. This function returns immediately, however the
		measurement function may continue to block for a short additional amount
		of time.

		Args:
			None

		---

		\exception ERR_WRONG_STATE if the Task is not in the TASK_STARTED state

		'''
		tmp = dll.interruptMeasurement
		tmp.argtypes = [TaskHandle]
		tmp.restype = ErrCode
		ret = tmp(self.__task)

		handleReturnCode(ret)


	def clearCalibration(self):
		''' Deletes the calibration data (if any) that the Task is storing.

		Args:
			None

		Returns:
			Nothing

		---

		Will never throw an exception

		'''
		tmp = dll.clearCalibration
		tmp.argtypes = [TaskHandle]
		tmp.restype = ErrCode
		ret = tmp(self.__task)
		handleReturnCode(ret)


	def isCalibrationComplete(self):
		''' Determine if the task has any calibration parameters.

		Args:
			None

		Returns:
			True if the task has calibration parameters. False if it does not.

		'''
		tmp = dll.isCalibrationComplete
		tmp.argtypes = [TaskHandle]
		tmp.restype = ct.c_bool
		ret = tmp(self.__task)
		return ret


	def hasFactoryCalibration(self):
		''' Determine if the connected VNA has a preloaded factory calibration in it's embedded memory.

		Args:
			None

		Returns:
			True if the connected VNA has a factory calibration in it's PROM. False if it does not.

		'''
		tmp = dll.hasFactoryCalibration
		tmp.argtypes = [TaskHandle]
		tmp.restype = ct.c_bool
		ret = tmp(self.__task)
		return ret

	def importFactoryCalibration(self):
		''' Load the calibration from the VNA's embedded PROM into the current task.

		Args:
			None

		Returns:
			Nothing

		Throws:
			\exception ERR_BAD_CAL if the embedded calibration data is not present, or invalid.
			\exception ERR_WRONG_STATE if the task is not in the TASK_STOPPED or TASK_STARTED state

		'''
		tmp = dll.importFactoryCalibration
		tmp.argtypes = [TaskHandle]
		tmp.restype = ErrCode
		ret = tmp(self.__task)
		if ret == ERR_BAD_CAL:
			raise vnaexceptions.VNA_Exception_Bad_Cal("The embedded VNA calibration is either damaged, or not present.")
		handleReturnCode(ret)


	def getCalibrationNumberOfFrequencies(self):
		''' Get the number of frequencies in the calibration data

		Args:
			None

		Returns:
			Number of frequency points the current calibration contains.
			If there is no calibration present, the return value is 0


		'''
		tmp = dll.getCalibrationNumberOfFrequencies
		tmp.argtypes = [TaskHandle]
		tmp.restype = ct.c_uint
		ret = tmp(self.__task)
		return ret


	def getCalibrationFrequencies(self):
		''' Get the list of frequencies used in the calibration data.

		Args:
			None

		Returns:
			Numpy array of frequency points for which there is calibration data.
			If there is no calibration data, returns an empty numpy array.

		'''

		N = self.getCalibrationNumberOfFrequencies()
		tmp = dll.getCalibrationFrequencies
		tmp.argtypes = [TaskHandle]
		tmp.restype = ct.POINTER(ct.c_double*N)

		ret = tmp(self.__task)
		if ret:
			ret = np.array(ret.contents[:])
		else:
			ret = np.empty([0])
		return ret


	def exportCalibration(self):
		''' Retreives the calibration arrays from the current task.

		Note that to fully contain a calibration the caller must also get the frequency list
		and number of frequencies.

		It is recommended to use the \ref getCalibrationFrequencies() function to get the corresponding
		frequency point table, because the number and position of the of calibration frequency points
		do not have to match the sweep parameters.

		Return value is a 12-tuple of arrays of length \ref getCalibrationNumberOfFrequencies().

		This function is the complement of \ref importCalibration().

		Args:
			None

		Returns:
			e00      - Complex number which is an array of the EDF/e00 calibration term.
			e11      - Complex number which is an array of the ESF/e11 calibration term.
			e10e01   - Complex number which is an array of the ERF/e10e01 calibration term.
			e30      - Complex number which is an array of the EXF/e30 calibration term.
			e22      - Complex number which is an array of the ELF/e22 calibration term.
			e10e32   - Complex number which is an array of the ETF/e10e32 calibration term.
			ep33     - Complex number which is an array of the EDR/ep33 calibration term.
			ep22     - Complex number which is an array of the ESR/ep22 calibration term.
			ep23ep32 - Complex number which is an array of the ERR/ep23ep32 calibration term.
			ep03     - Complex number which is an array of the EXR/ep03 calibration term.
			ep11     - Complex number which is an array of the ELR/ep11 calibration term.
			ep23ep01 - Complex number which is an array of the ETR/ep23ep01 calibration term.


		---

		\exception ERR_BAD_CAL if isCalibrationComplete() returns false

		'''

		N = self.getCalibrationNumberOfFrequencies()

		e00      = ComplexDataFactory(N)()
		e11      = ComplexDataFactory(N)()
		e10e01   = ComplexDataFactory(N)()
		e30      = ComplexDataFactory(N)()
		e22      = ComplexDataFactory(N)()
		e10e32   = ComplexDataFactory(N)()
		ep33     = ComplexDataFactory(N)()
		ep22     = ComplexDataFactory(N)()
		ep12ep32 = ComplexDataFactory(N)()
		ep03     = ComplexDataFactory(N)()
		ep11     = ComplexDataFactory(N)()
		ep23ep01 = ComplexDataFactory(N)()

		tmp = dll.exportCalibration
		tmp.argtypes = [TaskHandle] + [ComplexDataFactory(N)] * 12
		tmp.restype = ErrCode
		ret = tmp(self.__task, e00, e11, e10e01, e30, e22, e10e32, ep33, ep22, ep12ep32, ep03, ep11, ep23ep01)
		handleReturnCode(ret)

		return (
					e00.toArray(),
					e11.toArray(),
					e10e01.toArray(),
					e30.toArray(),
					e22.toArray(),
					e10e32.toArray(),
					ep33.toArray(),
					ep22.toArray(),
					ep12ep32.toArray(),
					ep03.toArray(),
					ep11.toArray(),
					ep23ep01.toArray()
			)

	def importCalibration(self, freqs, e00, e11, e10e01, e30, e22, e10e32, ep33, ep22, ep12ep32, ep03, ep11, ep23ep01):
		''' Imports calibration coefficients from caller provided arrays.

		Note that these frequencies do not have to be exactly generateable by the hardware.
		At import an interpolated calibration is generated that matches the current sweep settings.

		Altering sweep settings automatically generates a new interpolated calibration
		from the original imported data provided here.

		Copies of the passed arrays are stored in the task's memory for the duration of
		it's lifetime, or until overridden.

		All 13 passed arrays **must** be the same length.

		This function is the complement of \ref exportCalibration().

		Args:
			freqs    - Array of frequency points for the calibration data arrays. Units are in Mhz.
			e00      - Array of complex numbers containing the set of EDF/e00 calibration terms.
			e11      - Array of complex numbers containing the set of ESF/e11 calibration terms.
			e10e01   - Array of complex numbers containing the set of ERF/e10e01 calibration terms.
			e30      - Array of complex numbers containing the set of EXF/e30 calibration terms.
			e22      - Array of complex numbers containing the set of ELF/e22 calibration terms.
			e10e32   - Array of complex numbers containing the set of ETF/e10e32 calibration terms.
			ep33     - Array of complex numbers containing the set of EDR/ep33 calibration terms.
			ep22     - Array of complex numbers containing the set of ESR/ep22 calibration terms.
			ep12ep32 - Array of complex numbers containing the set of ERR/ep12ep32 calibration terms.
			ep03     - Array of complex numbers containing the set of EXR/ep03 calibration terms.
			ep11     - Array of complex numbers containing the set of ELR/ep11 calibration terms.
			ep23ep01 - Array of complex numbers containing the set of ETR/ep23ep01 calibration terms.

		---

		\exception ERR_BAD_CAL if any of the array pointers are null
		\exception ERR_WRONG_STATE if the Task is not in the TASK_STOPPED or TASK_STARTED state


		'''

		N = len(freqs)
		assert N == len(e00)  == len(e11)  == len(e10e01)   == len(e30)  == len(e22)  == len(e10e32) \
				 == len(ep33) == len(ep22) == len(ep12ep32) == len(ep03) == len(ep11) == len(ep23ep01)

		carr_freqs    = (ct.c_double * N)(*freqs)
		carr_e00      = ComplexDataArrayFromNumpyArray(e00)
		carr_e11      = ComplexDataArrayFromNumpyArray(e11)
		carr_e10e01   = ComplexDataArrayFromNumpyArray(e10e01)
		carr_e30      = ComplexDataArrayFromNumpyArray(e30)
		carr_e22      = ComplexDataArrayFromNumpyArray(e22)
		carr_e10e32   = ComplexDataArrayFromNumpyArray(e10e32)
		carr_ep33     = ComplexDataArrayFromNumpyArray(ep33)
		carr_ep22     = ComplexDataArrayFromNumpyArray(ep22)
		carr_ep12ep32 = ComplexDataArrayFromNumpyArray(ep12ep32)
		carr_ep03     = ComplexDataArrayFromNumpyArray(ep03)
		carr_ep11     = ComplexDataArrayFromNumpyArray(ep11)
		carr_ep23ep01 = ComplexDataArrayFromNumpyArray(ep23ep01)

		tmp = dll.importCalibration
		tmp.argtypes = [TaskHandle, ct.POINTER(ct.c_double), ct.c_uint] + [ComplexDataFactory(N)] * 12
		tmp.restype = ErrCode
		ret = tmp(self.__task,
				carr_freqs,
				N,
				carr_e00,
				carr_e11,
				carr_e10e01,
				carr_e30,
				carr_e22,
				carr_e10e32,
				carr_ep33,
				carr_ep22,
				carr_ep12ep32,
				carr_ep03,
				carr_ep11,
				carr_ep23ep01)
		handleReturnCode(ret)


## @}

