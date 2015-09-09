#! /usr/bin/env python
# -*- coding: utf-8 -*-
#

import sys
import sip

from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QDoubleSpinBox
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QRadioButton
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QSpinBox
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QDialogButtonBox
from PyQt5.QtWidgets import QTextBrowser
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
			("STEP_P1_OPEN",  QPushButton('Port 1 Open')),
			("STEP_P1_SHORT", QPushButton('Port 1 Short')),
			("STEP_P1_LOAD",  QPushButton('Port 1 Load')),
			("STEP_P2_OPEN",  QPushButton('Port 2 Open')),
			("STEP_P2_SHORT", QPushButton('Port 2 Short')),
			("STEP_P2_LOAD",  QPushButton('Port 2 Load')),
			("STEP_THRU",     QPushButton('Through')),
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

	def update_plot(self, data):

		mag = data['comp_data']
		freq = data['pts']

		if len(mag) == 1:
			pens = ["k"]
		else:
			# print(data)

			pens = ["s", "g", "c", "m", (0, 200, 50), "b", (150, 150, 0), "r"]

		paths = []
		self.plot.clear()
		self.plot.plotItem.legend.items = []

		keys = list(mag.keys())
		if "FFT" in " ".join(keys):
			self.plot.setLabel("left", text="Magnitude")
			self.plot.setLabel("bottom", text="Time & Frequency")
		else:
			self.plot.setLabels(left="Magnitude (dB)", bottom="Frequency (Mhz)")
		keys.sort()
		for key in keys:
			value = mag[key]
			# print("Plotting", key)
			color = pens.pop()
			ret = self.plot.plot(freq, value, pen=color, antialias=True)

			# Oh god, abusing nbsp here is HORRIBLE.
			# The spacing of the legend is ghastly without it, though.
			self.plot.plotItem.legend.addItem(ret, "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"+key)
			paths.append(key)
		self.plot.setTitle(title='VNA %s - %s' % (self.targetIpWidget.text(), ", ".join(paths)))


	def timer_evt(self):
		# print("Timer Event!")
		while not self.response_queue.empty():
			arg, value = self.response_queue.get()
			if arg == 'sweep':
				self.update_plot(value)
			else:
				print("Unknown response type: '%s'" % arg)

	def buttonConnect_evt(self):
		params = (self.targetIpWidget.text(), int(self.targetPortWidget.text()))
		self.command_queue.put(("connect", params))

	def buttonRun_evt(self):
		press = self.runButton.isChecked()
		self.command_queue.put(("run", press))


	def buttonCalibrate_evt(self):
		print("Calibrate button!")
		self.calButtonControl.exec_()
		# self.command_queue.put(("connect", params))


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
		tb.addItem(self.makeMeasurementParameterControl(), "Measured Parameters")
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
		self.targetPortWidget = QLineEdit('%s' % str(1023+self.vna_no))
		self.connectButton    = QPushButton('Connect')
		self.runButton        = QPushButton('Run')

		self.runButton.setCheckable(True)

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

	def chkbox_change_evt(self, checked):
		checked = []
		for cb in self.param_checkboxes:
			if cb.isChecked():
				checked.append(cb.text())

		if len(checked) == 0:
			checked = ['S21']


		self.command_queue.put(("path", checked))

	def makeCallButtonCtrl(self):
		self.calButtonControl = CalibrateDialog(self)

		self.do_cal = QPushButton('Start Calibration')
		self.do_cal.clicked.connect(self.buttonCalibrate_evt)

		layout = QVBoxLayout()
		layout.addWidget(self.do_cal)

		ip_container = QGroupBox("Calibrate");
		ip_container.setLayout(layout)
		return ip_container

	def makeSweepControl(self):

		ptsLabel = QLabel('Number of Points:')
		self.ptsCtrl  = QSpinBox()
		self.ptsCtrl.setRange(1, 4001)
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


		ip_container = QGroupBox("Sweep Parameters");
		ip_container.setLayout(inputlayout)

		return ip_container


	def updateSweepParameters(self):
		pts   = self.ptsCtrl.value()
		start = self.strtCtrl.value()
		stop  = self.stpCtrl.value()
		self.deliverMessage(('sweep', (pts, start, stop)))

	def makeMeasurementParameterControl(self):

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

	def __init__(self):
		print("PyVNA __init__()")


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



	def addVnaBtnClick_evt(self):
		new = VnaPanel(len(self.vnas) + 1)
		self.vnas.append(new)
		self.layout.addWidget(new)
		# self.updateSweepParameters()

	def removeVnaBtnClick_evt(self):
		if len(self.vnas) == 0:
			print("No VNAs left to remove!")
			return

		rm = self.vnas.pop()
		rm.close()
		self.layout.removeWidget(rm)

		sip.delete(rm)


	def addControlPanel(self):


		addvnabtn = QPushButton('Add VNA')
		addvnabtn.clicked.connect(self.addVnaBtnClick_evt)

		closeButton      = QPushButton('Remove VNA')
		closeButton.clicked.connect(self.removeVnaBtnClick_evt)



		layout = QHBoxLayout()
		layout.addStretch()
		layout.addWidget(addvnabtn)
		layout.addWidget(closeButton)
		return layout


	def initUI(self):
		self.setWindowTitle('PyVNA')
		self.layout = QVBoxLayout()
		self.layout.addLayout(self.addControlPanel())
		self.layout.addWidget(HLine())
		self.addVnaBtnClick_evt()
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
	def __init__(self):


		# Create an PyQT4 application object.
		self.app = QApplication(sys.argv)

		# The QWidget widget is the base class of all user interface objects in PyQt4.
		self.ex = PyVNA()

		# Set window size.
		self.ex.resize(640, 480)

		# Set window title

	def run(self):
		self.ex.show()
		sys.exit(self.app.exec_())

# Show window
