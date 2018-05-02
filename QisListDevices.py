'''
AN-012 - Application note demonstrating control of power modules via QIS

This example checks everything is working by connecting to QIS and listing the devices
available for connection.  This verifies QuarchPy, QIS and the connection to the module(s)

########### VERSION HISTORY ###########

14/12/2016 - Iain Robertson	- Minor edits for formatting and layout
24/04/2018 - Andy Norrie	- Updated for QuarchPy

########### INSTRUCTIONS ###########

For localhost QIS, run the example as it is.
For remote QIS, comment out the 'openQis()' command and specify the IP:Port in the qusInterface(...) command

####################################
'''
from quarchpy import qisInterface, isQisRunning, startLocalQis

# isQisRunning([host='127.0.0.1'], [port=9722]) returns True if QIS is running and False if not.
if isQisRunning() == False:
    startLocalQis()

# Connect to the localhost QIS instance - you can also specify host='127.0.0.1' and port=9722 for remote control.
myQis = qisInterface()

# Request a list of all USB and LAN accessable modules
devList = myQis.getDeviceList()

# Print the devices
print ("\nList of devices attached to QIS:\n")
for device in devList:
	print (device)