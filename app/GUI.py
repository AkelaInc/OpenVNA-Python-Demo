#! /usr/bin/env python
# -*- coding: utf-8 -*-
#

import sys


from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QDoubleSpinBox
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QSpinBox
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QDialogButtonBox
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QToolBox

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import QSize
from PyQt5.QtGui  import QIcon

from PyQt5.QtCore import pyqtSlot
import pyqtgraph
# import numpy as np

import os.path
import app.vnathread

VNAS = {

}

def VLine():
	vrule = QFrame()
	vrule.setFrameShape(QFrame.VLine)
	vrule.setFrameShadow(QFrame.Sunken)
	vrule.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
	return vrule

def HLine():
	hrule = QFrame()
	hrule.setFrameShape(QFrame.HLine)
	hrule.setFrameShadow(QFrame.Sunken)
	hrule.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
	return hrule

class CalibrateDialog(QDialog):
	def __init__(self, parent=None):
		super(CalibrateDialog, self).__init__(parent)
		self.parent = parent


		self.verticalLayout = QVBoxLayout(self)
		self.verticalLayout.addWidget(self.createCallStepButtons())
		self.verticalLayout.addWidget(self.createCallSaveLoadButtons())
		self.verticalLayout.addStretch(1)
		self.verticalLayout.addWidget(self.createCloseButttonContainer())



		self.plot_paths = ['S21']


	def createCloseButttonContainer(self):

		self.buttonBox = QDialogButtonBox(self)
		self.buttonBox.setOrientation(Qt.Horizontal)
		self.buttonBox.setStandardButtons(QDialogButtonBox.Ok)

		# Cheat a bit here, and just call the close method directly.
		self.buttonBox.clicked.connect(self.close)

		return self.buttonBox


	def createCallSaveLoadButtons(self):
		steps = [
			("CAL_LOAD", QPushButton('Load')),
			("CAL_SAVE", QPushButton('Save')),
		]

		layout = QHBoxLayout()
		for key, wid in steps:
			layout.addWidget(wid)
			wid.setProperty("btn_name", key)
			wid.clicked.connect(self.callDataButtonClicked)


		calstep_container = QGroupBox("Save/Load Cal");
		calstep_container.setLayout(layout)

		return calstep_container

	def createCallStepButtons(self):
		steps = [
			("STEP_THRU",     QPushButton('Through')),
			("STEP_P1_OPEN",  QPushButton('Port 1 Open')),
			("STEP_P1_SHORT", QPushButton('Port 1 Short')),
			("STEP_P1_LOAD",  QPushButton('Port 1 Load')),
			("STEP_P2_OPEN",  QPushButton('Port 2 Open')),
			("STEP_P2_SHORT", QPushButton('Port 2 Short')),
			("STEP_P2_LOAD",  QPushButton('Port 2 Load')),
		]

		layout = QVBoxLayout()
		for key, wid in steps:
			layout.addWidget(wid)
			wid.setProperty("btn_name", key)
			wid.clicked.connect(self.callButtonClicked)


		calstep_container = QGroupBox("Calibration Steps");
		calstep_container.setLayout(layout)

		return calstep_container

	def callDataButtonClicked(self):
		stepname = self.sender().property('btn_name')
		self.parent.doCalDataManip(stepname)

	def callButtonClicked(self):
		stepname = self.sender().property('btn_name')
		self.parent.doCalStep(stepname)


