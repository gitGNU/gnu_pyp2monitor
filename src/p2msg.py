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

##@package p2msg Used to handle P2 messages

import logging
import utils

##Use to log
#@see utils.getLogger()
logger = utils.getLogger()


##The class managing message from the furnace
# @ingroup msgprocess
class P2Msg:
	
	##@defgroup dataFormat Data format
	# @ingroup msgprocess
	
	##Huge integer format
	#@ingroup dataFormat 
	FMT_INT		= 1
	##Raw string format
	#@ingroup dataFormat
	FMT_RAW_STR	= 2
	##Hexadecimal representation string
	#@ingroup dataFormat
	FMT_HEX_STR	= 3
	##Integer list
	#@ingroup dataFormat
	FMT_LIST	= 4

	##Instanciate a new P2Msg object
	#
	# @param header The message header (aka command identifier)
	# @param datas The message data
	def __init__(self, header = None, datas = None):
		#At initialisation we only store raw int list

		##The message header or command identifier
		self.header = None
		##The message data
		self.datas = None
		
		if not header == None:
			self.setHeader(header)
		if not datas == None:
			self.setData(datas)
		
		##The data length in bytes
		self.dataSz = None
		##The message checksum
		self.checksum = None
		##A flag telling wether the message is in a valid state or not
		self.valid = True
		pass

	##Cast an ascii string into a list of bytes (type cast only)
	#
	#@param strArg An ascii string
	#@return An array of integers
	@staticmethod
	def str2list(strArg):
		res = []
		for i in range(len(strArg)):
			res.append(ord(strArg[i]))
		return res

	##Convert a string with 2 digits hexadecimal numbers into a list of integers
	#
	# Input string example : "07474E5504"
	#
	#@param strArg A string with 2 hexadecimal digits integer representation (without space)
	#@return An array of integers
	@staticmethod
	def hex2list(strArg):
		res = []
		while len(strArg) > 0:
			res.append( int(strArg[0:2],16) )
			strArg = strArg[2:]
		return res;

	##Set the P2msg header
	#
	#@param header The frame header (as string or integer array)
	#
	#@return P2Msg::valid
	#
	#@exception TypeError On invalid type for header param
	def setHeader(self, header):
		if type(header) is str:
			self.header = P2Msg.str2list(header)
		elif type(header) is list:
			self.header = header
		else:
			raise TypeError("Waiting str or list but got "+str(type(header)))
				
		if len(header) != 2:
			self.valid = False
			
		return self.valid

	##Set the data size
	# if sizeChk is True and data already set, check for validity
	#
	# @param recvBuff Is either a raw string from the furnace begining with the data size (header removed) or an integer representing the data size
	# @param sizeChk A boolean telling if we have to check or not the data size (in the case where recvBuff is a raw string from serial port)
	#
	# @return P2Msg::valid
	#
	# @exception TypeError On invalid type for parameters
	def setDataSz(self, recvBuff, sizeChk = True):
		if type(recvBuff) is str:
			self.dataSz = ord(recvBuff[0])
		elif type(recvBuff) is int:
			self.dataSz = recvBuff
		else:
			raise TypeError("Waiting str or int but got ",type(recvBuff))

		if sizeChk and self.datas != None and self.dataSz != len(self.datas):
			raise Exception("Data size doesn't match actuel size of data in the message")

		return self.valid


	##Set the P2Msg data field
	# If sizeChk is True and data size already set check for validity
	#
	# @param datas A raw string or an integer list representing datas
	# @param sizeChk A boolean telling whether we check datas argument size or not
	#
	# @return P2Msg::valid
	#
	# @exception TypeError On invalid type for parameters
	def setData(self,datas, sizeChk = True):
		"""   DEACTIVATE TEST !!! TO REACTIVATE LATER
		if sizeChk and self.dataSz != len(datas):
			self.valid = False
		"""
			
		if type(datas) is str:
			self.datas = P2Msg.str2list(datas)
		elif type(datas) is list:
			self.datas = datas
		else:
			raise TypeError("Waiting str or list but got ",type(datas))

		if not sizeChk or self.dataSz == None:
			self.dataSz = len(self.datas)

		return self.valid

	##Set the cheksum
	#	If no arguments process the checksum from header and datas
	#	if checksum argument set and check is True set the checksum value and
	#	check its validity
	#
	# @param checksum Set to None for checksum processing from P2Msg::header P2Msg::dataSz and P2Msg::datas, else can be a raw sring or an integer array
	# @param check Is a boolean telling if we check or not the validity of the checksum
	#
	# @return P2Msg::valid
	#
	# @exception TypeError On invalid type for parameters
	def setChecksum(self, checksum = None, check = True):
		if checksum != None:
			if len(checksum) != 2:
				self.valid = False
				self.checksum = 0
			elif type(checksum) is str or type(checksum) is list:
				self.checksum = ord(checksum[1]) + (ord(checksum[0]) * 0x100)
			elif type(checksum) is int:
				self.checksum = checksum
			else:
				raise TypeError("Waiting int, str or list but got : ",type(checksum))

			if check:
				ok = self.check()
				self.valid = ok
				if not ok:
					logger.warn("Warning invalid checksum for : "+self.getStr())
		else:
			self.checksum = self.calcChecksum()
			

		return self.valid

	##Prepare a message to be ready to send
	#
	# @param header Set to None to leave header unchanged
	# @param data Set to None to leave data unchanged
	#
	# @return None
	def prepare(self, header = None, data = None):
		if header != None: #Set header
			self.setHeader(header)
		
		if data != None: #Set data
			self.setData(data)
		
		#Data size update
		self.setDataSz(len(self.datas))
		#Checksum process and set
		self.setChecksum()
		
		if self.header != None and self.datas != None:
			self.valid = True

		pass

	##Reset the value of the P2Msg::valid flag
	#
	#@param val The wanted value for the flag
	def resetValid(self, val=True):
		if val:
			self.valid = True
		else:
			self.valid = False

	##Return the data size
	#
	# @param fmt The wanted data format
	#
	# @return Formated data size
	#
	# @see dataFormat
	#
	# @exception TypeError On invalid type for parameters
	def getDataSz(self,fmt = FMT_INT):
		if fmt == P2Msg.FMT_INT:
			if self.dataSz == None:
				return 0
			return self.dataSz
		elif fmt == P2Msg.FMT_RAW_STR:
			if self.dataSz == None:
				return ""
			return str(bytearray([self.dataSz]))
		elif fmt == P2Msg.FMT_HEX_STR:
			if self.dataSz == None:
				return ""
			return "%02X" % self.dataSz
		else:
			raise TypeError("Unknow or invalid format")

	##Return the checksum
	#
	# @param fmt The wanted data format
	#
	# @return Formated checksum
	#
	# @see dataFormat
	#
	# @exception TypeError On invalid type for parameters
	def getChecksum(self, fmt = FMT_INT):
		if fmt == P2Msg.FMT_INT:
			return self.checksum
		elif fmt == P2Msg.FMT_RAW_STR:
			return str(bytearray([self.checksum/0x100, self.checksum%0x100]))
		elif fmt == P2Msg.FMT_HEX_STR:
			return "%02X%02X" % (self.checksum / 0x100, self.checksum % 0x100)
		elif fmt == P2Msg.FMT_LIST:
			return [self.checksum/ 0x100, self.checksum % 0x100]
		else:
			raise TypeError("Unknow format")

	"""
		Return a list attribute in the requested format
	"""
	##Format an integer list
	#
	# @param lst The list to format
	# @param fmt The wanted data format
	#
	# @return Formated list
	#
	# @see dataFormat
	#
	# @exception TypeError On invalid type for parameters
	@staticmethod
	def formatList(lst, fmt):
		if fmt == P2Msg.FMT_LIST:
			return lst
		elif fmt == P2Msg.FMT_HEX_STR:
			if lst == None:
				return ""
			res = ""
			for i in lst:
				res += "%02X" % i
			return res
		elif fmt == P2Msg.FMT_RAW_STR:
			if lst == None:
				return ""
			return str(bytearray(lst))
		else:
			raise TypeError("Unknow or invalid format")
	
	##Return the header
	#
	# @param fmt The wanted data format
	#
	# @return Formated header
	#
	# @see dataFormat
	def getHeader(self, fmt = FMT_LIST):
		return P2Msg.formatList(self.header, fmt)

	##Return the data
	#
	# @param fmt The wanted data format
	#
	# @return Formated data
	#
	# @see dataFormat
	def getData(self, fmt = FMT_LIST):
		return P2Msg.formatList(self.datas, fmt)
		

	##Alias for P2Msg::getStr()
	def __print__(self):
		return self.getStr()
		
	##Return a string representing the message in hexadecimal notation
	#
	#@return A string with hexadecimal number notation on two hex digits
	def getStr(self):
		res = ""
		if self.header != None:
			for h in self.header:
				res += "%02X" % h
		if self.datas != None:
			res += "%02X" % len(self.datas)
			for data in self.datas:
				res += "%02X" % data
		if self.checksum != None:
			res += "%02X" % (self.checksum / 0x100)
			res += "%02X" % (self.checksum % 0x100)
		return res

	##Return the raw str representing the message
	#
	#@return An ascii string
	def getRaw(self):
		res = ""
		res += self.getHeader(P2Msg.FMT_RAW_STR)
		res += self.getDataSz(P2Msg.FMT_RAW_STR)
		res += self.getData(P2Msg.FMT_RAW_STR)
		res += self.getChecksum(P2Msg.FMT_RAW_STR)
		if self.failed():
			logger.warn("message marked as invalid while getting raw string")
		if not self.check():
			logger.warn("invalid message's chekcsum while getting raw string")
		return res

	##Display all the informations on the message
	def dump(self):
		print "Header :\t"+str(self.header)
		print "Data size =\t"+str(self.dataSz)
		print "Datas :\t"+str(self.datas)
		print "Checksum =\t"+"%02X%02X"%(self.checksum/0x100, self.checksum%0x100)
		print "Message marked as",
		if self.valid:
			print "valid"
		else:
			print "not valid"
		pass

	##Return a string trying to display every printable ASCII character
	#
	#	The returned string represente each data's bytes sperated with a space.
	#	Printable character are displayed as a single char when other value are displayed in 2 digits hexadecimal notation
	#
	# @param data The data to parse
	# @param chrRange The character range to display
	#
	# @return A string
	def dumpData(self,data,chrRange = [' ','~']):
		res = ""
		for c in data:
			if c >= ord(chrRange[0]) and c <= ord(chrRange[1]):
				res += chr(c)+" "
			else:
				res += "0x%02X " % c
		return res

	##A try to display initialisation message
	#
	# This functions try to display P2 furnace initialisation message in a more readable format
	def dispInitMsg(self):
		res = ""
		if self.header[0] < ord('A') or self.header[0] > ord('z') or self.header[1]<ord('A') or self.header[1]>ord('z'):
			res = "[0x%02X 0x%02X]" % (self.header[0],self.header[1])
		else:
			res = "[%c%c] " % (self.header[0],self.header[1])

		if self.header[0] == ord('M'):
			hid = self.header[1]
			if hid == ord('A') or hid == ord('B') or hid == ord('M'):
				for d in self.datas[:5]:
					res+="0x%02X "%d
				res += self.dumpData(self.datas[5:])
			elif hid ==  ord('D'):
				res += chr(self.datas[0])+" "
				for d in self.datas[1:7]:
					res+="0x%02X "%d
				res += self.dumpData(self.datas[7:])
			elif hid == ord('T'):
				res+="0x%02X "%self.datas[0]
				res+= self.dumpData(self.datas[1:])
			elif hid == ord('L'):
				for d in self.datas[:11]:
					res+="0x%02X "%d
				res += self.dumpData(self.datas[11:])
			elif hid == ord('F') or hid == ord('W'):
				for d in self.datas[:3]:
					res+="0x%02X "%d
				res += self.dumpData(self.datas[3:])
			else:
				for d in self.datas:
					res+="0x%02X "%d
		else:
			for d in self.datas:
				res+="0x%02X "%d
		return res

	##Return the not valid flag
	#
	# @return the negation of P2Msg::valid
	#
	def failed(self):
		return (not self.valid)

	##Return the checksum as an integer for this message
	#
	# Process and return the current message checksum
	#
	# @return An integer representing the message's checksum
	def calcChecksum(self):
		chk = self.dataSz
		for h in self.header:
			chk += h
		for data in self.datas:
			chk += data
		return chk;
	
	##Check the message checksum
	#
	# Process the checksum and check if it is the same than the stored checksum
	#
	# @return A boolean value
	def check(self):
		return (self.getChecksum() == self.checksum)

