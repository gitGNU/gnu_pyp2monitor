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

import sys
import signal #Portability problem ???

import pipes

#import Gnuplot, Gnuplot.funcutils

import p2dbstore
import p2data
import utils


args = utils.argParse('reader')

#Init output (logging and verbosity)
utils.initLogging(args['verbosity'])


if args['csvdump'] != None and args['database']:
	p2data.csvDump(args['database'], args['csvdump'])
	exit(0)

if 'field_list' in args and args['field_list']:
	names = p2data.colNames()
	print "Field list :"
	for i in range(len(names)):
		print i,':\t'+names[i]
	exit(0)

print args
if args['database']:
	if args['query'] != None:
		gp = pipes.Template()
		gp.append('gnuplot --persist', '--')
		g = gp.open('/tmp/pyp2dataread.pipe', 'w')
		
		datas = p2data.P2Datas(args['database'],args['query'],args['separator'])
		
		datas.populate()
		
		rep = datas.getDateTimeFormats()
		
		
		if not (args['format'] == None or args['format'] == 'gnuplot'):
			if args['format'] == 'png':
				g.write('set terminal png')
			elif args['format'] == 'svg':
				g.write('set terminal svg')
			elif args['format'] == 'jpg':
				g.write('set terminal jpg')
			if args['resolution'] != None:
				g.write(' size '+args['resolution'])
			g.write('\n')
			g.write('set output "'+args['output']+'"\n')
		else:
			g.write('set terminal wxt\n')
		
		if args['title'] != None:
			g.write('set title '+args['title']+'\n')
		if not rep is False:
			(inFmt,outFmt) = rep
			g.write('set xdata time\n')
			g.write('set timefmt "'+inFmt+'"\n')
			g.write('set format x "'+outFmt+'"\n')
			g.write('set timefmt "'+inFmt+'"\n')
		
		g.write(datas.getPlotCommand())
		g.flush()
		
		if args['format'] == 'gnuplot':
			raw_input('Please press return to continue...\n')
		
		g.close()
		
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
