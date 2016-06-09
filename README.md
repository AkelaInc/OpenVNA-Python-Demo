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

Lastly, each VNA can be calibrated, and the calibration stored in a local file
if desired.

Fundamentally, the architecture of thie application is quite straight-forward. 
It uses a standard, 2-thread model, where one thread handles the UI, and 
the other communicated with the hardware. The two threads communicate via
a pair of thread-safe queues.

Dependencies:
 - PyQt5
 - PyQtGraph
 - Numpy (the API calls take/return numpy arrays)
 - Colorama (For logging niceness)

NOTE: The Version of PyQtGraph in Pip is (as of 2015-09-03) sufficently out of
date that is will not work (it doesn't support Qt5). If you build from current
sources, it works fine.

Currently, this demo has been tested on both linux and windows.

Once the dependencies are installed, simply running `python main.py` will start
the demo.

To use the DLL & API alone, numpy and colorama are required, though the other 
dependencies can be ignored.

Colorama can be installed through `pip` on windows without issue, though numpy
can be involved. The package from http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy
provides an easy shortcut.
