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
onlyForThisUser = False
showTotals = True

# opts:
# --verbose/-v  ==> verbose = True
# --hash=<hash> ==> selectedHash = hash
# --all/--everyone/-a ==> show torrents for all users
# --for-me ==> only show torrents owned by os.getuid()

# setup args
try:
	opts, args = getopt.getopt(argv[1:], 'va', ['hash=','torrent=','for-me','all','everyone'])
except getopt.GetoptError:
	print 'Usage: %s [file1.torrent ... fileN.torrent]' % argv[0]
	print 'Optional arguments: [--verbose/-v]: show stats'
	print '--hash=<hash>: only show this hash (implies verbose)'
	print '--for-me: only show torrents you\'re downloading'
	print '--all/--everyone/-a: show all torrents'
	print 'If torrents are specified, only those stats will be shown.'
	exit(2)

for o,a in opts:
	if o in("--verbose", "-v"):
		verbose = True
	elif o == '--hash':
		selectedHashes.append(a)
		verbose = True
		showTotals = False
	elif o == '--for-me':
		onlyForThisUser = True
	elif o in ('--everyone','--all','-a'):
		onlyForThisUser = False

for a in args:
	if os.path.exists( a ) and a.endswith( '.torrent' ):
		onlyForThisUser = False
		info = infoFromTorrent(a)
		if info == '':
			print 'Failed to find anything matching %s' % (a)
		else:
			selectedHashes.append( sha( bencode( info  ) ).hexdigest() )

dataStore = initDataStore()
doc = minidom.parse( dataStore.torrentXML() )

if len(selectedHashes) > 0:
	verbose = True
	showTotals = False

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
		ratio = float(0.0)

		if bytesDn > 0:
			ratio = float(bytesUp) / float(bytesDn)
		else:
			ratio = -0.00


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
			print 'Uploaded: %s, downloaded: %s [Ratio: %.2f, stop @%.2f]' % (human_readable(bytesUp), human_readable(bytesDn), ratio,ratioForHash(hash,str(ownerUID),autostopDir=dataStore.autostopDir()))
			print ''

if verbose:
	print '%s @ %s/s up, %s @ %s/s dn' % (human_readable(totalBytesUp), human_readable(totalSpeedUp), human_readable(totalBytesDn), human_readable(totalSpeedDn))

if showTotals:
	print
	print 'A total of %s is being downloaded' % human_readable(tsize)
