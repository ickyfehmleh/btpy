#!/usr/bin/python
#
# print contents of a dbm
#

import sys
import shelve
import anydbm

if len(sys.argv) == 1:
	print 'Usage: %s <path to dbm file>' % sys.argv[0]
	exit(2)

stats = None

try:
	stats = shelve.open( sys.argv[1], flag='r')
except:
	stats = anydbm.open( sys.argv[1], 'r' )

if len(sys.argv) > 2:
	for key in sys.argv[2:]:
		print '%s:%s' % (key,stats[key])
else:
	for key in stats:
		print '%s:%s' % (key, stats[key])
stats.close()
