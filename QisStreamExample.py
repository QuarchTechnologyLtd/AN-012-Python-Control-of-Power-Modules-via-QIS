'''
AN-012 - Application note demonstrating control of power modules via QIS

This example demonstrates several different control actions on power modules
Examples include sending commands and recording to file

- Power margining
- Simple stream example
- Arbitrary timebase re-sampling example

########### VERSION HISTORY ###########

20/09/2017 - Tom Pope	    - First version
24/04/2018 - Andy Norrie	- Updated for QuarchPy
02/10/2018 - Matt Holsey    - Re-updated for QuarchPy

########### INSTRUCTIONS ###########

1. Select the connection ID of the module you want to use
2. Comment in/out the test function that you want to run in the main() function)

####################################
'''
import sys, os
import time
from quarchpy import quarchDevice, quarchPPM, startLocalQis, isQisRunning, qisInterface

'''
Select the device you want to connect to here!
'''
myDeviceID = "usb::QTL1999-02-004"

def main():

    # isQisRunning([host='127.0.0.1'], [port=9722]) returns True if QIS is running and False if not and start QIS locally.
    if isQisRunning() == False:
        startLocalQis()

    # Specify the device to connect to, we are using a local version of QIS here, otherwise specify "QIS:192.168.1.101:9722"
    myQuarchDevice = quarchDevice (myDeviceID, ConType = "QIS")
    # Convert the base device to a power device
    myPowerDevice = quarchPPM (myQuarchDevice)
    print (module.sendCommand ("hello?"))

# Calling the main() function
if __name__=="__main__":
    main()