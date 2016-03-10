#### exec(open('testVNA2.py').read())
import VNA
import logSetup
import pickle
logSetup.initLogging()
from collections import namedtuple

## setup
DEVICE_IP = '192.168.1.193'
DEVICE_IPPort = 1234
vna = VNA.VNA(DEVICE_IP, DEVICE_IPPort)
[hoprate, attenuation, freq_N, freq_f] = vna.set_config(VNA.HOP_45K, VNA.ATTEN_0, freq=[375, 6000, 1024])
started, currstate = vna.setup_start()
paths = [ VNA.PATH_T1R1, VNA.PATH_T1R2, VNA.PATH_T2R1, VNA.PATH_T2R2 ] # measure all paths

prompt = lambda key='<enter>': 'Press '+key+' to continue...:'

frequencies = freq_f

## PORT1
# 1-port CAL, OPEN	-p1
value = input('1-port CAL, OPEN	-p1'+prompt())
[measure_check, return_values] = vna.measure_uncal(paths)
OA = return_values.T1R1
OR1 = return_values.Ref

# 1-port CAL, SHORT	-p1
value = input('1-port CAL, SHORT	-p1'+prompt())
[measure_check, return_values] = vna.measure_uncal(paths)
SA = return_values.T1R1
SR1 = return_values.Ref

# 1-port CAL, LOAD	-p1
value = input('1-port CAL, LOAD	-p1'+prompt())
[measure_check, return_values] = vna.measure_uncal(paths)
LA = return_values.T1R1
LU = return_values.T1R2
LR1 = return_values.Ref

## 2-port CAL, THROUGH
value = input('2-port CAL, THROUGH'+prompt())
[measure_check, return_values] = vna.measure_uncal(paths)
TA = return_values.T1R1
TU = return_values.T1R2
TV = return_values.T2R1
TB = return_values.T2R2
TR = return_values.Ref

## PORT2
# 1-port CAL, OPEN	-p2
value = input('1-port CAL, OPEN	-p2'+ prompt())
[measure_check, return_values] = vna.measure_uncal(paths)
OB = return_values.T2R2
OR2 = return_values.Ref

# 1-port CAL, SHORT	-p2
value = input('1-port CAL, SHORT	-p2' + prompt())
[measure_check, return_values] = vna.measure_uncal(paths)
SB = return_values.T2R2
SR2 = return_values.Ref

# 1-port CAL, LOAD	-p2
value = input('1-port CAL, LOAD	-p2' + prompt())
[measure_check, return_values] = vna.measure_uncal(paths)
LB = return_values.T2R2
LV = return_values.T2R1
LR2 = return_values.Ref



# store em!
tmplist = [	'frequencies',
			'OA', 'OR1', 'OB', 'OR2',
			'SA', 'SR1', 'SB', 'SR2',
			'LA', 'LU', 'LR1', 
			'LV', 'LB', 'LR2',
			'TA', 'TU', 'TV', 'TB', 'TR']
tmplist = ', '.join(tmplist)
raw_caldata = namedtuple('raw_caldata_SOLT', tmplist) 
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

