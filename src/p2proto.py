# -*- coding: utf-8 -*-#

# Copyright 2013, 2014 Weber Yann, Weber Laurent
#
# This file is part of pyP2Monitor.
#
#        pyP2Monitor is free software: you can redistribute it and/or modify
#        it under the terms of the GNU General Public License as published by
#        the Free Software Foundation, either version 3 of the License, or
#        (at your option) any later version.
#
#        pyP2Monitor is distributed in the hope that it will be useful,
#        but WITHOUT ANY WARRANTY; without even the implied warranty of
#        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#        GNU General Public License for more details.
#
#        You should have received a copy of the GNU General Public License
#        along with pyP2Monitor.  If not, see <http://www.gnu.org/licenses/>.
#

##@package p2proto
# Handle the P2 communication protocol

import time
import datetime
import sys
import logging

import p2com
from p2com import *

import p2dbstore
from p2dbstore import *

##Use to log
#@see utils.getLogger()
logger = utils.getLogger()


##Class implementing and handling the communication protocol with the furnace
#@ingroup comproto
class P2Furn:
	
	##@defgroup P2ProtoStages Communication stages
	#@ingroup comproto
	
	##Before initialisation stage
	#@ingroup P2ProtoStages
	STAGE_PREINIT	= 0
	##Authentication stage
	#@ingroup P2ProtoStages
	STAGE_LOGIN 	= 1
	##Initialisation exchange stage
	#@ingroup P2ProtoStages
	STAGE_INIT	= 2
	##After initialisation stage
	#@ingroup P2ProtoStages
	STAGE_POST_INIT	= 3
	##Data exchange stage
	#@ingroup P2ProtoStages
	STAGE_XCHG	= 4

	##@defgroup P2ProtoUsers Furnace user's value
	#@ingroup comproto

	##Plumber user
	#@ingroup P2ProtoUsers
	USER_PLUMBER	= "52610300007B"
	##Normal user
	#@ingroup P2ProtoUsers
	USER_NORMAL	= "526103000001"
	##Alternate normal user
	#@ingroup P2ProtoUsers
	USER_NORMAL_ALT	= "5261030000F3"
	##Service user
	#@ingroup P2ProtoUsers
	USER_SERVICE	= "52610300FFF9"


	##Instanciate a new P2Furn
	#
	# @param serial_port The serial port filename (eg : /dev/ttyS0 )
	def __init__(self, serial_port):
		
		##The serial port filename
		self.port = serial_port
		##The Associated P2Com object
		self.com = P2Com(serial_port)
		##Stores the current stage
		#@see P2ProtoStages
		self.curStage = P2Furn.STAGE_PREINIT

		pass
	
	##Return user hex value used to auth, given a user name
	#
	#@param user the user name
	#
	#@return An hex string representing the user id
	@staticmethod
	def userId(user):
		res = P2Furn.USER_NORMAL

		if user == 'service':
			res = P2Furn.USER_SERVICE
		elif user == 'normal_alt':
			res = P2Furn.USER_NORMAL_ALT
		elif user == 'plumber':
			res = P2Furn.USER_PLUMBER

		return res
	
	##Restart the serial port
	def restartSerialPort(self):
		self.com.close()
		self.com = P2Com(0)
		pass
	
	##Read a message from the furnace
	#
	# Simply call P2Com::read()
	#
	#@return A P2Msg object
	#
	#@see P2Com::read()
	def readMsg(self):
		return self.com.read()

	##Send a message to the furnace
	#
	# Simply call P2Com::sendMsg()
	#
	#@param msg A P2Msg object
	#@see P2Com::sendMsg()
	def sendMsg(self, msg):
		self.com.sendMsg(msg)

	##Begin the authentication stage
	#
	# @param user Is the hexadecimal representation of the message to send to authenticate
	# @param maxRetry The maximum number of retry before exit and consider as failed
	# @param retryWait The number of seconds between two authentication try
	#
	# @see P2ProtoUsers
	#
	# @exception Exception On invalid type for parameters
	def runAuth(self, user = USER_SERVICE, maxRetry = 3, retryWait = 10):
		
		logger.info("Entering authentication stage")
		logger.debug("Trying to auth with '"+user+"'")
		
		retry = True
		retryCnt = 0

		self.curStage = P2Furn.STAGE_LOGIN
		"""	
			Sending user Id
		"""
		retry = True
		while retry:
			logger.debug("Sending user Id, waiting for reply.")
			self.com.write(user)
		
			try:
				msg = self.com.read()
				#msg.dumpData()
				retry = False
				logger.debug("Answer received : "+msg.getStr())
			except P2ComError as e:
				if retryCnt < maxRetry:
					logger.warn("Error while waiting authentication aknowledge. Retry in "+str(retryWait)+"s")
					logger.debug("Error is : "+e.getErrStr())
					for i in range(retryWait):
						time.sleep(1)
					self.restartSerialPort()
					retryCnt += 1
				else:
					logger.critical("Authentication failed after "+str(retry)+" tries")
					raise Exception("Authentication to the P2 furnace failed too many times")
			pass
	
	##Run the initialisation stage
	#
	# @exception P2ComError On protocol error
	def runInit(self):

		logger.info("Entering initialisation stage")

		"""
			Waiting for the initialisation to end
		"""
		inMsg = None
		outMsg = P2Msg()
		#First headers value
		firstHeader = [0x4D,0x41]
		outData = [0x01]
		outMsg.prepare(firstHeader, outData)

		self.curStage = P2Furn.STAGE_INIT
		
		counter = 1
		"""
			Sending message with same header as reply while reply's header doesn't
			begin with "4D3"
		"""
		while self.curStage == P2Furn.STAGE_INIT:
			logger.info("Init message exchange #"+str(counter))
			self.com.sendMsg(outMsg)
			
			try:
				inMsg = self.com.read()
				#inMsg.dumpData()
				#print "MSGDUMP: "+inMsg.dispInitMsg()
			except P2ComError as e:
				print e
				if e.getErrno() == 9:
					raise e
					
				if e.getData() == None:
					logger.error("Message failure : no message")
				else:
					logger.error("Message failure : "+e.getData().getStr())

				##########################
				#
				# WARNING HERE WE SET OUR
				# REPLY HEADER FROM AN 
				# INVALID/INCOMPLETE
				# MESSAGE
				#
				###########################
				recvHeader = e.getData().getHeader(P2Msg.FMT_LIST)
				
				logger.debug("Received headers : "+str(recvHeader))
			else :
				#ici on pourrait peut etre check que le premier octet de header est bien 0x4D
				recvHeader = inMsg.getHeader(P2Msg.FMT_LIST)
			
			counter += 1
			#Exit if header begin with "4d3"
			if recvHeader[0] == 0x4D and (recvHeader[1] & 0xF0) == 0x30:
				self.curStage = P2Furn.STAGE_POST_INIT
			else:
				outMsg.prepare(recvHeader)

		logger.info("Initialisation successfully terminated with "+str(counter)+" exchange between computer and furnace")

		"""
			First initialisaion stage end
		"""
		#Read 32 times M2 values
		outMsg.prepare([0x4D,0x32],[0x01])
		nbMaxTs = 33
		ser = self.com.getCom()
		for i in range(nbMaxTs):
			self.com.sendMsg(outMsg)
			time.sleep(0.15) #Important sleep !
			if ser.inWaiting() > 0:
				inMsg = self.com.read()
				logger.info("2nd init message received")
				logger.debug("Message : "+inMsg.getStr())
			else:
				logger.debug("No message...")
				
			logger.debug(str(nbMaxTs-i)+" message left before 2nd init end.")

		#Send rb request
		logger.info("Sending rb request")
		outMsg.prepare([0x52,0x62],[0x00,0x00,0x01])
		try:
			self.com.sendMsg(outMsg)
			#Read ack
			inMsg = self.com.read() #usually "0x52 0x62 0x01 0x01 0x00 0xb6"
			logger.info("Rb acknowledge received")
		except P2ComError as e:
			logger.error("Timeout waiting rb aknowledge")
		

		logger.info("Second Init stage success.")
		
		#send M2 request
		logger.info("Waiting 3s before sending the first M2 request")
		time.sleep(3)
		logger.debug("Sending the first M2 request")
		outMsg.prepare([0x4D,0x32],[0x01])

		retryMax = 20
		i=0
		while i<retryMax:
			try:
				self.com.sendMsg(outMsg)
				#Read ack
				inMsg = self.com.read()
				logger.debug("M2 Acknowledge received")
				break
			except P2ComError as e:
				i+=1
				logger.warning(str(i)+" timeout waiting acknowledge for 3th init stage M2 message, retrying...")
				
		if i == retryMax:
			logger.error("Abording... Too much timeout received for 3th init stage M2 message.")

		#Change state
		self.curStage = P2Furn.STAGE_XCHG

		logger.info("Initialisation successfully terminated...")
		pass

	##Run the data retrieve function
	#
	# @param storage is a dict storing each data storage. Possible keys values are "sqlite" for sqlite db (value is the db file) or "file" for ascii dump (value is the dump file)
	# @param dateFromP2 is True when we want the furnace date and time, if false we take the date and time from the computer
	#
	# @exception TypeError On invalid type for parameter storage
	def readData(self, waitdata = 0.5, storage=[("sqlite", "p2.db")], dateFromP2 = False):
		
		logger.info("Entering data exchange mode")
		
		#Local variable initialisation
		inMsg = P2Msg()
		outMsg = P2Msg()

		headers = {"m1" : [0x4D,0x31], "m2" : [0x4D,0x32], "m3" : [0x4D,0x33]}

		#m1sending = True
		m1sending = False

		#Storage initialisation
		storObj = []
		for (method,name) in storage:
			if method == "sqlite":
				storObj.append(("sqlite", P2DbStore(name)))
			elif method == "file":
				storObj.append(("file", open(name, 'a')))
			elif method == "csv":
				storObj.append(('csv',csv.writer(open(name, 'wb'), delimiter=',')))
			else:
				raise TypeError('Waiting for a tuple of the form (["file" | "sqlite" | "csv", filename), but got ('+str(method)+','+str(name)+')')

		outMsg.prepare(headers["m2"], [0x01])
		#Fake m2 receive
		inMsg.prepare([0x4D,0x32],[0x01])
		
		curDate = None

		#infinite loop...
		while True:
			#Test wich header we have
			inHead = inMsg.getHeader(P2Msg.FMT_HEX_STR)
			if inHead == "4D33":
				#We received a M3
				outMsg.prepare(headers["m3"])
				logger.info("M3 message received")
			else:
				if m1sending:
					logger.debug("Sending a M1 message")
					outMsg.prepare(headers["m1"])
					m1sending = False
				else:
					logger.debug("Sending a M2 message")
					outMsg.prepare(headers["m2"])
					m1sending = True
			#Send the prepared message
			#time.sleep(0.5)
			self.com.sendMsg(outMsg)

			#And read the reply
			inMsg = self.com.read()
			
			"""
			Incoming frame process
			"""
			if inMsg.getHeader(P2Msg.FMT_HEX_STR) == "4D31" and (curDate != None or not dateFromP2):
				
				logger.debug("M1 received")
				#If we dont want the date from the P2 we take the computer's date and time
				if not dateFromP2:
					curDate = datetime.datetime.now()
				
				#Store data on each selected storage
				for (family, obj) in storObj:
					if family == "sqlite":
						#Only store frame with valid checksum
						if inMsg.check():
							obj.insert(curDate.strftime("%s"), inMsg.getData(P2Msg.FMT_HEX_STR))
					elif family == "csv":
						if inMsg.check():
							obj.writerow([curDate.strftime("%s")]+inMsg.getData(P2Msg.FMT_LIST))
					elif family == "file":
						if inMsg.check():
							obj.write(str(curDate.strftime("%s"))+" ::"+inMsg.getData(P2Msg.FMT_HEX_STR))
						else:
							obj.write(str(curDate.strftime("%s"))+" :invalid:"+inMsg.getData(P2Msg.FMT_HEX_STR))
				
				curTimestamp = None
			elif dateFromP2:
				logger.debug("M2 received")
				#If we want date and time from the furnace take it...
				if inMsg.getHeader(P2Msg.FMT_HEX_STR) == "4D32":
					#we got a date
					msgData = inMsg.getData(P2Msg.FMT_LIST)
					#msgData[2] is day of week. !!! Warning : Y3K problem ;o) !!!
					curDate = datetime.datetime(msgData[0]+2000,msgData[2],msgData[3],msgData[4],msgData[5],msgData[6])

			logger.debug("Received message : "+inMsg.getStr())
			time.sleep(waitdata)
		pass
		
	##Close the serial port and reset stage lag
	def stop(self):
		self.curStage = P2Furn.STAGE_PREINIT
		self.com.close()
		pass

