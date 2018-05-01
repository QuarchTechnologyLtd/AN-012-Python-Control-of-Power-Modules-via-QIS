from quarchpy import quarchDevice, startLocalQIS

# Comment this line if you are running QIS remotely. 
startLocalQIS()

quarchDevice = quarchDevice("tcp:1995-02-002-001", ConType = "QIS")

print(quarchDevice.sendCommand("*idn?"))

quarchDevice.closeConnection()