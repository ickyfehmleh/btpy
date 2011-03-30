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
import time

verbose = False
tsize = 0
selectedHashes = []
onlyForThisUser = True
showTotals = True
onlyActive = False
onlyStoppable = False

# setup args
try:
	opts, args = getopt.getopt(argv[1:], 'vats', ['stoppable','hash=','torrent=','for-me','all','everyone','transferring'])
except getopt.GetoptError:
	print 'Usage: %s [file1.torrent ... fileN.torrent]' % argv[0]
	print 'Optional arguments: [--verbose/-v]: show stats'
	print '--hash=<hash>: only show this hash (implies verbose)'
	print '--all/-a: show all downloads'
	print '--stoppable/-s: only show stoppable (1:1-seeded) torrents'
	print '--transferring/-t: show only active downloads'
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
	elif o in ('--transferring', '-t'):
		onlyActive = True
		showTotals = False
	elif o in ('--stoppable','-s'):
		onlyStoppable=True
		showTotals = False

for a in args:
	if os.path.exists( a ) and a.endswith( '.torrent' ):
		info = infoFromTorrent(a)
		if info == '':
			print 'Failed to find anything matching %s' % (a)
		else:
			infHash = hashFromInfo( info )
			selectedHashes.append( infHash )
try:
	doc = minidom.parse( TORRENT_XML )
except IOError,e:
	if e.errno == 2:
		print 'Torrenting not running, try again later'
	else:
		print 'I/O error parsing XML: %s' % e.strerror
	exit()

if len(selectedHashes) > 0:
	verbose = True
	showTotals = False
	onlyForThisUser = True
	#onlyActive = False

totalSpeedUp = 0
totalSpeedDn = 0
totalBytesUp = 0
totalBytesDn = 0
numMatches = 0
torrentStore = initTorrentStore()

if not verbose:
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

		nameUnicode = findNodeName( torrent, 'name' )
		name = nameUnicode.encode('ascii','ignore')
		fileSize = int(findNodeName( torrent, 'filesize' ))
		fsize = human_readable( fileSize )
		tsize += int( fileSize )
		bytesUp = int(findNodeName( torrent, 'totalUploadBytes' ))
		bytesDn = int(findNodeName( torrent, 'totalDownloadBytes' ))
		rawSpeedUp = findNodeName(torrent, 'uploadRate')
		rawSpeedDn = findNodeName(torrent, 'downloadRate')
		speedUp = float(rawSpeedUp)
		speedDn = float(rawSpeedDn)
		progressPercentage = findNodeName(torrent,'progress')
		totalBytesUp += bytesUp
		totalBytesDn += bytesDn
		totalSpeedUp += speedUp
		totalSpeedDn += speedDn
		status = findNodeName( torrent, 'status' )
		eta = findNodeName( torrent, 'eta' )
		isCompleted = False
		ratio = float(-0.00)
		isActive = False
		tfile = Torrent(torrentPath)
		stopRatio = torrentStore.ratioForTorrent( tfile )
		stopRatio = ratioForHash(hash,str(ownerUID))

		if eta == 'complete!':
			isCompleted = True

		if rawSpeedUp.count('-') == 0 and rawSpeedDn.count('-') == 0:
			if speedUp > 0.0 or speedDn > 0.0:
				isActive = True

		if bytesDn > 0:
			ratio = float(bytesUp) / float(bytesDn)

		if onlyActive and not isActive:
			continue

		if onlyStoppable:
			if ratio < 1.0 or not isCompleted:
				continue

		if verbose:
			print ''

		if not onlyForThisUser:
			ownerName = pwd.getpwuid(ownerUID)[0]
			percentageComplete = findNodeName(torrent,'progress')

			if eta != "complete!":
				print '%s: %s [%s, %s complete]' % (ownerName, name, fsize, progressPercentage )
			else:
				print '%s: %s [%s]' % (ownerName, name, fsize)
		else:
			print '%s [%s] (%.2f/%.2f)' % (name, fsize,ratio,stopRatio)

		if verbose:
			numMatches = numMatches + 1
			started = float(findNodeName(torrent,'started'))
			startDate = time.ctime( started )
			if status != "seeding":
				if eta == "complete!":
					print 'Status: %s (%s)' % (status, findNodeName( torrent, 'progress' ))
				else:
					errMsg = findNodeName(torrent,'msg')
					print 'ETA: %s' % eta
					if len(errMsg) > 0:
						print 'ERROR: %s' % errMsg
			print '%s @ %s/s uploaded, %s @ %s/s downloaded' % (human_readable(bytesUp), human_readable(speedUp), human_readable(bytesDn), human_readable(speedDn))

if showTotals:
	print

	if verbose:
		print 'Total of %s being downloaded, %s @ %s/s up, %s @ %s/s dn' % (human_readable(tsize), human_readable(totalBytesUp), human_readable(totalSpeedUp), human_readable(totalBytesDn), human_readable(totalSpeedDn))
	else:
		print 'A total of %s is being downloaded' % human_readable(tsize)