class VnaPanel(QWidget):

	def __init__(self, vna_no, *args, **kwargs):
		super(VnaPanel, self).__init__(*args, **kwargs)
		self.vna_no = vna_no
		self.connected = False

		self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

		layout = QHBoxLayout()
		layout.addLayout(self.createPlotWindow())
		layout.addWidget(VLine())
		layout.addLayout(self.makeControlWindow())
		self.setLayout(layout)

		self.proc, self.command_queue, self.response_queue = app.vnathread.create_thread(self.vna_no)

		self.timer = QTimer()
		self.timer.setInterval(1000/30)
		self.timer.timeout.connect(self.timer_evt)
		self.timer.start()
		self.updateSweepParameters()

	def update_ffts(self, mag, freq, pens):
		paths = []
		keys = list(mag.keys())
		keys.sort()
		for key in keys:
			if key.replace("-", " ") in self.plot_paths:
				value = mag[key]
				color = pens.pop()
				ret = self.plot.plot(freq, value, pen=color, antialias=True)

				# Oh god, abusing nbsp here is HORRIBLE.
				# The spacing of the legend is ghastly without it, though.
				self.plot.plotItem.legend.addItem(ret, "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"+key)
				paths.append(key)
		return paths

	def update_sparams(self, mag, freq, pens):
		paths = []
		keys = list(mag.keys())

		keys.sort()
		for key in keys:
			if key in self.plot_paths:
				value = mag[key]
				color = pens.pop()
				ret = self.plot.plot(freq, value, pen=color, antialias=True)

				# Oh god, abusing nbsp here is HORRIBLE.
				# The spacing of the legend is ghastly without it, though.
				self.plot.plotItem.legend.addItem(ret, "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"+key)
				paths.append(key)
		return paths

	def update_plot(self, data):

		assert data['pts']

		if len(data['fft_data']) and len(data['comp_data']):
			self.plot.setLabel("left", text="Magnitude")
			self.plot.setLabel("bottom", text="Time & Frequency")
		elif len(data['comp_data']):
			self.plot.setLabels(left="Magnitude (dB)", bottom="Frequency (Mhz)")

		elif len(data['fft_data']):
			self.plot.setLabels(left="Magnitude", bottom="Time (nanoseconds)")

		else:
			self.plot.setLabels(left="Wat?", bottom="Wat?")


		if len(data['comp_data']) + len(data['fft_data']) == 1:
			pens = ["k"]
		else:
			# print(data)

			pens = ["s", "g", "c", "m", (0, 200, 50), "b", (150, 150, 0), "r"]

		paths = []
		self.plot.clear()
		self.plot.plotItem.legend.items = []

		if len(data['comp_data']):
			loc_pens = pens[0:len(data['comp_data'])]
			paths += self.update_sparams(data['comp_data'], data['pts'], loc_pens)


			# Scale up the fft_data arrays so the look decent (this is
			# a visual-only tweak, the Y values are meaningless here anyways)

		if len(data['fft_data']):
			loc_pens = pens[len(data['comp_data']):len(data['comp_data'])+len(data['fft_data'])]

			for key in data['fft_data'].keys():
				data['fft_data'][key] = data['fft_data'][key] * 800
			if len(data['comp_data']):
				x_ax_val = data['pts']
			else:
				x_ax_val = data['fft_pts']


			paths += self.update_ffts(data['fft_data'], x_ax_val, loc_pens)


		self.plot.setTitle(title='VNA %s - %s' % (self.targetIpWidget.text(), ", ".join(paths)))


	def timer_evt(self):
		# print("Timer Event!")
		while not self.response_queue.empty():
			arg, value = self.response_queue.get()
			if arg == 'sweep data':
				self.update_plot(value)
			elif arg == 'connect':
				if value == True:
					self.runButton.setEnabled(True)
					self.connectButton.setText("Disconnect")
				elif value == False:
					self.runButton.setEnabled(False)
					self.connectButton.setText("Connect")
					self.runButton.setChecked(False)

			else:
				print("Unknown response type: '%s'" % arg)

	def buttonConnect_evt(self):
		params = (self.targetIpWidget.text(), int(self.targetPortWidget.text()))
		self.command_queue.put(("connect", params))

	def buttonRun_evt(self):
		press = self.runButton.isChecked()
		if press:
			self.sweep_parameters_group.setEnabled(False)
		else:
			self.sweep_parameters_group.setEnabled(True)

		self.command_queue.put(("run", press))
		self.chkbox_change_evt()


	def buttonCalibrate_evt(self):
		print("Calibrate button!")
		self.calButtonControl.exec_()
		# self.command_queue.put(("connect", params))

	def buttonManageCal_loadLocal_evt(self):
		self.command_queue.put(("cal_data", "CAL_LOAD"))
	def buttonManageCal_loadFactory_evt(self):
		self.command_queue.put(("cal_data", "CAL_FACTORY"))
	def buttonManageCal_clear_evt(self):
		self.command_queue.put(("cal_data", "CAL_CLEAR"))

		# self.calButtonControl.exec_()


	def createPlotWindow(self):

		layout = QVBoxLayout()
		self.plot = pyqtgraph.PlotWidget(title='VNA', labels={'left' : "Magnitude (dB)", 'bottom' : "Frequency (Mhz)"}, antialias=True)

		self.plot.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
		self.plot.enableAutoScale()
		self.plot.showGrid(x=True, y=True, alpha=0.35)
		self.legend = self.plot.addLegend(offset=(-60, -30))
		layout.addWidget(self.plot)

		return layout


	def makeControlWindow(self):
		tb = QToolBox()
		tb.addItem(self.makeIpContainer(), "Connection and Run-State")
		tb.addItem(self.makeDisplayedParameterControl(), "Displayed Parameters")
		tb.addItem(self.makeSweepControl(), "Sweep Parameters")
		tb.addItem(self.makeCallButtonCtrl(), "Calibration")
		tb.setMinimumWidth(220)
		tb.setMaximumWidth(220)
		layout = QVBoxLayout()
		layout.addWidget(tb)
		layout.addStretch(1)
		return layout

	def makeIpContainer(self):

		self.targetIpWidget   = QLineEdit('192.168.1.193')
		self.targetPortWidget = QLineEdit('%s' % str(1025+self.vna_no))
		self.connectButton    = QPushButton('Connect')
		self.runButton        = QPushButton('Run')
		self.runButton.setCheckable(True)
		self.runButton.setEnabled(False)

		self.connectButton.clicked.connect(self.buttonConnect_evt)
		self.runButton.clicked.connect(self.buttonRun_evt)

		inputlayout = QGridLayout()
		inputlayout.addWidget(QLabel('IP:'),         0, 0, 1, 1)
		inputlayout.addWidget(QLabel('Port:'),       1, 0, 1, 1)
		inputlayout.addWidget(self.targetIpWidget,   0, 1, 1, 3)
		inputlayout.addWidget(self.targetPortWidget, 1, 1, 1, 3)

		buttonlayout = QGridLayout()
		buttonlayout.addWidget(self.connectButton, 1, 0)
		buttonlayout.addWidget(self.runButton,     1, 1)


		layout = QVBoxLayout()
		layout.addLayout(inputlayout)
		layout.addLayout(buttonlayout)

		ip_container = QGroupBox("IP Address");
		ip_container.setLayout(layout)
		return ip_container

	def chkbox_change_evt(self, dummy_checked=None):
		checked = []
		for cb in self.param_checkboxes:
			if cb.isChecked():
				checked.append(cb.text())

		if len(checked) == 0:
			checked = ['S21']

		self.plot_paths = checked


	def makeCallButtonCtrl(self):
		self.calButtonControl = CalibrateDialog(self)

		self.clear_cal = QPushButton('Clear Calibration')
		self.load_factory_cal = QPushButton('Load Factory Calibration')
		self.load_local_cal = QPushButton('Load Local Calibration')
		self.do_cal = QPushButton('Start Calibration Procedure')

		self.clear_cal.clicked.connect(self.buttonManageCal_clear_evt)
		self.load_factory_cal.clicked.connect(self.buttonManageCal_loadFactory_evt)
		self.load_local_cal.clicked.connect(self.buttonManageCal_loadLocal_evt)




		self.do_cal.clicked.connect(self.buttonCalibrate_evt)

		layout = QVBoxLayout()
		layout.addWidget(self.clear_cal)
		layout.addWidget(self.load_factory_cal)
		layout.addWidget(self.load_local_cal)
		layout.addWidget(self.do_cal)

		ip_container = QGroupBox("Calibrate");
		ip_container.setLayout(layout)
		return ip_container

	def makeSweepControl(self):

		ptsLabel = QLabel('Number of Points:')
		self.ptsCtrl  = QSpinBox()
		self.ptsCtrl.setRange(1, 2500)
		self.ptsCtrl.setValue(1024)

		stFLabel = QLabel('Start Freq:')
		self.strtCtrl = QDoubleSpinBox()
		self.strtCtrl.setRange(375, 6050)
		self.strtCtrl.setValue(375)
		self.strtCtrl.setSuffix(" Mhz")
		spFLabel = QLabel('Stop Freq:')
		self.stpCtrl  = QDoubleSpinBox()
		self.stpCtrl.setRange(375, 6050)
		self.stpCtrl.setValue(6050)
		self.stpCtrl.setSuffix(" Mhz")

		self.ptsCtrl.valueChanged.connect(self.updateSweepParameters)
		self.strtCtrl.valueChanged.connect(self.updateSweepParameters)
		self.stpCtrl.valueChanged.connect(self.updateSweepParameters)


		inputlayout = QGridLayout()
		inputlayout.addWidget(QLabel('Start:'),      0, 0, 1, 1)
		inputlayout.addWidget(QLabel('Stop:'),       1, 0, 1, 1)
		inputlayout.addWidget(QLabel('Points:'),     2, 0, 1, 1)
		inputlayout.addWidget(self.strtCtrl,         0, 1, 1, 3)
		inputlayout.addWidget(self.stpCtrl,          1, 1, 1, 3)
		inputlayout.addWidget(self.ptsCtrl,          2, 1, 1, 3)


		self.sweep_parameters_group = QGroupBox("Sweep Parameters");
		self.sweep_parameters_group.setLayout(inputlayout)

		return self.sweep_parameters_group


	def updateSweepParameters(self):
		pts   = self.ptsCtrl.value()
		start = self.strtCtrl.value()
		stop  = self.stpCtrl.value()
		self.deliverMessage(('sweep', (pts, start, stop)))

	def makeDisplayedParameterControl(self):

		inputlayout1 = QGridLayout()
		inputlayout2 = QGridLayout()

		# Don't change these button's text! It's actually
		# used when determining which button was clicked.
		b1 = QCheckBox('S11')
		b2 = QCheckBox('S21')
		b3 = QCheckBox('S12')
		b4 = QCheckBox('S22')

		b5 = QCheckBox('S11 FFT')
		b6 = QCheckBox('S21 FFT')
		b7 = QCheckBox('S12 FFT')
		b8 = QCheckBox('S22 FFT')
		b1.toggle()
		b2.toggle()
		b3.toggle()
		b4.toggle()
		# b7.toggle()

		inputlayout1.addWidget(b1, 0, 0)
		inputlayout1.addWidget(b2, 1, 0)
		inputlayout1.addWidget(b3, 0, 1)
		inputlayout1.addWidget(b4, 1, 1)

		inputlayout2.addWidget(b5, 0, 0)
		inputlayout2.addWidget(b6, 1, 0)
		inputlayout2.addWidget(b7, 0, 1)
		inputlayout2.addWidget(b8, 1, 1)


		b1.stateChanged.connect(self.chkbox_change_evt)
		b2.stateChanged.connect(self.chkbox_change_evt)
		b3.stateChanged.connect(self.chkbox_change_evt)
		b4.stateChanged.connect(self.chkbox_change_evt)

		b5.stateChanged.connect(self.chkbox_change_evt)
		b6.stateChanged.connect(self.chkbox_change_evt)
		b7.stateChanged.connect(self.chkbox_change_evt)
		b8.stateChanged.connect(self.chkbox_change_evt)

		self.param_checkboxes = [b1, b2, b3, b4, b5, b6, b7, b8]

		sparam_container1 = QGroupBox("S-Parameter");
		sparam_container1.setLayout(inputlayout1)
		sparam_container2 = QGroupBox("S-Parameter FFT");
		sparam_container2.setLayout(inputlayout2)

		container = QVBoxLayout()
		container.addWidget(sparam_container1)
		container.addWidget(sparam_container2)

		container_wid = QGroupBox("");
		container_wid.setLayout(container)


		return container_wid

	def close(self):
		print("Vna close call!")

		self.command_queue.put(("run", False))
		self.command_queue.put(("halt", True))

	def doCalDataManip(self, calstep):
		self.deliverMessage(('cal_data', calstep))
	def doCalStep(self, calstep):
		self.deliverMessage(('calibrate', calstep))

	def deliverMessage(self, message):
		print("Command message: '%s'" % (message, ))
		self.command_queue.put(message)

