'''
AN-012 - Application note demonstrating control of power modules via QIS

This example connects to all 6 ports of the QTL1995 and streams from them at the same time.

Data is saved to file(s) with each module being saved into a different file.  A file size limit
forces data to be stored into multiple smaller files.

########### VERSION HISTORY ###########

14/12/2016 - Iain Robertson - Minor edits for formatting and layout
24/04/2018 - Pedro Cruz     - Updated for QuarchPy
02/10/2018 - Matt Holsey    - Re-updated for QuarchPy

########### INSTRUCTIONS ###########

- Set the required streamDuration
- Set the 

For localhost QIS, run the example as it is.
For remote QIS, comment out the 'openQis()' command and specify the IP:Port in the qusInterface(...) command

####################################
'''
# Imports the necessary QuarchPy parts. 
from quarchpy import quarchDevice, quarchPPM, startLocalQis, isQisRunning, qisInterface

# Other imports.
import sys, os
import time


''' 
Set the filename, duration and file size limit here if you need
'''
fileNamePart = 'QisMultiDeviceExampleshort1'        # Output file name.
streamDuration = 10                                 # Stream duration [s].
fileSize = 2000                                     # Max file size [mb].
myDevice1 = "tcp:QTL1995-02-001-001"                # Set the ID of the modules to use here
myDevice2 = "tcp:QTL1995-02-001-002"
myDevice3 = "tcp:QTL1995-02-001-003"
myDevice4 = "tcp:QTL1995-02-001-004"
myDevice5 = "tcp:QTL1995-02-001-005"
myDevice6 = "tcp:QTL1995-02-001-006"


''' 
Main function to connect to the modules and begin streaming
'''
def main():

    # isQisRunning([host='127.0.0.1'], [port=9722]) returns True if QIS is running and False if not and start QIS locally.
    if isQisRunning() == False:
        startLocalQis()

    ##small delay to allow qis to scan for devices before connecting
    time.sleep(5)
        
    # Create Quarch Device with basic functions - each individual module requires a connection.
    quarchDevice1 = quarchDevice(myDevice1, ConType = "QIS", timeout = 20)
    quarchDevice2 = quarchDevice(myDevice2, ConType = "QIS", timeout = 20)
    quarchDevice3 = quarchDevice(myDevice3, ConType = "QIS", timeout = 20)
    quarchDevice4 = quarchDevice(myDevice4, ConType = "QIS", timeout = 20)
    quarchDevice5 = quarchDevice(myDevice5, ConType = "QIS", timeout = 20)
    quarchDevice6 = quarchDevice(myDevice6, ConType = "QIS", timeout = 20)

    # Upgrade the basic Quarch Devices to PPMs modules, adding specific functions.
    quarchHDppm1 = quarchPPM(quarchDevice1)
    quarchHDppm2 = quarchPPM(quarchDevice2)
    quarchHDppm3 = quarchPPM(quarchDevice3)
    quarchHDppm4 = quarchPPM(quarchDevice4)
    quarchHDppm5 = quarchPPM(quarchDevice5)
    quarchHDppm6 = quarchPPM(quarchDevice6)

    # Create a list with the PPM devices, and call the multi stream example.  This function blocks until the stream is complete so any custom code
    # you require needs to go within multiDeviceStreamExample
    quarchHDlist = [quarchHDppm1, quarchHDppm2, quarchHDppm3, quarchHDppm4, quarchHDppm5, quarchHDppm6]
    multiDeviceStreamExample(quarchHDlist)


    # Close the connections with each PPM device.
    quarchHDppm1.closeConnection()
    quarchHDppm2.closeConnection()
    quarchHDppm3.closeConnection()
    quarchHDppm4.closeConnection()
    quarchHDppm5.closeConnection()
    quarchHDppm6.closeConnection()

''' 
Runs multiple streams at once. This is suitable for a 6 way PPM or multiple individual power modules.  This is a blocking function, as it includes code to display
the instantaneous output of each port on screen, to demonstrate that additional actions can be undertaken while the stream is running.

You could also place your own code here to change the output voltage as part of a test, or perhaps to send commands and traffic to the drive.

- The first loop will set up the output mode for all the devices to 5V,  power up all the outputs if they are powered down and set up the stream.
it will return OK for each module successfully configured.

- The second loop will execute until "endTime". It starts the stream for each individual module and set up the data files, and enters a nested loop
that will print the power in each module. It closes the connection in each module after "endTime".

Your data files will be in the same directory of your script. 
'''
def multiDeviceStreamExample(quarchHDlist):

    # Print connected module information
    print("Running QIS multi-stream example.\n")
    
    print("Turning on the output in all modules and setting up the stream...")
      
    for module in quarchHDlist:
        # Print the serial number of each module.
        print("\nModule serial:"), 
        print(module.sendCommand("*serial?"))

        # Print the module number.
        print("  Ready? "),

        # Checks if 3V3 or 5V has automatically been set. If not, manually sets to 5V.
        if (module.sendCommand("Config Output Mode?") == "DISABLED"):
            module.sendCommand("Config Output Mode 5V")
            time.sleep(3)   # Requires at least 3 seconds between changing output voltage and powering up.
        
        # Sets the trigger mode such that the stream is controlled by the script.
        module.sendCommand("Record Trigger Mode Manual")
        # Set the averaging rage to one sample every ~0.25mS
        module.sendCommand("Record Averaging 64")

        # Checks device power state
        CurrentState = module.sendCommand("run power?")

        # If outputs are off, power it up.
        if CurrentState == "OFF":
            print(module.sendCommand("Run Power up"))
        else:
            print("OK")
     
        # Enables power calculations to be stored in file
        module.sendCommand("Stream Mode Power Enable")

    # Wait for user permission to start stream. Try and except to be compatible with both python 2 and 3
    try:
        raw_input("\nAll modules successfully configured, press enter to stream...\n")
    except:
        input("\nAll modules successfully configured, press enter to stream...\n")


    # Aux variables. 
    fileNameCount = 1
    startTime = time.time()
    endTime = startTime + streamDuration

    # Loop to create multiple files.
    while time.time() <= endTime:
        deviceNumber = 1

        # Set up and start the stream in all 6 modules.
        for module in quarchHDlist:
            # Define the file name.
            fileName = "%(1)s_%(2)d_%(3)d.txt" % {'1' : fileNamePart, '2': fileNameCount, '3': deviceNumber}
            # Start the stream.
            module.startStream(fileName, fileSize, 'Stream %d' % deviceNumber)
            deviceNumber += 1
        
        fileNameCount += 1

        # Keep streaming and printing the power while endTime is not reached.
        while time.time() <= endTime:
                   
            # Restart the screen after the readings and print the header.
            outputStr = ''
            os.system("cls")
            print("|  OUTPUT#  |  POWER 12V  |  POWER 5V  |")            
            print("----------------------------------------")
            
            # Measure the power in 5V and 12V channels and prints it.
            for module in quarchHDlist:
                power_5v = module.sendCommand("measure power 5v")
                power_12v = module.sendCommand("measure power 12v")

                sys.stdout.write("|{:^11}|{:^13}|{:^12}|\n".format(module.ConString[-1], power_12v, power_5v ) )
            
            sys.stdout.flush()

            time.sleep(1)

            # Checks if there's any problem with any of the streams.
            if module.streamInterrupt():
                break
        
        # After the endTime, close the connections with the modules.         
        for module in quarchHDlist:
            module.stopStream() 

            


# Call the main() function.
if __name__=="__main__":
    main()