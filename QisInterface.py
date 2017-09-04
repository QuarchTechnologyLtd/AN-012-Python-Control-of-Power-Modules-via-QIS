import socket
import re
import time
import sys
import os
import datetime
import select
import threading

#QisInterface provides a way of connecting to a Quarch backend running at the specified ip address and port, defaults to localhost and 9722
class QisInterface:
	def __init__(self, host='127.0.0.1', port=9722):
		self.host = host
		self.port = port
		self.maxRxBytes = 4096
		self.sock = None		
		self.t1 = threading.Thread() #Thread that the stream loop runs in
		self.threadRunEvent = threading.Event() #Threading event that indicates if the thread loop should stop or continue				
		self.threadStreamRunSentEvent = threading.Event()
		self.threadStreamLoopEndedEvent = threading.Event()
		self.connect()		
	# Connect() tries to open a socket  on the host and port specified in the objects variables
	# If successful it returns the backends welcome string. If it fails it returns a string saying unable to connect
	# The backend should be running and host and port set before running this function. Normally it should be called at the beggining
	# of talking to the backend and left open until finished talking when the disconnect() function shuld be ran
	def connect(self):
		try:			
			self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.sock.connect((self.host, self.port))
			self.sock.settimeout(5)
			#clear packets
			try:
				welcomeString =self.sock.recv(self.maxRxBytes).rstrip()
				welcomeString = 'Connected@' + self.host + ':' + str(self.port) + ' ' + '\n    ' + welcomeString
				return welcomeString
				#print welcomeString
			except:
				print
				print ('No welcome received. Unable to connect to Quarch backend on specified host and port (' + self.host + ':' + str(self.port) + ')')
				print ('Is backend running and host accessible?')				
				print
				raise
		except:
			print
			print ('Unable to connect to Quarch backend on specified host and port (' + self.host + ':' + str(self.port) + ').')
			print ('Is backend running and host accessible?')
			print
			raise		
	# Tries to close the socket to specified host and port.
	def disconnect(self):
		res = 'Disconnecting from backend'
		try:
			self.sock.shutdown(socket.SHUT_RDWR)
			self.sock.close()
		except:			
			exc_type, exc_obj, exc_tb = sys.exc_info()
			fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
			print ('Unable to end connection. ' + self.host + ':' + str(self.port) + ' \r\n' + str(exc_type) + ' ' + str(fname) + ' ' + str(exc_tb.tb_lineno))
			raise				
		return res						
	
	def startStream(self, module, fileName='streamData.txt', fileMaxMB=2000, streamName='Stream With No Name'):
		#Clear the event used for signalling the stream loop to end  
		self.threadRunEvent.clear()
		self.threadStreamRunSentEvent.clear()
		#Create the thread		
		self.t1 = threading.Thread(target=self.startStreamThread, args=(module, fileName, fileMaxMB, streamName))                
		#Start the thread        
		self.t1.start()		
		#Don't return until rec stream has been issued
		while not self.threadStreamRunSentEvent.isSet():
			donothing = 1
		time.sleep(0.1)
		
	def stopStream(self, module):	
		try:
			#print '!!!!!!!!!!!!!!!!! stopStream !!!!!!!!!!!!!!!!'
			self.threadRunEvent.set()
			time.sleep(0.1)			
			# Wait until tge stream thread is finished before returning to user.
			# This means this function will block until the QIS buffer is emptied by the second while loop in startStreanThread. 
			# This may take some time, especially at low averaging but should gurantee the data won't be lost and QIS buffer is emptied.
			while self.t1.isAlive():
				time.sleep(0.5)
			#print '!!!!!!!!!!!!!!!!! T1 IS OVER !!!!!!!!!!!!!!!!'
			#try to make sure thread is really over before returning
			time.sleep(0.1)
		except:
			print '!!!!!!!!!!!!!!!!!!  stopStream exception !!!!!!!!!!!!!!!!!!'
			raise
		
	# This is the function that is ran when t1 is created. It is ran in a seperate thread from the main application so streaming can
	# happen without blocking the main application from doing other things.
	# Within this function/thread you have to be very careful not to try and 'communicate'  with anything from other threads. If you do
	# you MUST use a thread safe way of communicating. The thread creates it's own socket and should use that NOT the objects socket
	# (which some of the comms with module functions will use by default).
	def startStreamThread(self, module, fileName='streamData.txt', fileMaxMB=2000, streamName='Stream With No Name'):
		#Create a new socket and connect to back end
		try:			
			streamSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			streamSock.connect((self.host, self.port))
			streamSock.settimeout(5)
			#clear packets
			try:
				welcomeString = streamSock.recv(self.maxRxBytes).rstrip()
			except:						
				raise
		except:					
			raise

		#Start module streaming and then read stream data
		try:			
			stripes = ['Empty Header']			
			#Send stream command so module starts streaming data into the backends buffer
			streamRes = self.sendAndReceiveCmd(streamSock, 'rec stream', device=module)
			print streamRes
			if ('rec stream : OK' in streamRes):
				self.threadStreamRunSentEvent.set()
			else:
				print 'FAILED TO START STREAM'
				return
			#If recording to file then get header for file
			if(fileName is not None):
				averaging = self.streamHeaderAverage(device=module, sock=streamSock)
				count=0
				maxTries=10
				while 'Header Not Available' in averaging:
					averaging = self.streamHeaderAverage(device=module, sock=streamSock)
					time.sleep(0.1)
					count = count +1
					if count > maxTries:
						print 'PPM header not available. Exiting'	
						exit()						
				version =  self.streamHeaderVersion(device=module, sock=streamSock)
				sampleRate = 250000 #adc samples / sec
				stripeRate = sampleRate /  float(averaging) #stripes / sec			
				with open(fileName, 'w') as f:
					timeStampHeader = datetime.datetime.now().strftime("%H:%M:%S:%f %d/%m/%y")							
					formatHeader = self.streamHeaderFormat(device=module, sock=streamSock)					
					f.write(streamName + ', ' + version + ', ' + module + ', ' + timeStampHeader + ', avg=' + str(averaging) + ' samples per stripe, stripeRate=' + str(stripeRate) + ' stripes per second\n')
					f.write(formatHeader + '\n')
			numStripesPerRead = 4096
			maxFileExceeded = False
			openAttempts = 0
			isRun = 0
			while isRun == 0:
				try:
					with open(fileName, 'a') as f:
						fileMB = 0
						fileRaw = 0
						#Until the event threadRunEvent is set externally to this thread, loop and read from the stream	
						while not self.threadRunEvent.isSet():
							newStripes = self.streamGetStripesText(streamSock, module, numStripesPerRead)
							#time.sleep(0.1)
							
							#Check file size isn't too big
							if len(newStripes) > 0:
								#fileRaw += len(newStripes)
								#fileMBAdd = fileRaw >> 20
								#if (fileMBAdd > 0):
								#	fileMB += fileMBAdd
								#	fileRaw -= fileMBAdd * 1048576
								#Writes in file if not too big else stops streaming
								#if fileMB < fileMaxMB:									
								for s in newStripes:
									f.write(s + '\n')
									#time.sleep(0.01)
								#else:
								#	maxFileExceeded = True
								#	print 'QisInterface file size exceeded  in loop 1 - breaking'
								#	maxFileStatus = self.streamBufferStatus(device=module)
								#	time.sleep(0.1)
								#	break
							else:
								#print '!!!!!!!!!!!!!!!!!!!  GOT NO STRIPES  !!!!!!!!!!!!!!!!'	
								# there's no stripes in the buffer - it's not filling up fast - sleeps so we don't spam qis with requests (seems to make QIS crash)
								# it might be clever to change the sleep time accoring to the situation e.g. wait longer with higher averaging or lots of no stripes in a row
								#time.sleep(0.3)								
								#print ('  !!!!!!!!!!!!GOT NO STRIPES  !!!!!!!!!!!!!')
								streamStatus = self.streamRunningStatus(device=module, sock=streamSock)
								time.sleep(0.3)
								if ("Overrun" in streamStatus):
									print 'QisInterface overrun - breaking'
						#print 'THREAD LOOP EXITED'
						
						print self.sendAndReceiveCmd(streamSock, 'rec stop', device=module)
						time.sleep(0.2)
						
						#If the backend buffer still has data then keep reading it out
						print 'Streaming stopped. Emptying data left in QIS buffer to file (' + self.streamBufferStatus(device=module, sock=streamSock) + ')'
						time.sleep(0.1)
						newStripes = self.streamGetStripesText(streamSock, module, numStripesPerRead)
						time.sleep(0.1)
						while len(newStripes) > 0:						
							#print '2nd loop len newStripes='+str(len(newStripes))							
							fileRaw += len(newStripes)
							fileMBAdd = fileRaw >> 20
							if (fileMBAdd > 0):
								fileMB += fileMBAdd
								fileRaw -= fileMBAdd * 1048576
								
							if fileMB < fileMaxMB:
								for s in newStripes:
									f.write(s + '\n')
							else:
								if not maxFileExceeded:
									maxFileStatus = self.streamBufferStatus(device=module,  sock=streamSock)
									maxFileExceeded = True																												
							time.sleep(0.01) #reduce speed of loop to stop spamming qis
							newStripes = self.streamGetStripesText(streamSock, module, numStripesPerRead)
							
						if maxFileExceeded:
							f.write('Warning: Max file size exceeded before end of stream.\n')
							f.write('Unrecorded stripes in buffer when file full: ' + maxFileStatus + '.')		
							print 'Warning: Max file size exceeded. Some data has not been saved to file: ' + maxFileStatus + '.'								
						print 'Stripes in buffer now: ' + self.streamBufferStatus(device=module, sock=streamSock)
						isRun = 1
				except IOError:
					print '\n\n!!!!!!!!!!!!!!!!!!!! IO Error in QisInterface !!!!!!!!!!!!!!!!!!!!\n\n'
					time.sleep(0.5)
					openAttempts += 1
					if openAttempts > 4:
						isRun = 1
						raise
		except:
			raise			
		#Close streams socket
		try:
			streamSock.shutdown(socket.SHUT_RDWR)
			streamSock.close()
		except:			
			raise
			
	# Send text and get the backends response. - acts as wrapper to the sendAndReceiveText, intended to provide some extra convenience
	# when sending commands to module (as opposed to back end)
	# If read until cursor is set to True (which is default) then keep reading response until a cursor is returned as the last character of result string
	# After command is sent wait for betweenCommandDelay which defaults to 0 but can be specified to add a delay between commands
	# The objects connection needs to be opened (connect()) before this is used
	def sendAndReceiveCmd(self, sock=None, cmd='$help', device='', readUntilCursor=True, betweenCommandDelay=0.0):
		if sock==None:
			sock = self.sock
		res =  self.sendAndReceiveText(sock, cmd, device, readUntilCursor)
		time.sleep(betweenCommandDelay)
		#If ends with cursor get rid of it
		if res[-1:] == '>':
			res = res[:-3] #remove last three chars - hopefully '\r\n>'
		return cmd + ' : ' + res
	
	    	
	# Send text to the back end then read it's response
	# The objects connection needs to be opened (connect()) before this is used
	# If read until cursor is set to True (which is default) then keep reading response until a cursor is returned as the last character of result string
	def sendAndReceiveText(self, sock, sendText='$help', device='', readUntilCursor=True):
		try:						
			#print 'sending text:"' + sendText + '"'
			self.sendText(sock, sendText, device)
			time.sleep(0.1)
			res = self.rxBytes(sock)
			#print 'res="' + res + '"'
			#Somtimes we just get one cursor back of currently unknown origins
			#If that happens discard it and read again
			if res == '>':
				#print " CURSOR ONLY"
				res = self.rxBytes(sock)
			#If create socked fail (between backend and tcp/ip module)
			if 'Create Socket Fail' in res:
				print res
			if 'Connection Timeout' in res:				
				print res
			#If reading until  a cursor comes back then keep reading until a cursor appears or max tries exceeded
			if readUntilCursor:
				maxReads = 1000
				count = 0
				#check for cursor at end of read and if not there read again
				while res[-1:] != '>':
					newRes = self.rxBytes(sock)
					res = res + newRes
					count = count + 1
					if count >= maxReads:
						myStr = ' Count = Error: max reads exceeded before cursor returned\r\n'
						print myStr
						return myStr						
			return res
		except:
			raise

	def rxBytes(self,sock):
		#sock.setblocking(0) #make socket non-blocking		
		maxExceptions=10	
		exceptions=0
		maxReadRepeats=50
		readRepeats=0
		timeout_in_seconds = 10
		#Keep trying to read bytes until we get some, unless number of read repeads or exceptions is exceeded
		while True:	
			try:
				#select.select returns a list of waitable objects which are ready. On windows it has to be sockets.
				#The first arguement is a list of objects to wait for reading, second writing, third 'exceptional condition'
				#We only use the read list and our socket to check if it is readable. if no timeout is specified then it blocks until it becomes readable.
				ready = select.select([sock], [], [], timeout_in_seconds)
				if ready[0]:
					ret = sock.recv(self.maxRxBytes)
					return ret
				else:
					print 'rxBytes - readRepeats + 1'
					readRepeats=readRepeats+1
					time.sleep(0.5)
			except:
				print 'rxBytes - exceptions + 1'
				#raise
				exceptions=exceptions+1
				time.sleep(0.5)			
			#If read repeats has been exceeded we failed to get any data on this read.
			#   !!! This is likely to break whatever called us !!!
			if readRepeats >= maxReadRepeats:
				print 'Max read repeats exceeded - returning.'
				return 'No data received from QIS'
			#If number of exceptions exceeded then give up by exiting
			if exceptions >= maxExceptions:
				print 'Max exceptions exceeded - exiting' #exceptions are probably 10035 non-blocking socket could not complete immediatley
				exit()			
	# Send text to the back end don't read it's response
	# The sockets connection needs to be opened (connect()) before this is used			
	def sendText(self, sock, message='$help', device=''):
		if device != '':
			specialTimeout =  '%500000'
			message = device + specialTimeout +  ' ' + message			
			#print 'Sending: "' + message + '" ' + self.host + ':' + str(self.port)
		try:
			sock.sendall(message + '\r\n')
			return 'Sent:' + message
		except:
			raise
			
            
	# Query the backend for a list of connected modules. A $scan command is sent to refresh the list of devices,
	# Then a wait occurs while the backend discovers devices (network ones can take a while) and then a list of device name strings is returned
	# The objects connection needs to be opened (connect()) before this is used				
	def getDeviceList(self, sock=None):
		if sock == None:
			sock = self.sock		
		scanWait = 2
		#print 'Scanning for devices and waiting ' + str(scanWait) + ' seconds.'
		devString = self.sendAndReceiveText(sock, '$scan')
		time.sleep(scanWait)
		devString = self.sendAndReceiveText(sock, '$list')
		#print '"' + devString + '"'
		devString = re.sub(r'>', '', devString) #remove cursor
		devString = re.sub(r'\d+\) ', '', devString) #remove number) space
		#print '"' + devString + '"'
		devString = devString.split('\r\n')
		devString = filter(None, devString) #remove empty elements
		return devString
		
	# Query stream status for a device attached to backend
	# The objects connection needs to be opened (connect()) before this is used				
	def streamRunningStatus(self, device, sock=None):
		try:
			if sock == None:
				sock = self.sock		
			index = 0 # index of relevant line in split string
			streamStatus = self.sendAndReceiveText(sock, 'stream?', device)
			streamStatus = streamStatus.split('\r\n')
			streamStatus[index] = re.sub(r':', '', streamStatus[index]) #remove :
			return streamStatus[index]
		except:
			raise
			
	# Query stream buffer status for a device attached to backend
	# The objects connection needs to be opened (connect()) before this is used		
	def streamBufferStatus(self, device, sock=None):
		try:
			if sock == None:
				sock = self.sock
			index = 1 # index of relevant line in split string
			streamStatus = self.sendAndReceiveText(sock, 'stream?', device)
			streamStatus = streamStatus.split('\r\n')
			streamStatus[index] = re.sub(r'^Stripes Buffered: ', '', streamStatus[index])
			return streamStatus[index]
		except:
			raise
			
	# Get the averaging used on the last/current stream
	# The objects connection needs to be opened (connect()) before this is used		
	def streamHeaderAverage(self, device, sock=None):
		try:
			if sock == None:
				sock = self.sock		
			index = 2 # index of relevant line in split string
			streamStatus = self.sendAndReceiveText(sock, sendText='stream text header', device=device)
			streamStatus = streamStatus.split('\r\n')
			if  'Header Not Available' in streamStatus[0]:
				str = streamStatus[0] + '. Check stream has been ran on device.'
				#print str
				return str			
			streamStatus[index] = re.sub(r'^Average: ', '', streamStatus[index])
			avg = streamStatus[index]
			avg = 2 ** int(avg)
			return '{}'.format(avg)
		except:
			print (device + ' Unable to get stream average.' + self.host + ':' + str(self.port))
			raise	
	# Get the version of the stream and convert to string for the specified device
	# The objects connection needs to be opened (connect()) before this is used		
	def streamHeaderVersion(self, device, sock=None):
		try:
			if sock == None:
				sock = self.sock						
			index = 0 # index of relevant line in split string
			streamStatus = self.sendAndReceiveText(sock,'stream text header', device)
			streamStatus = streamStatus.split('\r\n')
			if  'Header Not Available' in streamStatus[0]:
				str = streamStatus[0] + '. Check stream has been ran on device.'
				print str
				return str				
			version = re.sub(r'^Version: ', '', streamStatus[index])
			if version == '3':
				version = 'Original PPM'
			elif version == '4':
				version = 'XLC PPM'
			elif version == '5':
				version = 'HD PPM'
			else:
				version = 'Unknown stream version'
			return version			
		except:
			print(device + ' Unable to get stream version.' + self.host + ':' + str(self.port))
			raise
	# Get a header string giving which measurements are returned in the string for the specified device
	# The objects connection needs to be opened (connect()) before this is used					
	def streamHeaderFormat(self, device, sock=None):
		try:
			if sock == None:
				sock = self.sock			
			index = 1 # index of relevant line in split string
			streamStatus = self.sendAndReceiveText(sock,'stream text header', device)
			streamStatus = streamStatus.split('\r\n')
			if  'Header Not Available' in streamStatus[0]:
				str = streamStatus[0] + '. Check stream has been ran on device.'
				print str
				return str									
			format = int(re.sub(r'^Format: ', '', streamStatus[index]))						
			b0 = 1				#12V_I
			b1 = 1 << 1     #12V_V
			b2 = 1 << 2		#5V_I
			b3 = 1 << 3     #5V_V			
			formatHeader = 'StripeNum, Trig, '			
			if format & b3:
				formatHeader = formatHeader +  '5V_V,'
			if format & b2:
				formatHeader = formatHeader +  ' 5V_I,'
			if format & b1:
				formatHeader = formatHeader +  ' 12V_V,'
			if format & b0:
				formatHeader = formatHeader +   ' 12V_I'									
			return formatHeader			
		except:			
			print (device + ' Unable to get stream  format.' + self.host + ':' + '{}'.format(self.port))
			raise
			
	# Get stripes out of the backends stream buffer for the specified device using text commands
	# The objects connection needs to be opened (connect()) before this is used		
	def streamGetStripesText(self, sock, device, numStripes="all"):
		try:
			stripes = self.sendAndReceiveText(sock, 'stream text ' + str(numStripes), device, readUntilCursor=True)
			if stripes[-1:] != '>':
				return "Error no cursor returned."
			else:
				stripes = stripes[:-3] #remove last three chars - hopefully '\r\n>'			
			stripes = re.sub(r'eof', '', stripes)
			stripes = stripes.split('\r\n')
			stripes = filter(None, stripes) #remove empty sting elements
			#print stripes			
			return stripes
		except:
			raise		
			
	def avgStringFromPwr(self, avgPwrTwo):
		if(avgPwrTwo==0):
			return '0'
		elif(avgPwrTwo==1):
			return '2'
		elif(avgPwrTwo > 1 and avgPwrTwo < 10 ):
			avg = 2 ** int(avgPwrTwo)
			return '{}'.format(avg)
		elif(avgPwrTwo==10):
			return '1k'
		elif(avgPwrTwo==11):
			return '2k'
		elif(avgPwrTwo==12):
			return '4k'
		elif(avgPwrTwo==13):
			return '8k'		
		elif(avgPwrTwo==14):
			return '16k'
		elif(avgPwrTwo==15):
			return '32k'			
		else:
			return 'Invalid Average Value'			