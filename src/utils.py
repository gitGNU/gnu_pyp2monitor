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

##@package Store usefull functions


"""
Doxygen main page
"""
##@mainpage pyP2Monitor doxygen documentation
#
# @section mpfi Fonctionnal parts index
#
# @subsection mpllfc Low level furnace communication
#
# - @ref p2com "Serial port communication package"
#
# @subsection mpfmp Furnace message processing
#
# - @ref p2msg "Raw message processing and handling package"
# - @ref p2dbstore "Database message storage"
# - @ref p2data "Furnace frame formating and GnuPlot generation"
# 
# @subsection mpfcp Furnace communication protocol
#
# - @ref p2proto Furnace protocol handling package
#
# @section mpthanks Thanks
#
# - Hervé Wacheux <herve.wacheux@free.fr>
# - Thomas Fahr <thomasfahr@gmx.de>
# - Thomas Rigert <thomas@rigert.com>
#

##@defgroup lowlevel Low level communication

##@defgroup msgprocess Furnace message processing

##@defgroup comproto Furnace communication protocol

##Stores the monitoring programm version
VERSION="pyP2Monitor v0.3.4"
##Stores the reader programm version
VERSION_READER="pyP2DataReader v0.2"

import sys
import argparse
import logging
import logging.handlers

##Function used to parse options and return a dict with all options in it
#
#		Actually options are (see below for meaning):
#			background
#			data_wait
#			database
#			csv
#			file
#			delay
#			log_file
#			log_level
#			log_num
#			log_size
#			max_data
#			max_time
#			port
#			print_data
#			quiet
#			stage
#			user
#			verbosity
#			version
def argParse(prog="monitor", usage = False):
	u = usage
	if prog=="monitor":
		return monitorArgParse(u)
	else:
		return readerArgParse(u)

## Use argParse to parse command line options for the monitor programm
# 
# @return A dict with options value
def monitorArgParse(usage = False):
	parser = argparse.ArgumentParser(prog="pyP2Monitor",description=VERSION+' : Get and store datas from a P2 Furnace using a serial port.',
									epilog='pyP2Monitor is under GNU GPL')

	serial_arg = parser.add_argument_group('Serial port options')

	data_arg = parser.add_argument_group('Data processing options')

	run_arg = parser.add_argument_group('Runtime options')
	
	daemon_arg = parser.add_argument_group('Daemon options')

	log_arg = parser.add_argument_group('Logging options')


	parser.add_argument('-v', '--version', action='store_const', const=True, default=False,
						help='Display the programm version and exit')

	serial_arg.add_argument('-p', '--port', action='store', type=str, default='/dev/ttyS0',
						help='Set the serial port file wich the furnace is plugged ( exemple /dev/ttyUSB0 )')
	serial_arg.add_argument('-D', '--delay', action='store', type=int, metavar='MICROSEC',
						help='Set the number of microseconds to wait between to send on the serial port')

	data_arg.add_argument('-d', '--database', action='append', type=str, metavar='SQLITE_DB_FILE',
						help='Tell the programm to store data in SQLITE_DB_FILE sqlite database')
	data_arg.add_argument('-c', '--csv', action='append', type=str, metavar='CSV_FILE',
						help='Tell the programm to store data in CSV_FILE file in csv format')
	data_arg.add_argument('-F', '--file', action='append', type=str, metavar='FILENAME',
						help='Tell the programm to store data in FILENAME file as \'date:[invalid]:hex_string\' (it is the only storage keeping invalid messages)')
	data_arg.add_argument('-P', '--print-data', action='store_const', const=True, default=False,
							help='Print received data on stdout')
	data_arg.add_argument('-w', '--data-wait', action='store', type=float, default=1, metavar='SECS',
						help='Time to wait between two data request')
						
	run_arg.add_argument('-t', '--max-time', action='store', type=int, metavar='SECS',
						help='Tell the programm to stop after SECS seconds')
	run_arg.add_argument('-n', '--max-data', action='store', type=int, metavar='INTEGER',
						help='Tell the programm to stop after receiving NUMBER valid datas')
	run_arg.add_argument('--stage', action='append', choices=['auth', 'init', 'data', 'all'], default=None,
						help='Indicate wich stage in wich order to run (for example "--stage data init" while run the exchange stage before the init stage)')
	run_arg.add_argument('-u', '--user', choices=['plumber', 'normal', 'normal2', 'service'], default='service',
						help='Set the user used to authenticate on the furnace')

	daemon_arg.add_argument('-B', '--background', action='store_const', const=True, default=False,
						help='Tell the programm to run in background (not implemented yet)')
	daemon_arg.add_argument('-K', '--stop', action='store_const', const=True, default=False,
						help='Try to kill a pyP2SerialMonitor in background')
	daemon_arg.add_argument('-i', '--pidfile', action='store', type=str, default="/tmp/pyP2SerialMon.pid", metavar='PIDFILE',
						help='Pidfile name (used with -B or -K)')


	log_arg.add_argument('--verbosity', action='store', choices=[ 'critical', 'error', 'warn', 'info', 'debug', 'silent'], default='error',
						help='Set the log level for console output')
	log_arg.add_argument('-q', '--quiet', '--silent', action='store_const', const=True, default=False,
						help='Run silentely (no console output)')
	log_arg.add_argument('-f', '--log-file', action='store', type=str,
						help='Set the log file')
	log_arg.add_argument('--log-level', action='store', choices=['info', 'warn', 'error', 'debug', 'silent'], default='warn',
						help='Set the log level for logfile')
	log_arg.add_argument('--log-size', action='store', type=int, default=5120, metavar='BYTES',
						help='Set the maximum size for a logfile before rotating to another logfile')
	log_arg.add_argument('--log-num', action='store', type=int, default=5, metavar='INTEGER',
						help='Set the number of logfile to keep')
			
	if usage:
		parser.print_usage(sys.stderr)
		exit(1)		
	
	args = parser.parse_args()

	res = vars(args)

	if res['stage'] == None:
		res['stage'] = ['all']
	
	return vars(args)

