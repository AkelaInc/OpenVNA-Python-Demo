#### exec(open('testVNA.py').read())
import VNA
import logSetup
import pickle
from time import strftime; dtstamp = strftime("%Y-%m-%d--%H-%M-%S")

logSetup.initLogging()

## setup
DEVICE_IP = '192.168.1.193'
DEVICE_IPPort = 1234
vna = VNA.VNA(DEVICE_IP, DEVICE_IPPort)
[hoprate, attenuation, freq_N, freq_f] = vna.set_config(VNA.HOP_45K, VNA.ATTEN_0, freq=[375, 6000, 1024])
started, currstate = vna.setup_start()
paths = [ VNA.PATH_T1R1, VNA.PATH_T1R2, VNA.PATH_T2R1, VNA.PATH_T2R2 ] # measure all paths

## measure raw
[uncal_check, uncal_vals] = vna.measure_uncal(paths)
[dut_A, dut_U, dut_V, dut_B, dut_rRef] = uncal_vals

### Collect calibration data
#calfilename = 'calibration'+ '_ip'+DEVICE_IP.split('.')[3] +'_'+strftime('%Y-%m-%d') + '.AkelaVNAcal'
#calDict = vna.generate_caldata(paths, ports=[1,2], caltype='solt')
#pickle.dump(calDict, open(calfilename,'wb'))

## Load calibration data
calfilename = 'calibration_ip193_2015-08-25.pickle'
cald = pickle.load(open(calfilename,'rb'))
calibration = vna.generate_cal(cald, caltype='solt')

### Compare calibration to Akela VNA v1.4 (LabView)
#plt = VNA.calutil.compare_cal(cald, calibration, savepath='/home/abhe/3dsims/VNA/comparecal/')

## Apply calibration to new measurements
calibrated_measurement = vna.measure_cal(paths, caltype='solt')
[dut_S11, dut_S21, dut_S12, dut_S22, dut_Ref] = calibrated_measurement
