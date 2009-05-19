#!/usr/bin/env python
#
# cycle through download dir and show the torrents being grabbed
#
# additionally consult /share/incoming/.torrents.xml to print stats
# 
import sys
from common import *
from xml.dom import minidom, Node
import string
import math
import time
from string import Template
import string
import os.path
import shutil
import tempfile

class SafeWriteFile(object):
	def __init__(self,fileName):
		self._fileName=str(fileName)
		self._tempFile=str(tempfile.mktemp())
		self._fileHandle = open( self._tempFile, 'w' )

	def writeline(self,s):
		self._fileHandle.write( s )
		self._fileHandle.write( '\n' )

	def println(self,s):
		self.writeline(s)

	def close(self):
		self._fileHandle.close()
		shutil.move(self._tempFile, self._fileName)

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
########################################################################

def printmsg(msg,showDate=True,log=True):
	if showDate:
		t = time.strftime( '%Y-%m-%d @ %I:%M:%S %P' )
		print '[%s]: %s' % (t, msg)

		if log:
			appName = os.path.basename(sys.argv[0])
			f = open( os.path.join(DATA_DIR, appName + '.log' ), 'a' )
			f.write( '[%s]: %s\n' % (t,msg) )
			f.close()
	else:
		print msg

def boldTransferRate(n):
	n = long(n)
	s = '%s/s' % human_readable(n)

	if n > 0:
		s = '<b>%s</b>' % s
	return s

def ratioForHash(hash,uid,autostopDir=None):
	ratio = float(0.0)

	stopFile = os.path.join(autostopDir,hash+'.xml')

	if os.path.exists(stopFile):
		ratio = ratioFromAutostopFile(stopFile)
	else:
		stopFile = os.path.join(autostopDir,uid+'.xml')
		if os.path.exists(stopFile):
			ratio = ratioFromAutostopFile(stopFile)
	return ratio

## stolen from btlaunchmanycurses.py
def human_readable(n):
    n = long(n)
    unit = [' B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
    i = 0
    if (n > 999):
	i = 1
	while i + 1 < len(unit) and (n >> 10) >= 999:
	    i += 1
	    n >>= 10
	n = float(n) / (1 << 10)
    if i > 0:
	size = '%.1f' % n + '%s' % unit[i]
    else:
	size = '%.0f' % n + '%s' % unit[i]
    return size
########################################################################

def statsForTorrentNode(torrent):
	mapping = dict()
	torrentPath = findNodeName( torrent, 'fullpath' )
	name = findNodeName( torrent, 'name' ).encode('utf-8')
	fsize = int( findNodeName( torrent, 'filesize' ) )
	hstBytesUp = int(findNodeName( torrent, 'totalUploadBytes'))
	hstBytesDn = int(findNodeName( torrent, 'totalDownloadBytes'))
	rateUp = float(findNodeName( torrent, 'uploadRate' ) )
	rateDn = float(findNodeName( torrent, 'downloadRate' ) )
	status = findNodeName( torrent, 'status' )
	eta = findNodeName( torrent, 'eta' )

	if hstBytesDn > 0:
		mapping['ratio'] = '%.2f' % (float(hstBytesUp) / float(hstBytesDn))
	else:
		mapping['ratio'] = '&nbsp;'

	# 1:1 achieved?
	if status == 'seeding':
		if hstBytesUp > hstBytesDn:
			mapping['tableRowClass'] = 'statusStoppable'
		else:
			mapping['tableRowClass'] = 'statusSeeding'
	else:
		if eta == "complete!":
			 mapping['tableRowClass'] = 'statusOther'
		else:
			 mapping['tableRowClass'] = 'statusDownloading'

	mapping['torrentName'] = name
	mapping['formattedFileSize'] = human_readable(fsize)
	mapping['fileSize'] = fsize
	
	## "dlStatus"
	mapping['status'] = status
	mapping['progressPercentage'] = findNodeName(torrent,'progress')
	mapping['eta'] = eta
	mapping['errorMessage'] = findNodeName(torrent,'msg')

	## down rate
	mapping['bytesDown'] = hstBytesDn
	mapping['formattedBytesDown'] = human_readable(hstBytesDn)
	mapping['rateDown'] = rateDn
	mapping['formattedRateDown'] = boldTransferRate(rateDn)
	mapping['seedCount'] = int( findNodeName( torrent, 'seeds') )		

	## up rate
	mapping['bytesUp'] = hstBytesUp
	mapping['formattedBytesUp'] = human_readable(hstBytesUp) 
	mapping['rateUp'] = rateUp
	mapping['formattedRateUp'] = boldTransferRate(rateUp)
	mapping['peerCount'] = int( findNodeName( torrent, 'peers' ) )

	ownerUID = findNodeName(torrent,'owner')
	hash = findNodeName(torrent,'hash')
	stopRatio = ratioForHash(hash,ownerUID,autostopDir=AUTOSTOPD_DIR)
	mapping['stopRatio'] = '%.2f' % stopRatio

	return mapping
########################################################################

def processDocument(doc):
	tsize = 0
	
	totalBytesUp = 0
	totalBytesDn = 0
	totalRateUp  = 0
	totalRateDn  = 0
	totalIncoming = 0
	
	html = []
	rss = []
	
	mapping = dict()
	mapping['lastGeneratedDate'] = time.ctime()
	
	html.append( TemplatedFile('template.header.html' ).substitute(mapping) )
	#rss.append( TemplatedFile('template.header.rss' ).substitute(mapping) )
	tmpl = TemplatedFile('template.torrent.html')
	
	for torrent in doc.documentElement.childNodes:
		if torrent.nodeName == 'torrent':
			stats = statsForTorrentNode(torrent)
			totalIncoming += long(stats.get('fileSize',0))
			totalRateUp += float(stats['rateUp'])
			totalRateDn += float(stats['rateDown'])
			totalBytesUp += long(stats['bytesUp'])
			totalBytesDn += long(stats['bytesDown'])
	
			html.append( tmpl.substitute(stats) )
	
	## footers
	mapping = dict()
	mapping['formattedTotalBytes'] = human_readable(totalIncoming)
	mapping['formattedTotalBytesUp'] = human_readable(totalBytesUp)
	mapping['formattedTotalRateUp'] = human_readable(totalRateUp)
	mapping['formattedTotalBytesDown'] = human_readable(totalBytesDn)
	mapping['formattedTotalRateDown'] = human_readable(totalRateDn)
	
	html.append( TemplatedFile( 'template.footer.html' ).substitute( mapping ) )

	outp = SafeWriteFile('status.html')
	outp.writeline( string.join(html) )
	outp.close()
	
def process():
	try:
		doc = minidom.parse( TORRENT_XML )
		processDocument(doc)
	except:
		printmsg( 'Caught exception parsing document: %s' % str(sys.exc_info()) )
	return True

# main:
sleepTime = 30
printmsg( 'Will sleep for %d secs' % sleepTime)

cont = True

while cont:
	try:
		cont = process()
		time.sleep(sleepTime)
	except KeyboardInterrupt:
		cont = False
	#except:
	#       print 'Unhandled exception: ', sys.exc_info()
	#       cont = False

printmsg( 'Exiting gracefully!')
exit()
