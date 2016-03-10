def phaseshift_signal(signal, angle, deg=True, verify=False):
	import numpy as np

	if len(angle)==1:
		scalar = True
	else:
		scalar = False
	#

	if deg:
		theta = (angle/180.) * np.pi
	else:
		theta = angle
	#
	rotMatrix = np.array([[np.cos(theta), -1*np.sin(theta)], 
			                 [np.sin(theta),  np.cos(theta)]])
	cartesian_mat = np.asarray([np.real(signal), np.imag(signal)]).transpose()

	if scalar:
		cartesian_result = np.asarray( np.asmatrix(cartesian_mat) * np.asmatrix(rotMatrix) )
	else:
		cartesian_result = np.vstack( [ np.asarray( np.asmatrix(cartesian_mat[idx,:]) * np.asmatrix(rotMatrix[:,:, angle[idx]]) ) for idx in range(0,len(signal)) ] )
	#
	complex_result = cartesian_result[:,0] + 1j*cartesian_result[:,1]

	# to check:
	phaseshift_check = np.angle(signal) - np.angle(complex_result)
	phaseshift_check_wrapped = np.arctan2(np.sin(phaseshift_check), np.cos(phaseshift_check))
	if verify:
		print(set(phaseshift_check_wrapped))
	#

	return complex_result

	## TO TEST
	#import numpy as np
	#import sigutil
	#from copy import deepcopy as dpcpy
	#tmp = dpcpy(dut_S11)
	#tmp_result = sigutil.phaseshift_signal(tmp, np.asarray([90]*len(tmp)), deg=True, verify=True)
####
