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


##@package p2data Store functions and object handling P2's data processing
#
# Stores functions used to format raw data from the furnace


import time
import datetime
import json
import logging
import tempfile


import os, string, tempfile, types, sys

import p2msg
import p2dbstore
import p2data
import utils

##Use to log
#@see utils.getLogger()
logger = utils.getLogger()

##Class used to store a range of data in tuples like (time, value)
#
# This class is used by pyP2DataReader to store query result.
# @ingroup msgprocess
class P2Query:
	
	##Instanciate a new P2Query object
	#
	# @param dateFormat The format used to convert beg and end
	# @param colNum The data's column number handled by this object
	# @param beg A timestamp representing the lower handled date and time
	# @param end A timestamp representing the biggest handled date and time
	# @param time Used if one of param beg or end is set to None. Represent length of the time range.
	def __init__(self,dateFormat, colNum, beg=None, end=None, time=None):
		
		##The higher date and time of the date range. Stored as a timestamp.
		self.beg = None
		##The smaller date and time of the date range. Stored as a timestamp.
		self.end = None
		##A dict storing query's data. Keys are timestamp, and value are data
		self.datas=dict()
		##Store the column number
		self.colNum=int(colNum)
		
		
		#store the first timestamp
		if beg != None:
			if beg == 'first':
				self.beg = 0
			else:
				if dateFormat == 'diff':
					secs=P2Query.fromInterval(beg)
					self.beg = datetime.datetime.now()
					self.beg = int(self.beg.strftime("%s")) + secs
				else:
					self.beg=datetime.strptime(beg,dateFormat)
					self.beg = int(self.beg.strftime("%s"))
			
		#store the last timestamp
		if end != None:
			if end == 'now':
				self.end=datetime.datetime.now()
				self.end = int(self.end.strftime("%s"))
			else:
				if dateFormat == 'diff':
					secs=P2Query.fromInterval(end)
					self.end = datetime.datetime.now()
					self.end = int(self.end.strftime("%s")) + secs
				else:
					self.end=datetime.strptime(end,dateFormat)
					self.end = int(self.end.strftime("%s"))
		
		#Calculate from time interval if needed
		if time != None:
			secs=P2Query.fromInterval(time)
			
			if beg == None and not end == None:
				self.beg = self.end + secs
				
			elif end == None and not beg == None:
				self.end = self.beg + secs
		
		#Check that date are correct
		if self.end<self.beg:
			logger.critical('End date is smaller than begin date')
			exit(1)	
		
		pass
	
	##Return a number of seconds from an interval
	#
	# Return a number of seconds from a interval composed by a signed integer and a suffix.
	# Allowed suffixes are 's' for seconds, 'm' for minutes, 'h' for hours and  'd' for days
	#
	#@param interval A string representing a time interval
	#@return The number of seconds represented by this interval
	@staticmethod
	def fromInterval(interval):
		
		secs = 0
		unit = interval[len(interval)-1]
		secs=int(interval[:-1])
		
		if unit == 's':
			secs = secs
		elif unit == 'm':
			secs *= 60
		elif unit == 'h':
			secs *= 3600
		elif unit == 'd':
			secs *= 3600 * 24
		else:
			logger.critical('Invalid time interval : '+time)
			exit(1)
		
		return secs
	
	##Set the data's content of the query object
	#	Set the content with an array of the form [[timestamp0,val0],[timestamp1,val1], ... ]
	#	with val the array of value associated with a data
	#
	#@param content An array storing arrays of the form [timestamp,val]
	#@return True
	def setContent(self, content):
		self.datas=dict()
		for (ts,vals) in content:
			self.datas[ts] = vals[self.colNum]
		return True
	
	
	##Return a value given a timestamp
	#
	#@param timestamp The wanted timestamp
	#@return An integer value or False if there is no data's associated with this timestamp
	def getVal(self,timestamp):
		if timestamp not in self.datas:
			return False
		else:
			return self.datas[timestamp]
	
	
	##Return the first timestamp ( P2Query::beg )
	def getBeg(self):
		return self.beg
	
	##Return the last timestamp ( P2Query::end )
	def getEnd(self):
		return self.end
	


