# QisStreamExample.py
# Iain Robertson - 14/12/2016
#
# Examples using QIS (Quarch Instrumentation Server) to stream data from a Quarch Power Module
import sys, os

libpath = os.path.dirname(os.path.abspath(__file__))
libpath = os.path.join(libpath, "lib")
sys.path.insert( 0, os.path.join(libpath,os.path.normpath('QisInterface')) )

import QisInterface #Import the Quarch QisInterface module which gives an interface to the QuarchBackEnd Java program
import time  #To use sleep
import sys    #To get args

""" Create an instance of QisInterface. Before this is ran the QuarchBackEnd needs to have been started """
# The backend can be ran on a different computer so long as network access is available and the correct details given.
qis = QisInterface.QisInterface(host='127.0.0.1', port=9722)

""" A module connected to the backend has to be specified as the streaming device, get it from arg1 """
try:
	module = sys.argv[1]
	res = qis.sendAndReceiveCmd(cmd='hello?', device=module)
	if 'Invalid' in res:
		print 'Module with name "' + module + '" not found.'
		raise
except:
	print 'Usage: \'python QisStreamExample.py DEVICE_ID\' where DEVICE_ID is the backend device name (e.g. tcp::qtl1995-01-012) of the module you wish to talk to.'
	print 'Try running QisListDevices.py to get a list of devices attached to backend.'
	exit()
print ''
print 'Script: Using module: ' + module + '\n'

""" Setup module """
#Start with module powered down and set to 3V3 mode to be safe. If using a 5V device change this.
print 'Script: ' +  qis.sendAndReceiveCmd(cmd='power down', device=module)
print 'Script: ' +  qis.sendAndReceiveCmd(cmd='conf out mode 3v3', device=module)
print 'Script: ' +  qis.sendAndReceiveCmd(cmd='conf stream ena on', device=module)	#HD PPM only
print 'Script: ' +  qis.sendAndReceiveCmd(cmd='rec trig mode manual', device=module)
print ''
print 'Script: Starting Test'
fileName = 'StreamExampleData.txt'
avgString = '32' #Increasing averaging done onboard the module reduces the amount of data to be transfered back but also reduces the detail in the data
print 'Script: ' +  qis.sendAndReceiveCmd(cmd='rec ave ' + avgString, device=module)

""" Start streaming """
qis.startStream(module, streamName='Test 1', fileName=fileName, fileMaxMB=2000)
#Module is now recording data to file. It will stop when qis.stopStream(module) is executed, or when a buffer fills
#In the meantime this thread continues to run with the recording thread running in the backgroud.

""" Do some things while recording as an example of running a test """
time.sleep(2)
print 'Script: ' +  qis.sendAndReceiveCmd(cmd='power up', device=module) #Switch module outputs on
#Loop for a while, while recording data, 
count = 0
seconds = 5 #approx number of seconds to loop and record for after power up and initial delay
while count < seconds:	
	time.sleep(1)
	count=count+1
	#Print the backend buffer status (used stripes out of total backend buffer size) if this fills new data is discarded
	print 'Script: ' + str(count) + ' out of ' + str(seconds)  +  '. Backend buffer status: Used ' + qis.streamBufferStatus(device=module)
	
""" Stop recording """
qis.stopStream(module) #This function can block for a while as it only returns once the backends
#buffer remaining stripes have been copied to file,
#and if averaging was low a large amount of data can be in the backends buffer
print ''
print 'Script: Finished Test 1. Data saved to \'' + fileName +'\''