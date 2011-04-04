#!/usr/bin/python
#
# show items that are expiring and when they expire
#

from common import *
import sys
import os
import stat
import os.path
import datetime
import string
from string import Template

DELETE_DAYS_OLD=22
# this should be externalized as a . file in data

## move to common
class TemplatedFile(object):
        def __init__(self,templateFile):
                self._templateFile=templateFile
                self._contents = self._contentsOfFile(self._templateFile)

        def _contentsOfFile(self,fileName):
                f = open( fileName, 'r')
                s = f.read()
                f.close()
                return s

        def substitute(self,mapping):
                s = Template(self._contents).substitute(mapping)
                return s

ROOT_DIR='/share/expired'

def findExpirationDate(fn):
	stats = os.stat( fn )
	lastmod = datetime.date.fromtimestamp( stats[8] )
	deleteDate = lastmod + datetime.timedelta(days=DELETE_DAYS_OLD)
	return deleteDate

def calculateSize(fn):
	bytes = 0
	filecount= 0

	if os.path.isdir( fn ):
		for root, dirs, files in os.walk( fn ):
			for file in files:
				filen = os.path.join( root, file )
				st = os.stat( filen )
				size = st[stat.ST_SIZE]
				bytes += size
				filecount = filecount + 1
	else:
		st = os.stat( fn )
		size = st[stat.ST_SIZE]
		bytes = size
		filecount = 1
	return (bytes,filecount)
#### 
if len(sys.argv) != 2:
	print 'Usage: %s <output file>' % sys.argv[0]
	sys.exit()
outputFile = sys.argv[1]
dates = {}

torrentStore = initTorrentStore()

# figure out how many days old
cfg = os.path.join( torrentStore.dataDir(), 'find-expired-days-old' )
f = open( cfg, 'r' )
cfgs = f.read()
f.close()
DELETE_DAYS_OLD=int(cfgs)

for file in os.listdir( ROOT_DIR ):
	filen = os.path.join( ROOT_DIR, file )
	dd = findExpirationDate( filen )
	delFiles = []

	if dates.has_key( dd ):
		delFiles = dates.get( dd )
	delFiles.append( filen )
	dates[dd] = delFiles

keys = dates.keys()
keys.sort()

# set up base file
html = []
totalFiles = 0
totalBytes = 0
mapping = {}
html.append( TemplatedFile(os.path.join( torrentStore.templateDir(), 'template.retire-header.html' ) ).substitute(mapping) )

tmpl = TemplatedFile( os.path.join( torrentStore.templateDir(), 'template.retire-item.html' ) )

for key in keys:
	mapping = {}
	mapping['formattedRetireDate'] = key.isoformat()
	for value in dates[key]:
		mapping['fullFileName'] = value
		mapping['fileName'] = os.path.basename( value )
		(fsize,fcount) = calculateSize( value )
		mapping['rawFileSize'] = fsize
		mapping['formattedFileSize' ] = human_readable( fsize )
		s = tmpl.substitute( mapping )
		html.append( s )
		totalFiles  = totalFiles + fcount
		totalBytes = totalBytes + fsize

mapping = {}
mapping['formattedFileCount'] = str(totalFiles)
mapping['formattedTotalBytes'] = human_readable( totalBytes )
mapping['rawTotalBytes'] = totalBytes

html.append( TemplatedFile(os.path.join( torrentStore.templateDir(), 'template.retire-footer.html' ) ).substitute(mapping) )

f = SafeWriteFile( outputFile )
f.write( string.join( html ) )
f.close()
os.chmod( outputFile, 0644 )
