'''
AN-012 - Application note demonstrating control of power modules via QIS

This example demonstrates the ability of the module to run multiple streams in a row.
This might be used when several work loads are being run on a drive, and each is to be logged seperately

########### VERSION HISTORY ###########

14/12/2016 - Iain Robertson - First version
24/04/2018 - Andy Norrie    - Updated for QuarchPy
02/10/2018 - Matt Holsey    - Re-updated for QuarchPy

########### INSTRUCTIONS ###########

1. Select the connection ID of the module you want to use
2. Comment in/out the test function that you want to run in the main() function)

####################################
'''

# Imports the necessary QuarchPy parts. 
import quarchpy
from quarchpy.qis import *
from quarchpy import quarchDevice, quarchPPM, startLocalQis, isQisRunning, qisInterface

# Other imports.
import sys, os
import time

'''
Select the device you want to connect to here!
'''
fileNamePart = 'MultiStreamExampleData'     # File name base
seconds = 20                                # Number of seconds to stream for on each cycle

def main():

    # Version 2.0.0 or higher expected for this appliation note
    quarchpy.requiredQuarchpyVersion ("2.0.0")

    # isQisRunning([host='127.0.0.1'], [port=9722]) returns True if QIS is running and False if not and start QIS locally.
    if isQisRunning() == False:
        startLocalQis()

    # Connect to the localhost QIS instance - you can also specify host='127.0.0.1' and port=9722 for remote control.
    myQis = qisInterface()

    # small sleep to allow qis to scan for devices
    time.sleep(5)

    # Request a list of all USB and LAN accessible modules
    myDeviceID = myQis.GetQisModuleSelection()

    # Specify the device to connect to, we are using a local version of QIS here, otherwise specify "QIS:192.168.1.101:9722"
    myQuarchDevice = quarchDevice (myDeviceID, ConType = "QIS", timeout=20)
    # Convert the base device to a power device
    module = quarchPPM (myQuarchDevice)

    # Prints out connected module information
    print ("Running QIS MULTIPLE STREAM Example")
    print ("Module Name:")
    print (module.sendCommand ("hello?"))
    
    # Output mode is set automatically on HD modules using an HD fixture, otherwise we will chose 3v3 mode for this example
    if (module.sendCommand ("config:output Mode?") == "DISABLED"):
        print ("Either using an HD without an intelligent fixture or an XLC. Manually setting voltage to 3v3")
        print (module.sendCommand ("config:output:mode 5v"))
    
    # Sets for a manual record trigger, so we can start the stream from the script
    print (module.sendCommand ("record:trigger:mode manual"))
    # Use 4k averaging (around 1 measurement every 32mS)
    print (module.sendCommand ("record:averaging 8k"))

    # Check the state of the module and power up if necessary
    print ("Checking the state of the device and power up if necessary")
    powerState = module.sendCommand ("run power?")
    print ("State of the Device: " + (powerState))    
    # If outputs are off
    if powerState == "OFF":
        # Power Up
        print (module.sendCommand ("run:power up"))
        time.sleep(2)

    fileNameCount = 1
    # Loop to create multiple stream files (5 in this example)
    while fileNameCount < 6:
    
        # Create the current file name then increment file counter
        fileName = fileNamePart + str(fileNameCount) + '.txt'
        fileNameCount+=1
        
        # Start the strean
        module.startStream(fileName, 2000, 'Example stream to file')

        # Module is now recording data to file. It will stop when stopStream () is executed, or when a buffer fills
        # In the meantime this thread continues to run with the recording thread running in the backgroud.
    
        #Loop for the set time (roughly timed in this example), recording data, 
        count = 0        
        while count < seconds:  
            # Count up the total stream time
            time.sleep(0.5)
            count += 0.5
            streamStatus = module.streamRunningStatus()#(device=module)
            
            # Print the backend buffer status (used stripes out of total backend buffer size) as a way to view the progress of the stream
            print ('Script: ' + str(count) + ' out of ' + str(seconds)  +  '. Backend buffer status: Used ' + module.streamBufferStatus() + '. Stream State: ' + streamStatus)
            
            # Check for an overrun and break if found. This will stop the current stream and allow a new one to be started            
            if module.streamInterrupt():
                break
        
        # Stop the stream.  This command will block until the buffered stream data has been pulled from the module
        module.stopStream()
        
        #pause to allow stop / start stream
        time.sleep(1)
    #buffer remaining stripes have been copied to file,
    #and if averaging was low a large amount of data can be in the backends buffer
    print ('')
    print ('Script: Finished Test 1. Data saved to \'' + fileName +'\'')
	
if __name__=="__main__":
    main()
    