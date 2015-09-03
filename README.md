## PyVNA

This is a (relatively) simple demo program that uses the Python Akela DLL
API to acquire and plot VNA data from an arbitrary number of remote VNAs.

PyVNA is Python 2 and Python 3 compatible.

Additional VNAs can be added and/or removed dynamically while the application 
is running. Additionally, some simple analysis functions (iFFT of the frequency
domain data) can be enabled/disabled while data is being take seamlessly.
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
