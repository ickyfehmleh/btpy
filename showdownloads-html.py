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

tsize = 0

dataStore = initDataStore()
doc = minidom.parse( dataStore.torrentXML() )

print "<html>"
print "<head>"
print "  <title>Downloads</title>"
print "</head>"
# TODO: separate out into its own .css
print "<link rel=\"stylesheet\" href=\"/tinfo.css\" type=\"text/css\">"

# do not cache this page!
print "<META HTTP-EQUIV=\"Pragma\" CONTENT=\"no-cache\">"
print "<META HTTP-EQUIV=\"Expires\" CONTENT=\"-1\">"
print "<body>"
print ""

# last updated time
print "<span class=\"timestamp\"><b>Last Generated</b>: %s</span><br/><br/>" % time.ctime( time.time() )

print ""
print "<table border='1' cellspacing='0' cellpadding='2' width='100%' class=\"mainTable\">"
print "<tr class=\"tableHeader\">"
print "	<th width='75%' align='center'>Name [Size]</font></th>"
print "	<th width='10%' align='center'>Up @ Rate</font></th>"
print "	<th width='10%' align='center'>Dn @ Rate</font></th>"
print " <th width='5%' align='center'>Ratio</font></th>"
print "</tr>"
print ""

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
			print "<tr class=\"seededStoppable\">"
			ratioOK = True
		else:
			print "<tr>"

		print "<td align=\'left\'>%s <span class=\"sizeSlug\">[%s]</span>" % (name, human_readable(fsize))

		if status != "seeding":
			progressPercentage = findNodeName(torrent,'progress')
			msg = findNodeName(torrent,'msg')

			if eta == "complete!":
				print "<br/><span class=\"dlStatus\"><b>Status</b>: %s (%s)</span>" % (status, progressPercentage)
			else:
				print "<br/><span class=\"dlEta\"><b>ETA</b>: %s [%s complete]</span>" % (eta,progressPercentage)
			if msg is not None and len(msg) > 0:
				print " <span class=\"errMsg\">%s</span>" % msg
		print "</td>"

		print "<td nowrap=\"nowrap\" align='center'>%s @ %s<br/>to %d peers</td>" % (human_readable(hstBytesUp), boldTransferRate(rateUp), numPeers)
		print "<td nowrap=\"nowrap\" align='center'>%s @ %s<br/>from %d seeds</td>" % (human_readable(hstBytesDn),boldTransferRate(rateDn), numSeeds)

		ownerUID = findNodeName(torrent,'owner')
		hash = findNodeName(torrent,'hash')
		stopRatio = ratioForHash(hash,ownerUID,autostopDir=dataStore.autostopDir())

		print "<td nowrap=\"nowrap\" align='center'>"

		if hstBytesDn > 0:
			print "%.2f" % (float(hstBytesUp) / float(hstBytesDn))
		else:
			print "&nbsp;"

		if stopRatio > 0.0:
			print '<br/>(%.2f)' % stopRatio

		print "</td>"
		print "</tr>"
# totals
print "<tr class=\"tableFooter\">"
print " <td nowrap=\"nowrap\" align='right'>= %s</td>" % human_readable(totalIncoming)
print " <td nowrap=\"nowrap\" align='right'>= %s @ %s/s</td>" % (human_readable(totalBytesUp),human_readable(totalRateUp))
print " <td nowrap=\"nowrap\" align='right'>= %s @ %s/s</td>" % (human_readable(totalBytesDn),human_readable(totalRateDn))
print " <td nowrap=\"nowrap\" align='right'>&nbsp;</td>"
print "</tr>"

# /totals
print "</table>"
print "</body>"
print "</html>"
