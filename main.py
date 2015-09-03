
from app import GUI
from app import logSetup

def run():
	ui = GUI.MainWindow()
	ui.run()

if __name__ == "__main__":
	logSetup.initLogging()
	run()