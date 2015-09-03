

import logging
import colorama as clr

import sys
import traceback
# Pylint can't figure out what's in the record library for some reason
#pylint: disable-msg=E1101

colours = [
		clr.Fore.RED,
		clr.Fore.GREEN,
		clr.Fore.YELLOW,
		clr.Fore.MAGENTA,
		clr.Fore.CYAN,
		clr.Back.YELLOW + clr.Fore.BLACK,
		clr.Back.YELLOW + clr.Fore.BLUE,
		clr.Fore.WHITE,
		clr.Fore.BLUE,
	]

def getColor(idx):
	return colours[idx%len(colours)]


class ColourHandler(logging.Handler):

	def __init__(self, level=logging.INFO):
		logging.Handler.__init__(self, level)
		self.formatter = logging.Formatter('\r%(name)s%(padding)s - %(style)s%(levelname)s - %(message)s'+clr.Style.RESET_ALL)
		clr.init()

		self.logPaths = {}

	def emit(self, record):

		# print record.levelname
		# print record.name

		segments = record.name.split(".")
		if segments[0] == "Main" and len(segments) > 1:
			segments.pop(0)
			segments[0] = "Main."+segments[0]

		nameList = []

		for indice, pathSegment in enumerate(segments):
			if not indice in self.logPaths:
				self.logPaths[indice] = [pathSegment]
			elif not pathSegment in self.logPaths[indice]:
				self.logPaths[indice].append(pathSegment)

			name = clr.Style.RESET_ALL
			name += getColor(self.logPaths[indice].index(pathSegment))
			name += pathSegment
			name += clr.Style.RESET_ALL
			nameList.append(name)


		record.name = ".".join(nameList)

		if record.levelname == "DEBUG":
			record.style = clr.Style.DIM
		elif record.levelname == "WARNING":
			record.style = clr.Style.BRIGHT
		elif record.levelname == "ERROR":
			record.style = clr.Style.BRIGHT+clr.Fore.RED
		elif record.levelname == "CRITICAL":
			record.style = clr.Style.BRIGHT+clr.Back.BLUE+clr.Fore.RED
		else:
			record.style = clr.Style.NORMAL

		record.padding = ""
		print((self.format(record)))



def exceptHook(exc_type, exc_value, exc_traceback):
	if issubclass(exc_type, KeyboardInterrupt):
		sys.__excepthook__(exc_type, exc_value, exc_traceback)
		return
	mainLogger = logging.getLogger("Main")			# Main logger
	mainLogger.critical('Uncaught exception!')
	mainLogger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

# Global hackyness to detect and warn on double-initialization of the logging systems.
LOGGING_INITIALIZED = False

def initLogging(logLevel=logging.INFO):

	global LOGGING_INITIALIZED
	if LOGGING_INITIALIZED:
		current_stack = traceback.format_stack()
		print("ERROR - Logging initialized twice!")
		for line in current_stack:
			print(line.rstrip())
		return

	LOGGING_INITIALIZED = True

	print("Setting up loggers....")


	mainLogger = logging.getLogger("Main")			# Main logger
	mainLogger.setLevel(logLevel)

	# Do not propigate up to any parent loggers other things install
	mainLogger.propagate = False

	ch = ColourHandler(level=logLevel)
	mainLogger.addHandler(ch)

	sys.excepthook = exceptHook

	print("done")


if __name__ == "__main__":
	initLogging(logToDb=True)
	log = logging.getLogger("Main.Test")
	log.debug("Testing logging - level: debug")
	log.info("Testing logging - level: info")
	log.warn("Testing logging - level: warn")
	log.error("Testing logging - level: error")
	log.critical("Testing logging - level: critical")
