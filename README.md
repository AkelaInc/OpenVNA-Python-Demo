## PyOpenVNA

This repository contains both the Akela VNA DLL API Python wrapper and a 
simple demo program that showcases the ability for a single computer to acquire
and plot data from an arbitrary number of remote VNAs.

Both the API wrapper and demp program are Python 2 and Python 3 compatible.

In the demo program, additional VNAs can be added and/or removed dynamically 
without needing to start and stop a acquisition from any active VNAs. 
Additionally, the choice of measured S-parameters, as well as some simple 
analysis functions (iFFT of the frequency domain data) can be enabled/disabled 
on-the fly without even halting a running acquisition (the changes are simply
applied on the next sweep). 

Fundamentally, the architecture of this application is quite straight-forward. 
It uses a standard, 2-thread model, where one thread handles the UI, and 
the other communicated with the hardware. The two threads communicate via
a pair of thread-safe queues.

Dependencies:
 - PyQt5
 - PyQtGraph
 - Numpy (the API calls take/return numpy arrays)
 - Colorama (For logging niceness)

NOTE: The Version of PyQtGraph in Pip is (as of 2016-02-10) sufficiently out of
date that is will not work (it doesn't support Qt5). If you build from current
sources, it works fine.

NOTE 2: Python 2k compatibility with Qt5 is.... annoying. Basically, the guy
behind RiverBankComputing (who wrote PyQt) is not releasing PyQt5 bindings
for Python 2, in an attempt to incentivise Py3k adoption.
PyQt5 *will* build fine for Py2k, but you either have to compile it yourself,
or find a 3rd party who has made pre-built binaries available. For testing, 
I used binaries from https://github.com/pyqt/python-qt5.git 
(`pip install git+https://github.com/pyqt/python-qt5.git`)

Currently, this demo has been tested on both linux and windows.

Once the dependencies are installed, simply running `python main.py` will start
the demo.
