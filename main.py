
from app import GUI
from app import logSetup

def run():
	ui = GUI.MainWindow(versionNo="0.1.2")
	ui.run()

if __name__ == "__main__":
	logSetup.initLogging()
	run()