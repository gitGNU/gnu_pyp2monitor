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

import os, sys

import utils
from p2proto import *

logger = utils.getLogger()

##Gentle exit to manage sigint
# 
# A signal handler function used in signal.signal to cacth SIGINT and
# and signal 10
#
def gentle_exit(signal, frame):
	logger.critical("signal caught, exiting")
	#Serial port closing
	com.stop()
	os.unlink(pidfile)
	sys.exit(0)

##"Fork" into background
#
# @param pidifle The name of the file storing the daemon pid
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

##Run the wanted stages
#
# @param com The p2proto::P2Furn object
# @param stages A value between 1 and 7 ( &1 for auth &2 for init &3 for data reading)
# @param maxretry Tells how many time each stage can fail before raising an error
def runMonitorStages(com, stages, maxretry):
	
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
