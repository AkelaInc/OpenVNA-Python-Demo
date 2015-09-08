# ######################################################################### #
# vnalibrary.py	--	Python module wrapping VNADLL							#
# 																			#
#  	Adapted from /libradar/vnadll/akela_vna_dll.h							#
# 																			#
# 	Author: Abhejit Rajagopal <abhejit@ece.ucsb.edu>						#
# 			Connor Wolf <cwolf@akelainc.com>								#
# 																			#
# 	Date: 07.23.2015														#
# 																			#
# ######################################################################### #


##
#  \addtogroup Python-Exceptions
#
#  \section py-vna-exceptions Exceptions thrown by VNA::vnalibrary::RAW_VNA
#
#  @authors Connor Wolf <cwolf@akelainc.com>
#
#  These are the exceptions that the \ref VNA::vnalibrary::RAW_VNA class
#  may throw.
#
#  Each exception corresponds to the eponymous C error return code,
#  prefixed with "VNA_Exception_".
#



##
#  \addtogroup Python-Exceptions
#  @{
#

# TODO: Exception documentation!

class VNA_Exception(Exception):
	pass


class VNA_Exception_Bad_Atten(VNA_Exception):
	pass
class VNA_Exception_Bad_Cal(VNA_Exception):
	pass
class VNA_Exception_Bad_Handle(VNA_Exception):
	pass
class VNA_Exception_Bad_Hop(VNA_Exception):
	pass
class VNA_Exception_Bad_Path(VNA_Exception):
	pass
class VNA_Exception_Bad_Prom(VNA_Exception):
	pass
class VNA_Exception_Bytes(VNA_Exception):
	pass
class VNA_Exception_Freq_Out_Of_Bounds(VNA_Exception):
	pass
class VNA_Exception_Interrupted(VNA_Exception):
	pass
class VNA_Exception_No_Response(VNA_Exception):
	pass
class VNA_Exception_Missing_Ip(VNA_Exception):
	pass
class VNA_Exception_Missing_Port(VNA_Exception):
	pass
class VNA_Exception_Missing_Hop(VNA_Exception):
	pass
class VNA_Exception_Missing_Atten(VNA_Exception):
	pass
class VNA_Exception_Missing_Freqs(VNA_Exception):
	pass
class VNA_Exception_Prog_Overflow(VNA_Exception):
	pass
class VNA_Exception_Socket(VNA_Exception):
	pass
class VNA_Exception_Too_Many_Points(VNA_Exception):
	pass
class VNA_Exception_Wrong_State(VNA_Exception):
	pass



## @}
