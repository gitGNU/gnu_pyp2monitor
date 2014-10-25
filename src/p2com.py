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

##@package p2com Package handling serial port I/O with the furnace.
#
# This package define functions helping to read and write data to the Furnace.
#

import sys
import serial
import logging

import p2msg
from p2msg import P2Msg

import utils

##Use to log
#@see utils.getLogger()
logger = utils.getLogger()

##Class handling I/O exception
#
# This class is an exception class used to handle serial port I/O errors such as timeout.
# @ingroup lowlevel
class P2ComError(Exception):

	##Stores string representation for an error code.
	ERR_STR = {	10: "Incomplete or timeout header recv", 
			11: "Timeout on data size recv",
			12: "Incomplete or timeout data recv",
			13: "Incomplete message or checksum or timeout on checksum recv",
			2 : "Invalid checksum",
			9 : "Global timeout, no frame received"}
	
	##Error code for timeout
	ERR_TIMEOUT	= 9
	##Error code for header receive
	ERR_HEADER	= 10
	##Error code for invalid data size
	ERR_DATASZ	= 11
	##Error code for global data error
	ERR_DATA	= 12
	##Error code for invalid checksum on received frame
	ERR_CHKSUM_RECV	= 13
	##Error code for checksum error
	ERR_CHKSUM	= 2

	##Instanciate a P2ComError object
	#
	# @param errno The error code
	# @param data The data received on serial port	
	def __init__(self,errno, data = None):
		
		##The associated error code
		self.errno = errno
		##The associaed datas
		self.data = data
		
	##Cast a P2ComError into a string
	def __str__(self):
		return "Error "+str(self.errno)+" : "+P2ComError.ERR_STR[self.errno]
		
	##Return the associated error code
	def getErrno(self):
		return self.errno

	##Return the associated error string
	def getErrStr(self):
		return P2ComError.ERR_STR[self.errno]
	
	##Return the associated data
	def getData(self):
		return self.data

	

##The class managing the communication with the furnace on serial port
# @ingroup lowlevel
class P2Com:
	

	##Instanciate a new P2Com object and open the serial port with the good parameters
	#
	#@param portFile The file name of the serial port (/dev/ttyS0 by default)
	def __init__(self, portFile):
		##A small timeout
		#
		# This small tiemout is used as time between each read retry
		self.timeout = 0.01
		##Read fail timeout
		self.failTimeout = 10

		##The serial port object
		#self.ser = serial.Serial(portFile,9600,serial.EIGHTBITS,serial.PARITY_NONE,serial.STOPBITS_ONE,self.timeout,)
		self.ser = serial.Serial(portFile,9600,serial.EIGHTBITS,serial.PARITY_NONE,serial.STOPBITS_ONE,self.timeout,)

		##The last char of a sended frame "\r"
		self.FRAME_END=0x0D;
		##The last char sended by the furnace in a frame (obsolete and false)
		self.RECV_END=231;
	
	##Return the serial port object
	def getCom(self):
		return self.ser
	
	##Obsolete function (the checksum is not processed here now)
	#
	# Process a checksum given a message
	def checksum(msg):
		"""@todo
		Remove P2Com.checksum()
		"""
		#Store the sum
		buff = 0
		#Work var
		tmp = msg

		while len(tmp) > 0:
			#Add to buff a new byte (the two last char of the string) 
			buff += int(tmp[-2:],16)
			#Remove the byte from tmp
			tmp=tmp[:-3]
	
		#Return buff converted as a 4 digits hex number 
		return "%04X" % buff

	##Write raw datas on to the furnace after adding checksum to it (obsolete)
	#
	#	Take as argument a string representing hexadecimal numbers
	#	and send the associated bytes array to the serial port.
	#
	#	Exemple : a call to write("10050F") sends [16,5,15] to the serial port
	#
	# @param msg a string representing an hexadecimal number
	# @return None
	def write(self,msg):
		msg_bck = msg
		checksum = 0
		res = []
		tmp = ""
		while len(msg) > 0:
			#Store the two first hexadecimal digits
			tmp = int(msg[0:2],16)
			#and remove them from the string
			msg = msg[2:]

			#The checksum is a simple addition
			checksum += tmp

			res.append(tmp)

		#Adding the two bytes of the checksum to the data
		res.append(checksum/0x100)
		res.append(checksum%0x100)
		#Adding the end of frame character
		res.append(self.FRAME_END)

		#Send datas on the serial port
		self.ser.write(str(bytearray(res)))

		logger.debug("Send '"+msg_bck+"%04X" % checksum+"'")
		
		pass
	
	##Write data to serial port
	#
	#@param msg a P2Msg object
	#@return None
	def sendMsg(self, msg):
		self.ser.write(msg.getRaw()+"\r")

		logger.debug("Send '"+msg.getStr()+"'")
		pass

	##Read datas on the serial port
	#
	#	Reads datas from the serial port and returns a P2Msg
	#
	#@exception P2ComError On receive error
	#@return P2Msg object
	def read(self):
		recvBuff = ""
		res = P2Msg()
		retry = 0
		
		logger.debug("Waiting for data on serial port")

		while retry * self.timeout <= self.failTimeout:
			recvBuff = self.ser.read(1024)
			if len(recvBuff) > 0:
				#Frame receive
				if len(recvBuff) >= 1 and not res.setHeader(recvBuff[0:2]):
					raise P2ComError(10,res)
				if len(recvBuff) >= 3 and not res.setDataSz(recvBuff[2:3]):
					raise P2ComError(11,res)
				if len(recvBuff) >= 5 and not res.setData(recvBuff[3:-2]):
					raise P2ComError(12,res)
				if not res.setChecksum(recvBuff[-2:]):
					raise P2ComError(13,res)
				logger.debug("Frame received "+res.getStr())
				return res

			retry += 1
		raise P2ComError(9)
	
	##Close the serial port
	#
	#@return None
	def close(self):
		self.ser.close();

