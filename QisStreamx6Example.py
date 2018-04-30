# Imports the necessary QuarchPy parts. 
from quarchpy import quarchDevice, quarchPPM, startLocalQIS

# Other imports.
import sys, os
import time

############ EDIT HERE. 
fileNamePart = 'QisMultiDeviceExampleshort1'    # Output file name.
streamDuration = 10     # Stream duration [s].
fileSize = 2000     # Max file size [mb].
#######################


''' Main function should call functions after openning the connections with the devices and before closing it. 
'''
def main():

    # Start a local instance of QIS. If you want to connect to a remote QIS, comment this line. 
    startLocalQIS()

    # Create Quarch Device with basic functions - each individual module requires a connection.
    quarchDevice1 = quarchDevice("tcp:1995-02-005-001", ConType = "QIS")
    quarchDevice2 = quarchDevice("tcp:1995-02-005-002", ConType = "QIS")
    quarchDevice3 = quarchDevice("tcp:1995-02-005-003", ConType = "QIS")
    quarchDevice4 = quarchDevice("tcp:1995-02-005-004", ConType = "QIS")
    quarchDevice5 = quarchDevice("tcp:1995-02-005-005", ConType = "QIS")
    quarchDevice6 = quarchDevice("tcp:1995-02-005-006", ConType = "QIS")

    # Upgrade the basic Quarch Devices to PPMs modules, adding specific functions.
    quarchHDppm1 = quarchPPM(quarchDevice1)
    quarchHDppm2 = quarchPPM(quarchDevice2)
    quarchHDppm3 = quarchPPM(quarchDevice3)
    quarchHDppm4 = quarchPPM(quarchDevice4)
    quarchHDppm5 = quarchPPM(quarchDevice5)
    quarchHDppm6 = quarchPPM(quarchDevice6)

    # Create a list with the PPM devices. 
    quarchHDlist = [quarchHDppm1, quarchHDppm2, quarchHDppm3, quarchHDppm4, quarchHDppm5, quarchHDppm6]

    # All functions using PPM devices should be called after the connections are opened and before they are closed.
    multiDeviceStreamExample(quarchHDlist)

    # Close the connections with each PPM device.
    quarchHDppm1.closeConnection()
    quarchHDppm2.closeConnection()
    quarchHDppm3.closeConnection()
    quarchHDppm4.closeConnection()
    quarchHDppm5.closeConnection()
    quarchHDppm6.closeConnection()

    
''' Runs multiple streams at once. This is suitable for a 6 way PPM or multiple individual power modules.

- The first loop will set up the output mode for all the devices to 5V,  power up all the outputs if they are powered down and set up the stream.
it will return OK for each module sucessfully configured.

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

    # Wait for user permission to start stream.
    raw_input("\nAll modules successfully configured, press enter to stream...\n")

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

        module.streamingStopped()				


# Call the main() function.
if __name__=="__main__":
    main()