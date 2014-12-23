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

##@package p2dbstore Define the P2DbStore object, used to store P2's datas in a database

import sqlite3
import logging
import utils

##Use to log
#@see utils.getLogger()
logger = utils.getLogger()

##Used to handle the Sqlite database connection
# @ingroup msgprocess
class P2DbStore:

	##Create the Database object
	#
	#@param filename The Sqlite file name
	def __init__(self, filename="p2.db"):
		
		##The database connection
		self.conn = sqlite3.connect(filename)
		##The database cursor
		self.c = self.conn.cursor()
		self.c.execute('create table if not exists p2data (date integer, data collate binary)')
		self.conn.commit()
		
		pass

	##Insert datas into database
	#
	#@param timestamp The data's timestamp
	#@param datas The data to store
	def insert(self, timestamp, datas):
		#Maybe add checks
		
		#val = (timestamp,pickle.dumps(datas))
		val = (timestamp,datas)

		self.c.execute('insert into p2data values (?,?)', val)
		self.conn.commit()
		
		logger.debug('Data inserted in db')
		logger.debug('Data stored in database')
		pass

	##Retrieve data from database
	#
	#@param dateMin is the smaller data's timestamp returned
	#@param dateMax is the higher data's timestamp returned (0 or less mean no limit)
	#
	#@return An array of selected datas
	def getData(self, dateMin=0, dateMax=0):
		val = () #Store SQL query parameters
		
		#SQL query construction
		req = 'select * from p2data'
		if dateMin > 0:
			req += ' where date >= ?'
			val += (dateMin,)
		if dateMax > 0:
			if len(val) == 0:
				req += ' where '
			else:
				req += ' and '
			req += ' date <= ?'
			val += (dateMax,)
		req += ' order by date'
		
		#SQL query execution
		logger.debug('Executing : \''+req+'\' on database')
		self.c.execute(req, val)
		
		#Return selected rows as an array
		return self.c.fetchall()
	
	##Retrieve the oldest date in the db
	#
	#@return The smallest timestamp in the db
	def getFirst(self, oldest=True):
		req = 'SELECT * FROM p2data ORDER BY date LIMIT 1'
		self.c.execute(req, ())
		res = self.c.fetchone()
		if res != None:
			res = res[0]
		return res
	
	##Retrieve the last (newest) data in db
	#
  # Can be a relatively long query
  #
	#@return The bigger timestamp
	def getLastData(self):
		req = 'SELECT * FROM p2data ORDER BY date DESC LIMIT 1'
		self.c.execute(req,())
		return self.c.fetchall()
	
	##P2DbStore destructor
	def __del__(self):
		self.c.close()