## Use argParse to parse command line options for the reader programm
# 
# @return A dict with options value
def readerArgParse(usage = False):
	parser = argparse.ArgumentParser(prog="pyP2DataReader",description=VERSION_READER+' : Get datas from a sqlite database and output a picture representing datas giving a format.',
			epilog='pyP2DataReader is part of pyP2Monitor wich is is under GNU GPL')

	serial_arg = parser.add_argument_group('Serial port options')

	db_arg = parser.add_argument_group('Database options')

	in_arg = parser.add_argument_group('Input file options')

	out_arg = parser.add_argument_group('Output options')

	log_arg = parser.add_argument_group('Logging options')
			

	db_arg.add_argument('-d', '--database', action='store', type=str, default=False, metavar='SQLITE_DB_FILE',
			help='The database storing datas')
	db_arg.add_argument('-q', '--query', action='append', type=str, metavar='QUERY_STRING',
			help='Queries to be done')
	db_arg.add_argument('-s', '--separator', action='store', type=str, default=',', metavar='STRING',
			help='One or more characters used as argument separator in a query (default is ",")')
	db_arg.add_argument('--field-list', action='store_const', const=True, default=False,
			help='List data fields and them numbers. Then exit.');

	out_arg.add_argument('-o', '--output', action='store', type=str, default='out', metavar='FILENAME',
			help='Output file')
	out_arg.add_argument('-f', '--format', action='store', choices=['csv', 'png', 'jpg', 'svg', 'gnuplot'], default='gnuplot', metavar='FORMAT',
			help='Output format (csv, png, jpg, svg, gnuplot)')
	out_arg.add_argument('-t', '--title', action='store', type=str, default=None, metavar='STRING',
			help='Output title')
	out_arg.add_argument('-r', '--resolution', action='store', type=str, default=None, metavar='width,height',
			help='Set the size of an output image')

	out_arg.add_argument('--csvdump', action="store", type=str, default=None, metavar='FILENAME.csv', help='Dump the db into a csv file ( - for stdout)')
	
	############
	#	Not yet implemented
	#
	"""
	in_arg.add_argument('-i', '--input', action='store', type=str, metavar='GNUPLOT_DATAFILE',
			help='Use this datafile as input to generate output')

	in_arg.add_argument('-m', '--merge', action='store', type=str, metavar='GNUPLOT_DATAFILE',
			help='Tell the programm to merge datas with this data file')
	"""
	#
	#
	############	
		
	parser.add_argument('--verbosity', action='store', choices=[ 'critical', 'error', 'warn', 'info', 'debug', 'silent'], default='error',
			help='Set the log level for console output')
	parser.add_argument('-v', '--version', action='store_const', const=True, default=False,
			help='Display the programm version and exit')

	if usage:
		parser.print_usage(sys.stderr)
		exit(1)

	args = parser.parse_args()

	res = vars(args)

	return vars(args)



##Function used to initialise the logger
#
# Use logging package
#
# @param verbosity Use to set the logging level for console output
# @param log_file Use to set the base filename for log files
# @param log_level Use to set the logging level for log files
# @param log_num An integer telling how many logfile to keep
# @param log_size Size in byte to trigger logs rotation ( 
def initLogging(verbosity, log_file = None,log_level = None,log_num = None,log_size = None):
	# create logger
	logger = getLogger()
	logger.setLevel(logging.DEBUG)

	formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

	# create console handler and set level to debug
	ch = logging.StreamHandler()
	
	lvl = getLogLevelConst(verbosity)
	
	if lvl< 1000:
		ch.setLevel(lvl)
		logger.addHandler(ch)
		ch.setFormatter(formatter)

	if log_file != None and log_num != None and log_size != None:
		fl = logging.handlers.RotatingFileHandler(log_file, mode='a', maxBytes=log_size, backupCount=log_num, delay=True)
		
		lvl = getLogLevelConst(log_level)
		if lvl < 1000:
			fl.setLevel(lvl)
			logger.addHandler(fl)
			fl.setFormatter(formatter)

	logger.debug('logger configured')

##Convert a level get from the command line to a real logging level
def getLogLevelConst(strlvl):
		res = logging.ERROR
		
		if strlvl == 'debug':
			res = logging.DEBUG
		elif strlvl == 'info':
			res = logging.INFO
		elif strlvl == 'warn':
			res = logging.WARNING
		elif strlvl == 'error':
			res = logging.ERROR
		elif strlvl == 'critical':
			res = logging.CRITICAL
		elif strlvl == 'silent':
			res = 1000
		
		return res


##Return the logger used in the whole application
def getLogger():
	return logging.getLogger('pyP2Monitor')


