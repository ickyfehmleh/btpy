#!/usr/bin/python
#
# cycle through INCOMING and wipe any torrent that has been stopped and is 
# at least 14 days old
#

from sys import exit
from common import *
import os

def deleteDownloadedTorrent(dir):
	if os.path.isfile(dir):
		os.unlink(dir)
	else:
		for root, dirs, files in os.walk(dir):
			for currentDir in dirs:
				deleteDownloadedTorrent(os.path.join( dir, currentDir ) )
			for currentFile in files:
				fullFilePath = os.path.join( dir, currentFile )
				os.remove( fullFilePath )
		os.rmdir( dir )

# stat()s a dir/file, checks to see if its older than n number of days
def isFileOld(fn, daysOld=15):
	stats = os.stat(fn)
	lastmod = datetime.date.fromtimestamp(stats[8])
	today = datetime.date.today()
	oldTime = today + datetime.timedelta(days=-1 * daysOld)
	return oldTime > lastmod

def isTorrentProcessing(hash):
	return isTorrentHashActive(hash)

def processDirectory(root):
	inactiveTorrents = []

	for d in os.listdir( root ):
		print '*** %s [%s]' % (d, os.path.join( root, d) )
		if not d.startswith( '.' ) and not d.startswith('autostop') and not d.endswith( '.torrent' ):
			if isFileOld( os.path.join( root, d ) ):
				if not isTorrentProcessing(d):
					tname = os.path.join( root, d )
					if not tname in inactiveTorrents:
						inactiveTorrents.append( tname )
	return inactiveTorrents
####

inactiveTorrents = processDirectory( INCOMING_TORRENT_DIR )

if len(inactiveTorrents) > 0:
	for rmfile in inactiveTorrents:
		#deleteDownloadedTorrent( rmfile )
		print 'Removed: ', rmfile
exit()
