# QisStreamExample.py
# Tom Pope 20/09/2017
#
# Examples using QIS (Quarch Instrumentation Server) to stream data from a power module.
import sys, os

libpath = os.path.dirname(os.path.abspath(__file__))
libpath = os.path.join(libpath, "lib")
sys.path.insert( 0, os.path.join(libpath,os.path.normpath('QisInterface')) )

import QisInterface #Import the Quarch QisInterface module which gives an interface to the QuarchBackEnd Java program
import time  #To use sleep
import sys    #To get args

# If QIS is running on a remote host, replace with its local address
localHost =  '127.0.0.1'
qis = QisInterface.QisInterface(localHost)

def main():
	# Defines where debugPrint puts the output lines from the script. Comment as appropriate
	debugPrintSetup('Command Line')
	#debugPrintSetup('File', 'QisExampleDebug.txt')
	
	# Opening the Connection to the device.  USB and Ethernet are supported in this example.
	# For USB connections, the connection parameter is "usb::qtl1824-03-161". The full serial number 
	# of your module. For Ethernet connections, the connection parameter is "tcp::1999-02-999". 
	# The full serial number minus the "qtl" or can use the ip address instead of the serial number.
	
	module = "tcp::1995-02-002-002"
	# module = "usb::qtl1944-02-028"
	# moduleGroup = ["tcp::1995-02-002-001", "tcp::1995-02-002-002", "tcp::1995-02-002-003"]
	
	# Does a simple power margining routine printing results to console or a file
	#powerMarginingExample(module)
	
	# Runs a simple stream using default device settings
	#simpleStream(module)
	
	# Splits stream data into multiple files. Is a requirement for running at low averaging on XLC and HD
	#multiStreamExample(module)
	
	# Runs multiple streams at once. This is suitable for a 6 way PPM or multiple individual power modules.
	# CAUTION, running multiple streams requires a large bandwidth an CPU resource. It is important
	# to use a large device averaging and if overruns still occur, use multiple PCs instead.
	# multiDeviceStreamExample(moduleGroup)
	
	# Averages data for arbitrary time greater than device averaging
	# CAUTION, has a percentage error in timing equal to the device averaging time
	# divided by the time this script averages the data by. I.e. 1 second averaging 
	# using device averaging of 1k has an error of +/-0.4096%. However, it will not cause 
	# a culmulative timing error
	averageTime = 1	# Time in seconds to average over
	averageStream(module, averageTime)


def powerMarginingExample(module):
	# Prints out connected module information
	debugPrint("Running Qis Stream Example\n\n")
	debugPrint("Module Name:")
	debugPrint(qis.sendCmd(module,"hello?"))
	debugPrint("\n")
	
	# Checks if 3V3 or 5V has automatically been set. If not, manually sets to 3V3
	if (qis.sendCmd(module, "Config Output Mode?") == "DISABLED"):
		debugPrint("Either using an HD without an intelligent fixture or an XLC. Manually setting voltage")
		debugPrint(qis.sendCmd(module, "Config Output Mode 3V3"), 1)
	
	# Check the state of the module and power up if necessary
	debugPrint("Checking the state of the device and power up if necessary")
	CurrentState = qis.sendCmd(module,"run power?")
	debugPrint("State of the Device:" + (CurrentState))
	
	# If outputs are off
	if CurrentState == "OFF":
		# Power Up
		debugPrint(qis.sendCmd(module, "Run Power up"), 1)
	
	debugPrint("\nRunning power margingin test:\n")
	debugPrint("Margining results for 12V rail")
	
	# Loop through 6 different voltage levels, reducing by 200mV on each loop
	testVoltage = 12000
	for i in range(6):
		
		# Set the new voltage level
		debugPrint(qis.sendCmd(module, "Signal 12V Voltage %d" % testVoltage), 1)
		
		# Wait for voltage rails to settle at the new level
		time.sleep(1)
		
		# Request and print the voltage and current measurements
		debugPrint(qis.sendCmd(module, "Measure Voltage 12V?"))
		debugPrint(qis.sendCmd(module, "Measure Current 12V?"))
		
		# Decreasing the testVoltage by 200mV
		testVoltage -= 200
	
	# Set the 12V level back to default
	debugPrint("Setting the 12V rail back to default state")
	debugPrint(qis.sendCmd(module, "Signal 12V Voltage 12000"), 1)
	testVoltage = 3300
	debugPrint("\n\nMargining results 3V3 rail")
	for i in range(6):
		
		# Set the new voltage level
		debugPrint(qis.sendCmd(module, "Signal 3V3 Voltage %d" % testVoltage), 1)
		
		# Wait for voltage rails to settle at the new level
		time.sleep(1)
		
		# Request and print the voltage and current measurements
		debugPrint(qis.sendCmd(module, "Measure Voltage 3V3?"))
		debugPrint(qis.sendCmd(module, "Measure Current 3V3?"))
		
		# Decreasing the testVoltage by 100mV
		testVoltage -= 100
	
	debugPrint("Setting the 3V3 rail back to default state\n\n")
	debugPrint(qis.sendCmd(module, "Signal 3V3 Voltage 3300"), 1)
	
	debugPrint(qis.sendCmd(module, "Run Power down"), 1)
	
	debugPrint("ALL DONE!")

