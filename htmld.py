#!/usr/bin/env python
#
# cycle through download dir and show the torrents being grabbed
#
# additionally consult /share/incoming/.torrents.xml to print stats
# 
from sys import *
from common import *
from xml.dom import minidom, Node
import string
import math
import time
import os.path
import os
import shutil
import tempfile
from common import *
import sys

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
#####

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



def processRss(doc):
	outp = SafeWriteFile('status-rss.xml')
	outp.println('<?xml version="1.0" encoding="ISO-8859-1"?>' )
	outp.println( '<rss version="2.0">' )
	outp.println( '<channel>' )
	outp.println( '<title>Status</title>' )
	outp.println( '<link>http://www.howiesilberg.com/stuff.html?from=rss</link>' )
	outp.println( '<language>en-us</language>' )
	outp.println( '<copyright>1969-2036 HMS</copyright>' )

	for torrent in doc.documentElement.childNodes:
		if torrent.nodeName == 'torrent':
			name = findNodeName( torrent, 'name' ).encode('utf-8')
			rateUp = float(findNodeName( torrent, 'uploadRate' ) )
			rateDn = float(findNodeName( torrent, 'downloadRate' ) )
			numPeers = int( findNodeName( torrent, 'peers' ) )
			numSeeds = int( findNodeName( torrent, 'seeds') )
			fsize = int( findNodeName( torrent, 'filesize' ) )
			status = findNodeName( torrent, 'status' )
			bytesUp = int(findNodeName( torrent, 'totalUploadBytes'))
			bytesDn = int(findNodeName( torrent, 'totalDownloadBytes'))
			hash = findNodeName(torrent,'hash')

			outp.println( '<item>')
			outp.println( '<title><![CDATA[%s]]></title>' % name)
			outp.println( '<author>htmld</author>' )
			outp.println( '<pubDate>%s</pubDate>' % time.ctime( time.time() ) )
			outp.println( '<link>http://nowhere?hash=%s</link>' % hash )
			outp.println( '<description>' )
			
			# upBytes @ rate || dnBytes @ rate (% complete)
			if status != 'seeding': 
				eta = findNodeName( torrent, 'eta' )
				progressPercentage = findNodeName(torrent,'progress')

				outp.println( '%s complete: %s (%s @ %s dn)' % (progressPercentage, eta, human_readable(bytesDn), human_readable(rateDn)) )
			else:
				outp.println( '%s @ %s up' % (human_readable(bytesUp), human_readable(rateUp)))  
				if bytesDn > 0:
					outp.println( ', R: %.2f' % (float(bytesUp) / float(bytesDn)) )
					ownerUID = findNodeName(torrent,'owner')
					stopRatio = ratioForHash(hash,ownerUID,autostopDir=AUTOSTOPD_DIR)
			
					if stopRatio > 0.0:
						outp.println( '/%.2f' % stopRatio )					
			
			outp.println( '</description>')
			outp.println( '</item>')
	outp.println('</channel>' )
	outp.println('</rss>' )
	outp.close()
			
