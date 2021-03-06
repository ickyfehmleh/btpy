#
# common methods
# 
import os
import time

from sys import *
from os.path import *
from sha import *
from BitTornado.bencode import *
from shutil import *
import re
import datetime
from xml.dom import minidom, Node
import string
import shelve

## constants
INCOMING_TORRENT_DIR = '/share/incoming'
COMPLETED_TORRENT_DIR = '/share/torrents'
PERCENT_KEEP_FREE = .12

#PERCENT_KEEP_FREE = .30
#INCOMING_TORRENT_DIR = '/share/test/monitored'
#COMPLETED_TORRENT_DIR = '/share/test/monitored.done'

DATA_DIR=os.path.join(INCOMING_TORRENT_DIR, '.data')
AUTOSTOPD_DIR=os.path.join( DATA_DIR, 'autostopd')
TORRENT_XML=os.path.join(DATA_DIR, 'torrents.xml')
MASTER_HASH_LIST = os.path.join( DATA_DIR,'stats.db' )
ALLOWED_TRACKER_LIST = os.path.join( DATA_DIR, 'allowed_trackers.dat')
USER_DL_DIR=os.path.join( COMPLETED_TORRENT_DIR, str(os.getuid()) )
EXPIRED_TORRENT_DIR='/share/expired'
MAX_SLEEP_TIME = 20
FILE_DELIMITER = ':'
ACTIVE_USER_TORRENTS = os.path.expanduser( '~/.torrents.active' )
## /constants

# ======================================================================
# write an array to a file
def writeArrayToFile(array,fileName,newline=True):
	f = open( fileName, 'w' )

	for line in array:
		f.write( line )

		if newline:
			f.write( '\n' )
	f.close()

# cache a file
def cacheFileContents(fileName):
	lines = []

	try:
		fn = open( fileName, 'r' )

		for line in fn.readlines():
			line = line[:-1]
			lines.append( line )
		fn.close()
		return lines
	except IOError:
		return []

# locate a named node, return its value
def findNodeName(parentNode, name):
	for childNode in parentNode.childNodes:
		if name == childNode.nodeName:
			content = []
			for textNode in childNode.childNodes:
				content.append( textNode.nodeValue )
			return string.join( content )
	return ''


# find ratio for an autostop file
def ratioFromAutostopFile(fn):
	asf = minidom.parse( fn )
	req = asf.documentElement.childNodes[1]
	ratio = findNodeName( req, 'ratio' )
	if ratio:
		return float(ratio)
	return 0.00

def isTrackerAllowed(torrentTracker):
	rv = False

	f = open( ALLOWED_TRACKER_LIST, 'r' )
	for tracker in f.readlines():
		if tracker.startswith( '#'):
			continue

		tracker = tracker[:-1]
		if torrentTracker.rfind( tracker) > -1:
			rv = True
			break
	f.close();

	return rv

# ======================================================================
def isFileOwnerCurrentUser(fn):
	return os.stat(fn).st_uid == os.getuid()

def isTorrentHashActive(hash):
	fn = os.path.join( INCOMING_TORRENT_DIR, hash + '.torrent' )
	return os.path.exists( fn )

# ======================================================================
def printSleepingStatus(timeToSleep):
	i=0

	while i != timeToSleep:
		if i>1:
			stdout.write( "\b" )
		if i>=10:
			stdout.write( "\b" )

		stdout.write( "%d" % i )
		stdout.flush()
		i += 1
		time.sleep( 1 );
	stdout.write( "\n" );
	stdout.flush();

# ======================================================================
# check for a hash in the master hashes file to see if a file has already
# been downloaded
def checkDownloadStatus(h):
	found = False

	try:	
		# open master hashes
		hashes =  shelve.open( MASTER_HASH_LIST, flag='r' )
		found = hashes.has_key(h)
		hashes.close()
	except:
		print 'EXception caught!: %s' % exc_info()
		found = False

	return found

# ======================================================================
def recordActiveTorrent(torrentPath, name=None, hash=None):
	torrentPath = os.path.abspath( torrentPath )

	logstr = "%s%s%s%s%s%s%s" % (torrentPath, FILE_DELIMITER,
			hash, FILE_DELIMITER,
			name, FILE_DELIMITER,
			str(time.time()))

	f = open( ACTIVE_USER_TORRENTS, mode='a')
	f.write( logstr )
	f.write( '\n' )
	f.close()

def removeActiveTorrent(hash):
	if not os.path.exists( ACTIVE_USER_TORRENTS ):
		f = open( ACTIVE_USER_TORRENTS, mode='w' )
		f.close()
		os.chmod( ACTIVE_USER_TORRENTS, 0600 )
		return

	f = open( ACTIVE_USER_TORRENTS, mode='r' )
	output = []

	for line in f.readlines():
		currentHash = line.split(FILE_DELIMITER)[1]
		
		if currentHash != hash:
			output.append( line )

	f.close()

	# reopen and rewrite contents
	f = open( ACTIVE_USER_TORRENTS, mode='w')
	
	for line in output:
		f.write( line )
	f.close()
	os.chmod( ACTIVE_USER_TORRENTS, 0600 )

#########################################################################
# record a hash in our master hashlist file
def recordDownloadedTorrent(info):
	info_hash = sha( bencode( info  ) ).hexdigest()
	removeActiveTorrent(info_hash)

# ======================================================================
# replace crazy chars with _ to make scp life easier and scriptable
def escapeFilename(s):
	return re.sub("[^A-Za-z0-9\.]", "_", s)

# ======================================================================
## get full path for a file in a torrent
def fullFilePathFromTorrent(file_info):
	torrentFile = ''
	for item in file_info['path']:
		if torrentFile != '':
			torrentFile += "/"
		torrentFile += item
	return torrentFile

# ======================================================================
def nameFromTorrent(fn):
	info = infoFromTorrent(fn)

	if info == '':
		return None
	else:
		return info['name']

## get metainfo from a given torrent
def infoFromTorrent(fn):
	try:
		metainfo_file = open(fn, 'rb')
		metainfo = bdecode(metainfo_file.read())
		metainfo_file.close()
		info = metainfo['info']
		return info
	except:
		return ''

# ======================================================================
## find a file in a torrent
def findTorrent(s):
	try:
		f = open(s, 'rb')
		f.close()
		return s
	except:
		# cant open that file, assume its not there
		for root, dir, files in os.walk( INCOMING_TORRENT_DIR ):
			for file in files:
				if file.find('.torrent', 0 ) != -1:
					fn = os.path.join(INCOMING_TORRENT_DIR, file)
					info = infoFromTorrent(fn)
					info_hash = sha( bencode( info ) ).hexdigest()

					if info_hash == s:
						return fn

					if info['name'] == s:
						print "Located file %s in torrent %s" % (s, info_hash)
						return fn
					else:
						if info.has_key('files'):
							for torrentFileInfo in info['files']:
								torrentFile = fullFilePathFromTorrent( torrentFileInfo )
								if torrentFile == s:
									print "Located file %s in torrent %s" % (s, info_hash)
									return fn
	return ''
