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
import time

#pyP2Monitor import
import p2com 
from p2com import *
import p2proto
from p2proto import *
import p2msg
from p2msg import *
import utils

com = None
pidfile= ""

##Gentle exit to manage sigint
def gentle_exit(signal, frame):
	logger.critical("signal caught, exiting")
	#Serial port closing
	com.stop()
	os.unlink(pidfile)
	sys.exit(0)

##"Fork" into background
def start_daemon(pidfile):
	arg = []
	for e in sys.argv:
		if e != '-B' and e != '--background':	#Deleting background option
			arg.append(e)
	logger.debug("Starting background process...")
	pid = os.spawnv(os.P_NOWAIT,arg[0], arg)
	fdpid = open(pidfile,"w+")
	fdpid.write(str(pid))
	fdpid.close()
	
	logger.debug("Background process started. Pid = "+str(pid))
	
	return pid


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

#Running wanted stages
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
		
	if stages&1:
		again = 0
                while again<maxretry:
                        try:
                                com.runAuth(P2Furn.userId(args['user']))
                                again = maxretry+1
                        except p2com.P2ComError as e:
				if again < maxretry:
                                        logger.error("Authentication stage failed : "+str(e))
                                        again+=1
                                else:
                                        logger.critical("Authentication stage failed again after "+str(maxretry)+" attempts")
                                        raise e

	if stages&2:
		again = 0
                while again<maxretry:
                        try:
                                com.runInit()
                                again = maxretry+1
                        except p2com.P2ComError as e:
				if again < maxretry:
                                	logger.error("Initialisation stage failed : "+str(e))
                                	again+=1
				else:
                                        logger.critical("Initialisation stage failed again after "+str(maxretry)+" attempts")
                                        raise e

	if stages&3:
		again = 0
                while again<maxretry:
                        try:
                                com.readData(float(args['data_wait']),storage)
                                again = maxretry+1
                        except p2com.P2ComError as e:
				if again < maxretry:
                                        logger.error("DataReading stage failed : "+str(e))
                                        again+=1
                                else:  
                                        logger.critical("DataReading stage failed again after "+str(maxretry)+" attempts")
                                        raise e

#Serial port closing
com.stop()
