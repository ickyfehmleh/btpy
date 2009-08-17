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
import pwd

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

def boldTransferRate(n):
	n = long(n)
	s = '%s/s' % human_readable(n)

	if n > 0:
		s = '<b>%s</b>' % s
	return s

########################################################################

class HtmlOutputter(object):
	def __init__(self,outputHtmlFile):
		self._htmlFile=outputHtmlFile
		self._log=MessageLogger('htmld')

	def statsForTorrentNode(self,torrent):
		mapping = dict()
		torrentPath = findNodeName( torrent, 'fullpath' )
		name = findNodeName( torrent, 'name' ).encode('utf-8')
		fsize = long( findNodeName( torrent, 'filesize' ) )
		hstBytesUp = long(findNodeName( torrent, 'totalUploadBytes'))
		hstBytesDn = long(findNodeName( torrent, 'totalDownloadBytes'))
		rateUp = float(findNodeName( torrent, 'uploadRate' ) )
		rateDn = float(findNodeName( torrent, 'downloadRate' ) )
		status = findNodeName( torrent, 'status' )
		eta = findNodeName( torrent, 'eta' )
		started = float(findNodeName( torrent, 'started' ))

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

		## start date
		mapping['started'] = started
		mapping['formattedStartDate'] = time.ctime( started )
		age = time.time() - started
		mapping['age'] = age
		mapping['formattedAge'] = hours(age)
	
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

		## owner
		ownerUID = findNodeName(torrent,'owner')
		ownerName = pwd.getpwuid(ownerUID)[0]
		mapping['ownerUID'] = ownerUID
		mapping['ownerName'] = ownerName

		hash = findNodeName(torrent,'hash')
		stopRatio = ratioForHash(hash,ownerUID,autostopDir=AUTOSTOPD_DIR)
		mapping['stopRatio'] = '%.2f' % stopRatio

		return mapping

	def processDocument(self,doc):
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
	
		html.append( TemplatedFile(os.path.join( TEMPLATE_DIR, 'template.header.html' ) ).substitute(mapping) )
		#rss.append( TemplatedFile(os.path.join( TEMPLATE_DIR, 'template.header.rss' ) ).substitute(mapping) )
		tmpl = TemplatedFile(os.path.join( TEMPLATE_DIR, 'template.torrent.html' ) )
	
		for torrent in doc.documentElement.childNodes:
			if torrent.nodeName == 'torrent':
				stats = self.statsForTorrentNode(torrent)
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
	
		html.append( TemplatedFile( os.path.join( TEMPLATE_DIR, 'template.footer.html' ) ).substitute( mapping ) )

		outp = SafeWriteFile('status.html', 0755)
		outp.writeline( string.join(html) )
		outp.close()
	
	def process(self):
		try:
			doc = minidom.parse( TORRENT_XML )
			self.processDocument(doc)
		except:
			self.printmsg( 'Caught exception parsing document: %s' % str(sys.exc_info()) )
		return True

	def printmsg(self,s):
		self._log.printmsg(s)

	def close(self):
		self._log.close()
############################################################################################################

# main:
sleepTime = 30

cont = True
OUTPUT_FILE='status.html'
p = HtmlOutputter(OUTPUT_FILE)
p.printmsg('Outputting to %s' % OUTPUT_FILE)

while cont:
	try:
		cont = p.process()
		time.sleep(sleepTime)
	except KeyboardInterrupt:
		cont = False
	#except:
	#       print 'Unhandled exception: ', sys.exc_info()
	#       cont = False

p.printmsg( 'Exiting gracefully!')
p.close()
exit()
