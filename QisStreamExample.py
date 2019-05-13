'''
AN-012 - Application note demonstrating control of power modules via QIS

This example demonstrates several different control actions on power modules
Examples include sending commands and recording to file

- Power margining
- Simple stream example
- Arbitrary timebase re-sampling example

########### VERSION HISTORY ###########

20/09/2017 - Tom Pope       - First version
24/04/2018 - Andy Norrie    - Updated for QuarchPy
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
myDeviceID = "usb::QTL1824-03-201"

def main():

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
    myQuarchDevice = quarchDevice (myDeviceID, ConType = "QIS")
    # Convert the base device to a power device
    myPowerDevice = quarchPPM (myQuarchDevice)
    
    # Select one or more example functions to run
    powerMarginingExample (myPowerDevice)
    simpleStreamExample (myPowerDevice)
    averageStreamExample (myPowerDevice)

''' 
Performs a simple power margining routine printing results to console or a file
This reduces each rail in turn over a number of steps, and measures the voltage and current
at each step
'''
def powerMarginingExample(module):
    # Prints out connected module information
    print ("Running QIS POWER MARGINING Example")
    print ("Module Name:")
    print (module.sendCommand ("hello?"))
    
    # Output mode is set automatically on HD modules using an HD fixture, otherwise we will chose 3v3 mode for this example
    if (module.sendCommand ("config:output Mode?") == "DISABLED"):
        print ("Either using an HD without an intelligent fixture or an XLC. Manually setting voltage to 3v3")
        print (module.sendCommand ("config:output:mode 3V3"))
    
    # Check the state of the module and power up if necessary
    print ("Checking the state of the device and power up if necessary")
    powerState = module.sendCommand ("run power?")
    print ("State of the Device: " + (powerState))    
    # If outputs are off
    if powerState == "OFF":
        # Power Up
        print (module.sendCommand ("run:power up"))
    
    print ("Running power margining test:")
    print ("Margining results for 12V rail")
    
    # Loop through 6 different voltage levels, reducing by 200mV on each loop
    testVoltage = 12000
    for i in range(6):
        
        # Set the new voltage level
        print  (module.sendCommand ("Signal 12V Voltage %d" % testVoltage))
        
        # Wait for voltage rails to settle at the new level
        time.sleep(1)
        
        # Request and print the voltage and current measurements
        print (module.sendCommand ("measure:voltage 12v?"))
        print (module.sendCommand ("measure:current 12v?"))
        
        # Decreasing the testVoltage by 200mV
        testVoltage -= 200
    
    # Set the 12V level back to default
    print ("Setting the 12V rail back to default state")
    print (module.sendCommand ("signal:12v:voltage 12000"))
    testVoltage = 3300
    print ("Margining results 3V3 rail")
    for i in range(6):
        
        # Set the new voltage level
        print (module.sendCommand ("signal:3v3:voltage %d" % testVoltage))
        
        # Wait for voltage rails to settle at the new level
        time.sleep(1)
        
        # Request and print the voltage and current measurements
        print (module.sendCommand ("measure:voltage 3v3?"))
        print (module.sendCommand ("measure:current 3v3?"))
        
        # Decreasing the testVoltage by 100mV
        testVoltage -= 100
    
    # Set the outputs back to default and power down
    print ("Setting the 3V3 rail back to default state")
    print (module.sendCommand ("signal:3v3:voltage 3300"))    
    print (module.sendCommand ("run:power down"))
    
    print ("ALL DONE!")

'''
This example streams measurement data to file, by default in the same folder as the script
'''
def simpleStreamExample(module):
    # Prints out connected module information
    print ("Running QIS SIMPLE STREAM Example")
    print ("Module Name:")
    print (module.sendCommand ("hello?"))
    
    # Output mode is set automatically on HD modules using an HD fixture, otherwise we will chose 3v3 mode for this example
    if (module.sendCommand ("config:output Mode?") == "DISABLED"):
        print ("Either using an HD without an intelligent fixture or an XLC. Manually setting voltage to 3v3")
        print (module.sendCommand ("config:output:mode 3V3"))
    
    # Sets for a manual record trigger, so we can start the stream from the script
    print (module.sendCommand ("record:trigger:mode manual"))
    # Use 4k averaging (around 1 measurement every 32mS)
    print (module.sendCommand ("record:averaging 8k"))
    
    # In this example we write to a fixed path
    module.startStream('Stream1.txt', 2000, 'Example stream to file')    
    
    # Sleep for 2 seconds to ensure good data before it tries to start up.
    time.sleep(2)

    # Check the state of the module and power up if necessary
    print ("Checking the state of the device and power up if necessary")
    powerState = module.sendCommand ("run power?")
    print ("State of the Device: " + (powerState))    
    # If outputs are off
    if powerState == "OFF":
        # Power Up
        print (module.sendCommand ("run:power up"))
    
    # Delay for a x seconds while the stream is running.  You can also continue
    # to run your own commands/scripts here while the stream is recording in the background    
    print ("*** Sleep here for a while to allow stream data to record to file")
    time.sleep(20)
    
    
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
    module.stopStream ()
    
    # Power down the outputs    
    print (module.sendCommand ("run:power down"), False)    

'''
This example is identical to the simpleStream() example, except that we use the additional QIS
averaging system to re-sample the stream to an arbitrary timebase
'''
def averageStreamExample(module):
    # Prints out connected module information
    print ("Running QIS RESAMPLING Example")
    print ("Module Name:")
    print (module.sendCommand ("hello?"))
    
    # Output mode is set automatically on HD modules using an HD fixture, otherwise we will chose 3v3 mode for this example
    if (module.sendCommand ("config:output Mode?") == "DISABLED"):
        print ("Either using an HD without an intelligent fixture or an XLC. Manually setting voltage to 3v3")
        print (module.sendCommand ("config:output:mode 3V3"))
    
    # Sets for a manual record trigger, so we can start the stream from the script
    print (module.sendCommand ("record:trigger:mode manual"))
    # Set an initial averaging, a bit faster than the final resolution we want
    print (module.sendCommand ("record:averaging 16k"))
    
    # SET RESAMPLING HERE
    # This tells QIS to re-sample the data at a new timebase of 1 samples per second
    print ("Setting QIS resampling to 1000mS")
    module.streamResampleMode ("1000ms")
    
    # In this example we write to a fixed path
    module.startStream('Stream1_resampled.txt', '1000', 'Example stream to file with resampling')    
    
    # Sleep for 2 seconds to ensure good data before it tries to start up.
    time.sleep(2)

    # Check the state of the module and power up if necessary
    print ("Checking the state of the device and power up if necessary")
    powerState = module.sendCommand ("run power?")
    print ("State of the Device: " + (powerState))    
    # If outputs are off
    if powerState == "OFF":
        # Power Up
        print (module.sendCommand ("run:power up"))
    
    # Delay for 30 seconds while the stream is running.  You can also continue
    # to run your own commands/scripts here while the stream is recording in the background    
    time.sleep(30)
    
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
    module.stopStream ()
    # Power down the outputs    
    print (module.sendCommand ("run:power down"), False)   

# Calling the main() function
if __name__=="__main__":
    main()