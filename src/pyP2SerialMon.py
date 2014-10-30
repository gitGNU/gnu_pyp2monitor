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
import serial, signal, time, sys, os

#pyP2Monitor import
from p2com import *
from p2proto import *
from p2msg import *
from p2monitor import *

com = None
pidfile= ""

signal.signal(signal.SIGINT, gentle_exit)
signal.signal(10, gentle_exit)

#Argument parse
args = utils.argParse('monitor')

#Init output (logging and verbosity)
utils.initLogging(args['verbosity'], args['log_file'], args['log_level'], args['log_num'], args['log_size'])

logger = utils.getLogger()

#start background process to start a daemon
pidfile = args['pidfile']
if args['background']:
	exit(start_daemon(pidfile))
elif args['stop']: #or kill an existing daemon
	pidfd = open(pidfile,"r")
	pid = int(pidfd.read())
	os.kill(pid, 10)
	logger.debug("Sig 10 send to process",pid)
	exit(0)
	

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

"""
	if we got only one stage and this stage is all
	run the monitor and try to handle timeouts, errors etc to keep the
	monitoring process alive
"""
if len(args['stage']) == 1 and args['stage'][0] == 'all':
	
	stages = [1,2,3]
	curStage = 0
	retry = 0
	
	while True:
		
		for stage in stages:
			try:
				runMonitorStages(com, stages[curStage], 3)
			except p2com.P2ComError as e:
				#After 3 retry the current stage failed
				#We wait 5 seconds then we begin the whole process again
				logger.error("To many fails. Waiting and starting with authentication again.")
				time.sleep(5)
				break
	
#Else running the multiples wanted stages
for stage in args['stage']:
	maxretry = 3
	
	stages = 0	

	if stage == 'all':
		stages = 7
	elif stage == 'auth':
		stages = 1
	elif stage == 'init':
		stages = 2
	elif stage == 'data':
		stages = 3
		
	runMonitorStages(com, stages, maxretry)

#Serial port closing
com.stop()