class PyVNA(QWidget):

	def __init__(self, versionNo):
		print("PyVNA __init__()")
		self.version = versionNo

		pyqtgraph.setConfigOption('background', 'w')
		pyqtgraph.setConfigOption('foreground', 'k')

		self.vna_idx = 1
		super(PyVNA, self).__init__()

		icopath = "./Akela Logo.ico"

		# Icon isn't on current path, and we're running in a frozen context,
		# so therefore look for the icon at the frozen location.
		if not os.path.exists(icopath) and getattr(sys, 'frozen', False):
			icopath = os.path.join(sys._MEIPASS, icopath)


		icon = QIcon(icopath)
		self.setWindowIcon(icon)

		self.vnas = []
		self.initUI()

		self.setWindowTitle("OpenVNA Python Example Program")



	def addVnaBtnClick_evt(self, force=False):

		new = VnaPanel(len(self.vnas) + 1)
		self.vnas.append(new)
		self.layout.addWidget(new)

	def removeVnaBtnClick_evt(self):

		if len(self.vnas) == 0:
			print("No VNAs left to remove!")
			return

		rm = self.vnas.pop()
		rm.close()
		self.layout.removeWidget(rm)

		# Ugly, ugly hacks to force the
		# underlying widget to be destroyed.
		rm.setParent(None)
		rm.deleteLater()
		rm = None


	def addControlPanel(self):

		version = QLabel('Version: %s' % self.version)

		addvnabtn = QPushButton('Add VNA')
		addvnabtn.clicked.connect(self.addVnaBtnClick_evt)

		closeButton      = QPushButton('Remove VNA')
		closeButton.clicked.connect(self.removeVnaBtnClick_evt)



		layout = QHBoxLayout()
		layout.addWidget(version)
		layout.addStretch()
		layout.addWidget(addvnabtn)
		layout.addWidget(closeButton)
		return layout


	def initUI(self):

		self.layout = QVBoxLayout()
		self.layout.addLayout(self.addControlPanel())
		self.layout.addWidget(HLine())
		self.addVnaBtnClick_evt(force=True)
		self.layout.setAlignment(Qt.AlignTop)

		# self.installTimer()

		self.setLayout(self.layout)


	# def timer_evt(self):
	# 	print(objgraph.show_growth(limit=30))

	# def installTimer(self):

	# 	print("Installing objgraph timer")
	# 	self.timer = QTimer()
	# 	self.timer.setInterval(1000*3)
	# 	self.timer.timeout.connect(self.timer_evt)
	# 	self.timer.start()


class MainWindow(object):
	def __init__(self, versionNo):


		# Create an PyQT4 application object.
		self.app = QApplication(sys.argv)

		# The QWidget widget is the base class of all user interface objects in PyQt4.
		self.ex = PyVNA(versionNo=versionNo)

		# Set window size.
		self.ex.resize(750, 480)

		# Set window title

	def run(self):
		self.ex.show()
		sys.exit(self.app.exec_())

# Show window
