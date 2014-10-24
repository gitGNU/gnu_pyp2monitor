#!/usr/bin/python
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

#Python libs import
import serial
import time

#pyP2Monitor import
import p2com 
from p2com import *
import p2proto
from p2proto import *
import p2msg
from p2msg import *
import utils

#Argument parse
args = utils.argParse('monitor')

#Init output (logging and verbosity)
utils.initLogging(args['verbosity'], args['log_file'], args['log_level'], args['log_num'], args['log_size'])

#Store all the data's storage method
storage = []
if args['database'] != None:
	for c in args['database']:
		storage.append(('sqlite',c))
if args['file'] != None:
	for c in args['file']:
		storage.append(('file',c))
if args['csv'] != None:
	for c in args['csv']:
		storage.append(('csv',c))

#Serial port opening
com = P2Furn(args['port'])

#Running wanted stages
for stage in args['stage']:
	print 'stage : '+stage
	if stage == 'all':
		com.runAuth(args['user'])
		com.runInit()
		com.readData(storage)
	elif stage == 'auth':
		com.runAuth(args['user'])
	elif stage == 'init':
		com.runInit()
	elif stage == 'data':
		com.readData(storage)

#Serial port closing
com.stop()