def simpleStream(module):
	# Prints out connected module information
	debugPrint("Running Qis Stream Example\n\n")
	debugPrint("Module Name:")
	debugPrint(qis.sendCmd(module,"hello?"))
	debugPrint("\n")
	
	# Checks if 3V3 or 5V has automatically been set. If not, manually sets to 3V3
	if (qis.sendCmd(module, "Config Output Mode?") == "DISABLED"):
		debugPrint("Either using an HD without an intelligent fixture or an XLC. Manually setting voltage")
		debugPrint(qis.sendCmd(module, "Config Output Mode 5V"), 1)
	
	# Sets the trigger mode such that the stream is controlled by the script.
	debugPrint(qis.sendCmd(module, "Record Trigger Mode Manual"), 1)
	
	# Options for start stream:
	# set the filename to save data to, the max file size and the name for the stream.
	qis.startStream(module, 'Stream 1.txt', 2000, 'Test 1')
	# Module is now recording data to file. It will stop when a buffer fills, or when the streamTime has 
	# elapsed. In the meantime this thread continues to run with the recording thread running in the 
	# backgroud.
	
	# Sleep for 5 seconds to ensure good data before it tries to start up.
	time.sleep(1)
	# Check the state of the module and power up if necessary
	debugPrint("Checking the state of the device and power up if necessary")
	CurrentState = qis.sendCmd(module,"run power?")
	debugPrint("State of the Device:" + (CurrentState))
	
	# If outputs are off
	if CurrentState == "OFF":
		# Power Up
		debugPrint(qis.sendCmd(module, "Run Power up"), 1)
	
	streamTime = 10
	time.sleep(streamTime)
	streamStatus = qis.streamRunningStatus(module)
	if ("Stopped" in streamStatus):
		if ("Overrun" in streamStatus):
			debugPrint('Stream interrupted due to internal device buffer has filled up')
		elif ("User" in streamStatus):
			debugPrint('Stream interrupted due to max file size has being exceeded')
			# Stopped User is currently called because the individual file size exceeds fileMaxMB
		else:
			print("Stopped for unknown reason")
	qis.stopStream(module)
	debugPrint("Stream ran for %d's" % streamTime)
	debugPrint(qis.sendCmd(module, "Run Power down"), 1)
	# The above function is blocking and will wait until all data has been taken from the QIS buffer.
	debugPrint('Script: Finished Test 1. Data saved to \'Stream 1.txt\'')

def multiStreamExample(module):
	# Prints out connected module information
	debugPrint("Running Qis Multi-Stream Example\n\n")
	debugPrint("Module Name:")
	debugPrint(qis.sendCmd(module,"hello?"))
	debugPrint("")
	
	# Checks if 3V3 or 5V has automatically been set. If not, manually sets to 3V3
	if (qis.sendCmd(module, "Config Output Mode?") == "DISABLED"):
		debugPrint("Either using an HD without an intelligent fixture or an XLC. Manually setting voltage")
		debugPrint(qis.sendCmd(module, "Config Output Mode 3V3"), 1)
	
	# Sets the trigger mode such that the stream is controlled by the script.
	debugPrint(qis.sendCmd(module, "Record Trigger Mode Manual"), 1)
	
	debugPrint(qis.sendCmd(module, "Record Averaging 32k"), 1)
	
	fileNamePart = 'QisMultiExample'
	count = time.time()
	streamTime = 3600
	endTime = count + streamTime
	fileNameCount = 0
	# Loop to create multiple files
	while time.time() < endTime:
		# Create the current filename
		fileName = "%(1)s_%(2)d.txt" % {'1' : fileNamePart, '2': fileNameCount}
		debugPrint('New file started: ' + fileName)
		fileNameCount += 1
		
		qis.startStream(module, fileName, 2000, 'Test 1')
		
		while time.time() < endTime:
			time.sleep(1)
			streamStatus = qis.streamRunningStatus(module)
			if ("Stopped" in streamStatus):
				break
			if ("8388608 of 8388608" in qis.streamBufferStatus(module)):
				break
		qis.stopStream(module)

