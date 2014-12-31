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

import sys, os
import signal #Portability problem ???
import tempfile

import pipes

#import Gnuplot, Gnuplot.funcutils

import p2dbstore
import p2data
import utils


args = utils.argParse('reader')

#Init output (logging and verbosity)
utils.initLogging(args['verbosity'])

logger = utils.getLogger()


if args['csvdump'] != None and args['database']:
	p2data.csvDump(args['database'], args['csvdump'])
	exit(0)

if args['last_data'] != None:
	p2data.csvLastDataDump(args['last_data'])
	exit(0)

if 'field_list' in args and args['field_list']:
	names = p2data.colNames()
	print "Field list :"
	for i in range(len(names)):
		print i,':\t'+names[i]
	exit(0)

if args['database']:
	if args['query'] != None:
		datas = p2data.P2Datas(args['database'],args['query'],args['separator'])
		
		datas.populate()
		
		if args['format'] == 'csv':
			
			#opening output file
			if args['output'] == '-':
				cvsout=sys.stdout
			else:
				cvsout = open(args['output'], "w+");
			
			#csv dumping
			datas.getPlotData(True, cvsout,';')
			
			if args['output'] != '-':
				cvsout.close()
			
		else:
			#gnuplot command preparation
			gbuff = ""
			g = tempfile.NamedTemporaryFile('w+',-1,'pyP2gnuplotcommand')
			rep = datas.getDateTimeFormats()
			
			if not (args['format'] == None or args['format'] == 'gnuplot'):
				if args['format'] == 'png':
					gbuff+='set terminal png'
				elif args['format'] == 'svg':
					gbuff+='set terminal svg'
				elif args['format'] == 'jpg':
					gbuff+='set terminal jpg'
				if args['resolution'] != None:
					gbuff+=' size '+args['resolution']
				gbuff+='\n'
				gbuff+='set output "'+args['output']+'"\n'
			else:
				gbuff+='set terminal wxt\n'
			
			if args['title'] != None:
				gbuff+='set title "'+args['title']+'"\n'
			if not rep is False:
				(inFmt,outFmt) = rep
				gbuff+='set xdata time\n'
				gbuff+='set timefmt "'+inFmt+'"\n'
				gbuff+='set format x "%H:%M:%S"\n'
				gbuff+='set timefmt "'+inFmt+'"\n'
				gbuff+='set y2tics nomirror\n'
				gbuff+='set autoscale y\n'
				gbuff+='set autoscale y2\n'
				
			#adding the plot command (it loads data in a file also)
			gbuff += datas.getPlotCommand()
			logger.debug("Writing gnuplot options : "+ gbuff)
			g.write(gbuff)
			g.flush()
			
			os.system('gnuplot --persist "'+g.name+'"')
			
			if args['format'] == 'gnuplot':
				raw_input('Please press return to continue...\n')
			
			g.close()
		exit(0)
		
	else:
		print >> sys.stderr, 'Error, no query specified with database'
		utils.argParse('reader','usage')
		exit(1)
#elif args['input']:
#	print 'Not implemented yet'
else:
	print >> sys.stderr, 'Error, no input specified with -d or -i'
	utils.argParse('reader','usage')
	exit(1)
	

exit()
