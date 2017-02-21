# QisListDevices.pu
# Iain Robertson - 14/12/2016
#
# Example demonstrating the use of QIS (Quarch Instrumentation Server) to find modules that can be controller

import QisInterface #Import the QisInterface file. Doing it with 'import QisInterface' requires it to be in the same directory or in path.

host =  '127.0.0.1'
port = 9722
qis = QisInterface.QisInterface(host=host, port=port) # Create an instance of QisInterface. Before this is ran the QuarchBackEnd needs to have been started
devList = qis.getDeviceList()

print ''
print 'List of devices attached to backend @ ' + host + ':' + str(port) + ' :\n'
for el in devList:
	print '    ' + el