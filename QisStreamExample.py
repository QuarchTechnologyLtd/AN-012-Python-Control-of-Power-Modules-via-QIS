'''
AN-012 - Application note demonstrating control of power modules via QIS

This example demonstrates several different control actions on power analysis modules

- Simple stream example
- Arbitrary timebase re-sampling example

########### VERSION HISTORY ###########

15/10/2018 - Pedro Cruz     -  First Version
12/05/2012 - Matt Holsey    - Bug fixed - check stream is stopped before continuing with script

########### INSTRUCTIONS ###########

1. Select the connection ID of the module you want to use
2. Comment in/out the test function that you want to run in the main() function)

####################################
'''
import time

from quarchpy.connection_specific.connection_QIS import QisInterface
from quarchpy.device import quarchDevice, getQuarchDevice, quarchPPM
from quarchpy.qis import startLocalQis, isQisRunning, closeQis
from quarchpy.user_interface.user_interface import quarchSleep

'''
Select the device you want to connect to here!
'''

def main():

    # isQisRunning([host='127.0.0.1'], [port=9722]) returns True if QIS is running and False if not and start QIS locally.
    closeQisAtEndOfTest=False
    if isQisRunning() == False:
        startLocalQis()
        closeQisAtEndOfTest=True # QIS will only be closed if it was launched by this script and left open otherwise.

    # Connect to the localhost QIS instance - you can also specify host='127.0.0.1' and port=9722 for remote control.
    myQis = QisInterface()

    # small sleep to allow qis to scan for devices
    quarchSleep(5)

    # Request a list of all USB and LAN accessible modules
    myDeviceID = myQis.GetQisModuleSelection()
    listOfModules = myQis.qis_scan_devices()
    # Specify the device to connect to, we are using a local version of QIS here, otherwise specify "QIS:192.168.1.101:9722"
    myQuarchDevice = getQuarchDevice(myDeviceID, ConType = "QIS")
    # Convert the base device to a power device
    myPowerDevice = quarchPPM(myQuarchDevice)
    
    # Select one or more example functions to run
    simpleStreamExample (myPowerDevice)
    averageStreamExample (myPowerDevice)

    if closeQisAtEndOfTest==True:
        closeQis()

'''
This example streams measurement data to file, by default in the same folder as the script
'''
def simpleStreamExample(module):
    # Prints out connected module information
    print ("Running QIS SIMPLE STREAM Example")
    print ("Module Name: " + module.sendCommand ("hello?"))

    # Sets for a manual record trigger, so we can start the stream from the script
    print ("Set manual Trigger: " + module.sendCommand ("record:trigger:mode manual"))
    # Use 4k averaging (around 1 measurement every 32mS)
    print ("Set averaging: " + module.sendCommand ("record:averaging 32k"))
    
    # In this example we write to a fixed path
    module.startStream('Stream1.csv', 2000, 'Example stream to file')

    # Delay for a x seconds while the stream is running.  You can also continue
    # to run your own commands/scripts here while the stream is recording in the background    
    print ("*** Sleep here for a while to allow stream data to record to file")
    quarchSleep(30)
    
    # Check the stream status, so we know if anything went wrong during the stream
    streamStatus = module.streamRunningStatus()
    if ("Stopped" in streamStatus):
        if ("Overrun" in streamStatus):
            print ('Stream interrupted due to internal device buffer has filled up')
        elif ("User" in streamStatus):
            print ('Stream interrupted due to max file size has being exceeded')            
        else:
            print("Stopped for unknown reason")

    # Stop the stream.  This function is blocking and will wait until all remaining data has
    # been downloaded from the module
    module.stopStream()

    # check to ensure stream is fully stopped before continuing script
    while not "stopped" in str(module.streamRunningStatus()).lower():
        time.sleep(1)



'''
This example is identical to the simpleStream() example, except that we use the additional QIS
averaging system to re-sample the stream to an arbitrary timebase
'''
def averageStreamExample(module):
    # Prints out connected module information
    print ("Running QIS RESAMPLING Example")
    print ("Module Name: " + module.sendCommand ("hello?"))

    # Sets for a manual record trigger, so we can start the stream from the script
    print ("Set manual Trigger: " + module.sendCommand ("record:trigger:mode manual"))
    # Use 16k averaging as this is a bit faster than we require
    print ("Set averaging: " + module.sendCommand ("record:averaging 16k"))
    
    # SET RESAMPLING HERE
    # This tells QIS to re-sample the data at a new timebase of 1 samples per second
    print ("Setting QIS resampling to 1000mS")
    module.streamResampleMode ("1000ms")
    
    # In this example we write to a fixed path
    module.startStream('Stream1_resampled.csv', '1000', 'Example stream to file with resampling')    

    # Delay for 30 seconds while the stream is running.  You can also continue
    # to run your own commands/scripts here while the stream is recording in the background    
    quarchSleep(30)
    
    # Check the stream status, so we know if anything went wrong during the stream
    streamStatus = module.streamRunningStatus()
    if ("Stopped" in streamStatus):
        if ("Overrun" in streamStatus):
            print('Stream interrupted due to internal device buffer has filled up')
        elif ("User" in streamStatus):
            print('Stream interrupted due to max file size has being exceeded')
        else:
            print("Stopped for unknown reason")

    # Stop the stream.  This function is blocking and will wait until all remaining data has
    # been downloaded from the module
    module.stopStream()

# Calling the main() function
if __name__=="__main__":
    main()