def multiDeviceStreamExample(moduleGroup):
	# Prints out connected module information
	debugPrint("Running Qis Multi-Stream Example\n\n")
	debugPrint("Module Name:")
	for module in moduleGroup:
		debugPrint(qis.sendCmd(module,"hello?"))
		debugPrint("")
		
		# Checks if 3V3 or 5V has automatically been set. If not, manually sets to 3V3
		
		if (qis.sendCmd(module, "Config Output Mode?") == "DISABLED"):
			debugPrint("Either using an HD without an intelligent fixture or an XLC. Manually setting voltage")
			debugPrint(qis.sendCmd(module, "Config Output Mode 3V3"), 1)
		
		# Sets the trigger mode such that the stream is controlled by the script.
		debugPrint(qis.sendCmd(module, "Record Trigger Mode Manual"))
		
		debugPrint(qis.sendCmd(module, "Record Averaging 512"))
	
	fileNamePart = 'QisMultiExample'
	count = time.time()
	streamTime = 10
	endTime = count + streamTime
	fileNameCount = 0
	# Loop to create multiple files
	while time.time() < endTime:
		deviceNumber = 1
		for module in moduleGroup:
			# Create the current filename
			fileName = "%(1)s_%(2)d_%(3)d.txt" % {'1' : fileNamePart, '2': fileNameCount, '3': deviceNumber}
			debugPrint('New file started: ' + fileName)
			qis.startStream(module, fileName, 2000, 'Stream %d' % deviceNumber)
			deviceNumber += 1
		fileNameCount += 1
		while time.time() < endTime:
			time.sleep(1)
			for module in moduleGroup:
				streamStatus = qis.streamRunningStatus(module)
				if ("Stopped" in streamStatus):
					break
				if ("8388608 of 8388608" in qis.streamBufferStatus(module)):
					break
		for module in moduleGroup:
			qis.stopStream(module)

def averageStream(module, averageTime):
	# Prints out connected module information
	debugPrint("Running Qis Averaging Example\n\n")
	debugPrint("Module Name:")
	debugPrint(qis.sendCmd(module,"hello?"))
	debugPrint("\n")
	
	# Checks if 3V3 or 5V has automatically been set. If not, manually sets to 3V3
	if (qis.sendCmd(module, "Config Output Mode?") == "DISABLED"):
		debugPrint("Either using an HD without an intelligent fixture or an XLC. Manually setting voltage")
		debugPrint(qis.sendCmd(module, "Config Output Mode 5V"), 1)
	
	# Sets the trigger mode such that the stream is controlled by the script.
	debugPrint(qis.sendCmd(module, "Record Trigger Mode Manual"), 1)
	
	# Enables power calculations to be stored in specified file
	debugPrint(qis.sendCmd(module, "stream mode power enable"))
	sampleRate = '64'
	
	debugPrint(qis.sendCmd(module, "Record Averaging %s" % sampleRate))
	
	# Options for start stream:
	# set the filename to save data to, the max file size, the name for the stream and the number of samples to average
	qis.startStream(module, 'Stream 6.txt', 2000, 'Test 1', streamAverage = averageTime)
	# Module is now recording data to file. It will stop when a buffer fills, or when the streamTime has 
	# elapsed. In the meantime this thread continues to run with the recording thread running in the 
	# backgroud.
	
	# Sleep for 5 seconds to ensure good data before it tries to start up.
	time.sleep(5)
	# Check the state of the module and power up if necessary
	debugPrint("Checking the state of the device and power up if necessary")
	CurrentState = qis.sendCmd(module,"run power?")
	debugPrint("State of the Device:" + (CurrentState))
	
	# If outputs are off
	if CurrentState == "OFF":
		# Power
		debugPrint(qis.sendCmd(module, "Run Power up"), 1)
	
	streamTime = 43200
	endTime = time.time() + streamTime
	# Loop to create multiple files
	while time.time() < endTime:
		time.sleep(10)
		streamStatus = qis.streamRunningStatus(module)
		if ("Stopped" in streamStatus):
			if ("Overrun" in streamStatus):
				debugPrint('Stream interrupted due to internal device buffer has filled up')
			elif ("User" in streamStatus):
				debugPrint('Stream interrupted due to max file size has being exceeded')
				# Stopped User is currently called because the individual file size exceeds fileMaxMB
			else:
				print("Stopped for unknown reason")
	debugPrint('Stream ran for %d Seconds' % (endTime - time.time()))
	qis.stopStream(module)
	debugPrint("Stream ran for %d's" % streamTime)
	debugPrint(qis.sendCmd(module, "Run Power down"), 1)
	# The above function is blocking and will wait until all data has been taken from the QIS buffer.
	debugPrint('Script: Finished Test 1. Data saved to \'Stream 6.txt\'')

def debugPrintSetup(setting, filename = 'QisExampleDebug.txt'):
	global FILENAME, f, debugPrintType
	if (setting == 'Command Line'):
		debugPrintType = 0
	elif(setting == 'File'):
		FILENAME = filename
		f = open(FILENAME, 'w')
		debugPrintType = 1

# debugPrint is used either store all responses for debugging or only print useful information to the console
def debugPrint(text, setting = 0):
	if (debugPrintType == 0 and setting == 0):
		print(text)
	elif (debugPrintType == 1):
		f.write(text)


# Calling the main() function
if __name__=="__main__":
	main()