##Used to get datas from queries
#
# This object handle multiple query's and make request to the Sqlite database.
# @ingroup msgprocess
class P2Datas:
	
	##Alias for one letter query parameter to string parameter
	argsShort = {'b' : 'begin', 'e' : 'end', 't' : 'time', 'f' : 'format', 'd':'data', 'n':'num', 'a':'axes', 's':'style', 'c':'color', 'l':'label', 'sc':'scale', 'a':'add' }
	##List of argument that have to be set to None after the P2Query creation
	argsToNone = ['begin','end','time']
	
	##Instanciate a new P2Datas object
	#
	#@param dbFile is the sqlite db file
	#@param queries is a query string array
	#@param queryArgSep is the separator between two query's argument
	def __init__(self, dbFile, queries, queryArgSep):
		
		##The Sqlite database object
		self.db = p2dbstore.P2DbStore(dbFile)
		##The query list
		self.queries = []
		##The larger range between a begin and a end in seconds
		self.maxDiff=0
		##Set to True if every handled query have the same date range
		self.sameRange=True
		##Store query's arguments
		self.qArgs = []
		##Store the GnuPlot's data temporary file name
		self.tmpfile = None
		first = True
		
		for query in queries:
			args = P2Datas.queryToDict(query, queryArgSep)
			self.qArgs.append(args)
			if 'format' not in args:
				print >> sys.stderr, 'Error, no date format specified in query '+query
				exit(1)
			elif 'num' not in args:
				print >> sys.stderr, 'Error no data id number specified in query '+query
			self.queries.append(P2Query(args['format'], args['num'],args['begin'],args['end'],args['time']))
			curq = self.queries[-1:][0]
			diff = curq.getEnd() - curq.getBeg()
			if diff > self.maxDiff:
				self.maxDiff = diff
			if first:
				first = False
				base = [curq.getBeg(),curq.getEnd()]
			else:
				if base[0] != curq.getBeg() or base[1] != curq.getEnd():
					self.sameRange = False
			
		pass
	
	##Return a dict of "option"=>"value" from a query string
	#
	#@param query The query string
	#@param sep The query's argument separator
	#@return A dict representing each argument as 'option'=>'value'
	@staticmethod
	def queryToDict(query, sep):
		spl = query.split(sep)
		res = dict()
		for s in spl:
			spl2 = s.split('=',1)
			name = spl2[0]
			if name in P2Datas.argsShort:
				name = P2Datas.argsShort[name]
			res[name] = spl2[1]
		
		for n in P2Datas.argsToNone:
			if n not in res:
				res[n] = None
		return res
	
	
	##Fill a query with datas
	#
	#@param datas An array of data
	#@param queries An array of query to fill
	@staticmethod
	def fillQuery(datas,queries):
		#format content
		content = []
		for data in datas:
			dataList = p2msg.P2Msg.hex2list(data[1])
			if len(dataList) != 48:
				logger.warning('Data as not the waited length ('+str(len(dataList))+' \''+data[1]+'\'')
			else:
				dataList = data2List(data[0], dataList )
				#print data[0]
				content.append([data[0],dataList])
			
		#fill queries
		for query in queries:
			query.setContent(content)
	
	##Trigger the queries filling with data from the database
	#
	# When called this function tells to the P2Datas object to get datas from the database and to fill its handled P2Query object.
	def populate(self):
		
		if self.sameRange:
			#Get th data
			datas = self.db.getData(self.queries[0].getBeg(),self.queries[0].getEnd())
			P2Datas.fillQuery(datas,self.queries)
		else:
			filled = []
			"""The goal is to look for queries with same begin and end
			to make only one db query per group"""
			for i in range(len(self.queries)):
				if i not in filled:
					tofill=[i]
					#Look for same range
					for j in range(i,len(self.queries)):
						if self.queries[j].getBeg() == self.queries[i].getBeg() and self.queries[j].getEnd() == self.queries[i].getEnd():
							tofill.append(i)
					#Fill the group
					filled += tofill
					datas = self.db.getData(self.queries[i].getBeg(),self.queries[i].getEnd())
					tmp = tofill
					tofill = []
					for t in tmp:
						tofill.append(self.queries[t])
					P2Datas.fillQuery(datas, tofill)
		pass
			
			
	##Write GnuPlot's datas temporary file
	#
	# Use handled query to create and populate GnuPlot's temporary files.
	def getPlotData(self):

		if self.tmpfile != None:
			for t in self.tmpfile:
				t.close()
			self.tmpfile = None
		
		self.tmpfile = []
		for i in range(len(self.queries)):
			self.tmpfile.append(tempfile.NamedTemporaryFile('w+b',-1,'pyP2gnuplotdatas'))
		
		#Creating a dataSet foreach query
		
				
		#Formating datas from P2Query
		datasRes = []
		for t in range(0,self.maxDiff):
			
			#If there is data, put the first column : time
			if self.sameRange:
				#In this case everyone has the same begin
				beg = self.queries[0].getBeg()
				time = str(t+beg)
			else:
				time = str(t)
			
			#Then put data
			for i in range(len(self.queries)):
				
				query = self.queries[i] #the query
				args = self.qArgs[i] #The query args
				beg = query.getBeg()
				
				#Retrieving scale and correction
				if 'add' in args:
					add = args['add']
				else:
					add=0
				if 'scale' in args:
					scale = args['scale']
				else:
					scale = 1
				val = query.getVal(t+beg)
				
				
				if val is not False:
					self.tmpfile[i].write(time+' '+str(float(val)*float(scale)+float(add))+'\n')
					self.tmpfile[i].flush()	
		pass
	
	##Return the GnuPlot's plot command with the good arguments
	#
	#@return A string representing a GnuPlot's plot command
	def getPlotCommand(self):
		
		first = True
		res = ''
		
		for i in range(len(self.queries)):
			query = self.queries[i] #the query
			args = self.qArgs[i] #The query args
			if first:
				first = False
				res += 'plot '
			else:
				res += ' , '
			
			if self.tmpfile == None:
				self.getPlotData()
				
			res += '"'+self.tmpfile[i].name+'" using 1:2 '
			#res += '"'+self.tmpfile[i].name+'" using 1:'+str(i+2)+' '
			
			
			if 'label' in args:
				label = args['label']+' '
			else:
				label = colNames()[int(args['num'])]+' '
				
			#Retrieving scale and correction
			if 'add' in args:
				add = args['add']
			else:
				add=0
			if 'scale' in args:
				scale = args['scale']
			else:
				scale = 1	
			
			#Adding scale and correction to label
			if scale != 1.0:
				label += '*'+str(scale)
			if add != 0:
				if add > 0:
					label += '+'
				label += str(add)
				
			if 'style' in args:
				style = args['style']
			else:
				style = 'points'
			
			res += 'title "'+label+'" '
			res += ' with '+style+' '
			if 'color' in args:
				res += 'lt rgb "'+args['color']+'" '
			
		res += '\n'
		logger.debug('Plot command : '+res)
		return res
		
	##Return the time format to use giving the queries
	#
	# Find a good dateTimeFormat for GnuPlot's date display giving the date range of each query
	def getDateTimeFormats(self):
		if not self.sameRange:
			return False
		inFmt = '%s'
		outFmt = '%S'
		
		if self.maxDiff > 60 * 5:
			outFmt = '%H:%M:%s'
			#outFmt = '%S'
		if self.maxDiff > 3600 * 24:
			outFmt = '%d-%m %H:%M'
		
		
		return (inFmt,outFmt)
	
	##P2Datas destructor
	def __del__(self):
		for t in self.tmpfile:
			t.close()
		