def processHtml(doc):
	tsize = 0
	
	outp = SafeWriteFile('status.html')
	outp.println( "<head>" )
	outp.println( '  <title>Downloads</title>' )
	outp.println( '</head>' )
	# TODO: separate out into its own .css
	outp.println( '<link rel=\"stylesheet\" href=\"/tinfo.css\" type=\"text/css\">' )
	
	# do not cache this page!
	outp.println( '<META HTTP-EQUIV=\"Pragma\" CONTENT=\"no-cache\">' )
	outp.println( '<META HTTP-EQUIV=\"Expires\" CONTENT=\"-1\">' )
	outp.println( '<body>' )
	outp.println( '' )
	
	# last updated time
	outp.println( '<span class=\"timestamp\"><b>Last Generated</b>: %s</span><br/><br/>' % time.ctime( time.time() ) )
	
	outp.println( '' )
	outp.println( '<table border=\"1\" cellspacing=\"0\" cellpadding=\"2\" width=\"100%\" class=\"mainTable\">' )
	outp.println( '<tr class=\"tableHeader\">' )
	outp.println( '	<th width=\"75%\" align=\"center\">Name [Size]</font></th>' )
	outp.println( '	<th width=\"10%\" align=\"center\">Up @ Rate</font></th>' )
	outp.println( '	<th width=\"10%\" align=\"center\">Dn @ Rate</font></th>' )
	outp.println( ' <th width=\"5%\" align=\"center\">Ratio</font></th>' )
	outp.println( '</tr>' )
	outp.println( '' )
	
	totalBytesUp = 0
	totalBytesDn = 0
	totalRateUp  = 0
	totalRateDn  = 0
	totalIncoming = 0
	
	for torrent in doc.documentElement.childNodes:
	
		if torrent.nodeName == 'torrent':
			torrentPath = findNodeName( torrent, 'fullpath' )
	
			name = findNodeName( torrent, 'name' ).encode('utf-8')
			fsize = int( findNodeName( torrent, 'filesize' ) )
			totalIncoming += fsize
			hstBytesUp = int(findNodeName( torrent, 'totalUploadBytes'))
			hstBytesDn = int(findNodeName( torrent, 'totalDownloadBytes'))
			totalBytesUp += hstBytesUp
			totalBytesDn += hstBytesDn
			rateUp = float(findNodeName( torrent, 'uploadRate' ) )
			rateDn = float(findNodeName( torrent, 'downloadRate' ) )
			totalRateUp += rateUp
			totalRateDn += rateDn
			status = findNodeName( torrent, 'status' )
			eta = findNodeName( torrent, 'eta' )
			numPeers = int( findNodeName( torrent, 'peers' ) )
			numSeeds = int( findNodeName( torrent, 'seeds') )
	
			# 1:1 achieved?
			ratioOK = False
			if hstBytesUp > fsize and status == "seeding" and hstBytesUp > hstBytesDn:
				outp.println( '<tr class=\"seededStoppable\">' )
				ratioOK = True
			else:
				outp.println( '<tr>' )
	
			outp.println( '<td align=\"left\">%s <span class=\"sizeSlug\">[%s]</span>' % (name, human_readable(fsize)) )
	
			if status != "seeding":
				progressPercentage = findNodeName(torrent,'progress')
				msg = findNodeName(torrent,'msg')
	
				if eta == "complete!":
					outp.println( '<br/><span class=\"dlStatus\"><b>Status</b>: %s (%s)</span>' % (status, progressPercentage) )
				else:
					outp.println( '<br/><span class=\"dlEta\"><b>ETA</b>: %s [%s complete]</span>' % (eta,progressPercentage) )
				if msg is not None and len(msg) > 0:
					outp.println( ' <span class=\"errMsg\">%s</span>' % msg )
			outp.println( '</td>' )
	
			outp.println( '<td nowrap=\"nowrap\" align="center">%s @ %s<br/>to %d peers</td>' % (human_readable(hstBytesUp), boldTransferRate(rateUp), numPeers) )
			outp.println( '<td nowrap=\"nowrap\" align="center">%s @ %s<br/>from %d seeds</td>' % (human_readable(hstBytesDn),boldTransferRate(rateDn), numSeeds) )
	
			outp.println( '<td nowrap=\"nowrap\" align="center">' )
	
			if hstBytesDn > 0:
				outp.println( '%.2f' % (float(hstBytesUp) / float(hstBytesDn)) )
			else:
				outp.println( '&nbsp;' )
	
			ownerUID = findNodeName(torrent,'owner')
			hash = findNodeName(torrent,'hash')
			stopRatio = ratioForHash(hash,ownerUID,autostopDir=AUTOSTOPD_DIR)
	
			if stopRatio > 0.0:
				outp.println( '<br/>(%.2f)' % stopRatio )
	
			outp.println( '</td>' )
			outp.println( '</tr>' )
	# totals
	outp.println( '<tr class=\"tableFooter\">' )
	outp.println( ' <td nowrap=\"nowrap\" align="right">= %s</td>' % human_readable(totalIncoming) )
	outp.println( ' <td nowrap=\"nowrap\" align="right">= %s @ %s/s</td>' % (human_readable(totalBytesUp),human_readable(totalRateUp)) )
	outp.println( ' <td nowrap=\"nowrap\" align="right">= %s @ %s/s</td>' % (human_readable(totalBytesDn),human_readable(totalRateDn)) )
	outp.println( ' <td nowrap=\"nowrap\" align="right">&nbsp;</td>' )
	outp.println( '</tr>' )
	
	# /totals
	outp.println( '</table>' )
	outp.println( '</body>' )
	outp.println( '</html>' )
	outp.close()

def process():
	doc = minidom.parse( TORRENT_XML )
	printmsg('Processing...')
	processRss(doc)
	processHtml(doc)
	return True

def printmsg(msg,showDate=True):
	if showDate:
		t = time.strftime( '%Y-%m-%d @ %I:%M:%S %P' )
		print '[%s]: %s' % (t, msg)
	else:
		print msg

# main:
sleepTime = MAX_SLEEP_TIME
printmsg( 'Will sleep for %d secs' % sleepTime)

cont = True

while cont:
	try:
		cont = process()
		time.sleep(sleepTime)
	except KeyboardInterrupt:
		cont = False
	#except:
	#	print 'Unhandled exception: ', sys.exc_info()
	#	cont = False

printmsg( 'Exiting gracefully!')
exit()
