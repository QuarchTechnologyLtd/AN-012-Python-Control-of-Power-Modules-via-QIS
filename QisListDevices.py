# QisListDevices.pu
# Iain Robertson - 14/12/2016
#
# Example demonstrating the use of QIS (Quarch Instrumentation Server) to find modules that can be controller
import sys, os

libpath = os.path.dirname(os.path.abspath(__file__))
libpath = os.path.join(libpath, "lib")
sys.path.insert( 0, os.path.join(libpath,os.path.normpath('QisInterface')) )
# The above is required if the QisInterface file is not in the same directory as this script

import QisInterface	# Import the QisInterface file.

# If QIS is running on a remote host, replace with its local address
localHost =  '127.0.0.1'

qis = QisInterface.QisInterface(localHost) 	# Create an instance of QisInterface. Before this is ran QIS needs to have been started

devList = qis.getDeviceList()

print ''
print 'List of devices attached to QIS:\n'
for el in devList:
	print '    ' + el