##Take data and return a well formated integer array
#
# Take a string representing a huge hexadecimal number (the data field of a data frame from the furnace)
# and format it as an integer array applying number correction on some fields
#
#@param timestamp The timestamp to associate with this datas
#@param data The datas
#@param dateFormat The date's display format
#@return An integer array (except for the first item wich is a date as a string)
def data2List(timestamp, data, dateFormat="%Y/%m/%d_%H:%m:%S"):
	res = []
	date = datetime.datetime.fromtimestamp(timestamp)

	#Adding timestamp
	res.append(date.strftime(dateFormat))
	#Adding datas
	"""
	for d in data:
		res.append(d)
	"""
	for i in range(0,len(data),2):
		res.append(data[i]*0x100+data[i+1])
	#Applying number corrections on datas
	res[5] /= 2.0
	res[12] /= 10.0
	res[14] *= 0.0029
	res[15] /= 2.0
	res[16] /= 2.0
	res[24] /= 2.0
	#print 'lenres',len(res)
	
	return res


##Return an array with data column's name
#
# Return an array with P2 furnace data's column's name.
#
#@see data2List
def colNames():
	res = []
	
	res.append("Date et heure")
	res.append("Etat")
	res.append("b")
	res.append("c")
	res.append("d")
	res.append("Temp chaudiere")
	res.append("Temp fumee")
	res.append("Temp gaz brules")
	res.append("Puissance momentanee")
	res.append("Ventil. depart")
	res.append("Ventil. air combustion")
	res.append("Alimentation")
	res.append("O2 residuel")
	res.append("Regulation O2")
	res.append("Pellets restants (kg)")
	res.append("o")
	res.append("Temp exterieur")
	res.append("Temp consigne depart 1")
	res.append("Temp depart 1")
	res.append("s")
	res.append("t")
	res.append("Demarages")
	res.append("Duree fonctionnement (h)")
	res.append("Temp tableau")
	res.append("Consigne temp chaudiere")
	res.append("y")
	res.append("z")

	return res


##Return a json string from datas (OBSOLETE)
def datas2Json(datas):

	res = [colNames()]

	for data in datas:
		dataList = p2msg.P2Msg.hex2list(data[1])
		if len(dataList) == 48:
			res.append(data2List(data[0], dataList ))
	
	return json.dumps(res)

##Dump the database in csv format
#
# @param filename The filename to write csv in. If - output to stdout
# @param headers If true put a header with colnames
#
# @return a string representing the db dump in csv format

def csvDump(dbname, filename = '-', header = True, sep="; "):
	
	db = p2dbstore.P2DbStore(dbname)
	
	fd = None
	
	if filename == '-':
		fdout = sys.stdout
	else:
		fdout = open(filename, "w+")
		
	#put header
	if header:
		hnames =  colNames()
		for i in range(len(hnames)):
			fdout.write(hnames[i])
			if i < len(hnames)-1:
				fdout.write(sep)
		fdout.write("\n")
	
	datas = db.getData(0,0) #fetch all datas
	
	for (timestamp,data) in datas:
		dataList = p2msg.P2Msg.hex2list(data)
		
		if len(dataList) != 48:
			#bad len
			logger.warning("Bad data length "+str(len(dataList))+" : '"+(str(timestamp)+" "+data)+"'")
		else:
			dataNums = data2List(timestamp, dataList)
			for i in range(len(dataNums)):
				fdout.write(str(dataNums[i]))
				if i < len(dataNums)-1:
					fdout.write(sep)
			fdout.write("\n")
	
