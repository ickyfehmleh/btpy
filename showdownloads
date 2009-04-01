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
import pwd
import getopt

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

def ratioForHash(hash,uid):
	ratio = float(0.0)

	stopFile = os.path.join(AUTOSTOPD_DIR,hash+'.xml')
		
	if os.path.exists(stopFile):
		ratio = ratioFromAutostopFile(stopFile)
	else:
		stopFile = os.path.join(AUTOSTOPD_DIR,uid+'.xml')
		if os.path.exists(stopFile):
			ratio = ratioFromAutostopFile(stopFile)
	return ratio

def findNodeName(parentNode, name):
	for childNode in parentNode.childNodes:
		if name == childNode.nodeName:
			content = []
			for textNode in childNode.childNodes:
				content.append( textNode.nodeValue )
			return string.join( content )
	return ''

verbose = False
tsize = 0
selectedHashes = []
onlyForThisUser = True
showTotals = True

# opts:
# --verbose/-v  ==> verbose = True
# --hash=<hash> ==> selectedHash = hash
# --everyone/--all ==> show all downloads

# setup args
try:
	opts, args = getopt.getopt(argv[1:], 'va', ['hash=','torrent=','for-me','all','everyone'])
except getopt.GetoptError:
	print 'Usage: %s [file1.torrent ... fileN.torrent]' % argv[0]
	print 'Optional arguments: [--verbose/-v]: show stats'
	print '--hash=<hash>: only show this hash (implies verbose)'
	print '--all/-a: show all downloads'
	print 'If torrents are specified, only those stats will be shown.'
	exit(2)

for o,a in opts:
	if o in("--verbose", "-v"):
		verbose = True
	elif o == '--hash':
		selectedHashes.append(a)
		verbose = True
		showTotals = False
	elif o in ('--everyone', '--all', '-a'):
		onlyForThisUser = False

for a in args:
	if os.path.exists( a ) and a.endswith( '.torrent' ):
		info = infoFromTorrent(a)
		if info == '':
			print 'Failed to find anything matching %s' % (a)
		else:
			selectedHashes.append( sha( bencode( info  ) ).hexdigest() )

doc = minidom.parse( TORRENT_XML )

if len(selectedHashes) > 0:
	verbose = True
	showTotals = False
	onlyForThisUser = False

totalSpeedUp = 0
totalSpeedDn = 0
totalBytesUp = 0
totalBytesDn = 0

print ''

for torrent in doc.documentElement.childNodes:
	if torrent.nodeName == 'torrent':
		torrentPath = findNodeName( torrent, 'fullpath' )

		hash = findNodeName( torrent, 'hash' )

		if len(selectedHashes) > 0 and hash not in(selectedHashes):
			continue

		ownerUID = int(findNodeName(torrent,'owner'))

		if onlyForThisUser and ownerUID != os.getuid():
			continue

		name = findNodeName( torrent, 'name' ).encode('utf-8')
		fileSize = int(findNodeName( torrent, 'filesize' ))
		fsize = human_readable( fileSize )
		tsize += int( fileSize )
		bytesUp = int(findNodeName( torrent, 'totalUploadBytes' ))
		bytesDn = int(findNodeName( torrent, 'totalDownloadBytes' ))
		speedUp = float(findNodeName(torrent, 'uploadRate'))
		speedDn = float(findNodeName(torrent, 'downloadRate'))
		progressPercentage = findNodeName(torrent,'progress')
		totalBytesUp += bytesUp
		totalBytesDn += bytesDn
		totalSpeedUp += speedUp
		totalSpeedDn += speedDn
		status = findNodeName( torrent, 'status' )
		eta = findNodeName( torrent, 'eta' )
		ratio = float(-0.00)

		if bytesDn > 0:
			ratio = float(bytesUp) / float(bytesDn)

		if not onlyForThisUser:
			ownerName = pwd.getpwuid(ownerUID)[0]
			percentageComplete = findNodeName(torrent,'progress')

			if eta != "complete!":
				print '%s: %s [%s, %s complete]' % (ownerName, name, fsize, progressPercentage )
			else:
				print '%s: %s [%s]' % (ownerName, name, fsize)
		else:
			print '%s [%s] (%.2f)' % (name, fsize,ratio)

		if verbose:
			if status != "seeding":
				if eta == "complete!":
					print 'Status: %s (%s)' % (status, findNodeName( torrent, 'progress' ))
				else:
					errMsg = findNodeName(torrent,'msg')
					print 'ETA: %s' % eta
					if len(errMsg) > 0:
						print 'ERROR: %s' % errMsg
			print 'Uploaded: %s, downloaded: %s [Ratio: %.2f, stop @%.2f]' % (human_readable(bytesUp), human_readable(bytesDn), ratio,ratioForHash(hash,str(ownerUID)))
			print ''

if verbose:
	print '%s @ %s/s up, %s @ %s/s dn' % (human_readable(totalBytesUp), human_readable(totalSpeedUp), human_readable(totalBytesDn), human_readable(totalSpeedDn))

if showTotals:
	print
	print 'A total of %s is being downloaded' % human_readable(tsize)
