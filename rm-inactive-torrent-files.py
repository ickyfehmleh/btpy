#!/usr/bin/python
#
# cycle through COMPLETED_TORRENT_DIR and rm any .torrent file that's 
# inactive AND doesnt have a directory in INCOMING_TORRENT_DIR
#
# this will not break 'stop' since the torrent is not being downloaded nor
# is it waiting for a 'stop -i' run
#

from sys import exit
from common import *
import os

def isTorrentProcessing(hash):
	if isTorrentHashActive(hash):
		return True
	else:
	        fn = os.path.join( INCOMING_TORRENT_DIR, hash )
        	return os.path.exists( fn )

def processDirectory(dir):
	inactiveTorrents = []

	for root, dirs, files in os.walk( dir ):
		for d in dirs:
			pd = processDirectory( os.path.join( root, d ) )
			## FIXME find a cleaner way of doing this
			for pdf in pd:
				inactiveTorrents.append( pdf )
			
		for f in files:
			if f.endswith('.torrent'):
				tname = os.path.join( root, f )
				info = infoFromTorrent(tname)

				if info == '':
					print '### Failed to get info from torrent %s' % tname
					continue

				hash = sha( bencode( info ) ).hexdigest()

				if not isTorrentProcessing(hash):
					if not tname in inactiveTorrents:
						inactiveTorrents.append( tname )
	return inactiveTorrents
####

inactiveTorrents = processDirectory( COMPLETED_TORRENT_DIR )

if len(inactiveTorrents) > 0:
	for rmfile in inactiveTorrents:
		os.unlink( rmfile )
		print 'Removed: ', rmfile
exit()
