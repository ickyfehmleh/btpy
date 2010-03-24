#
# common methods
# 
import os
import time

from sys import *
from os.path import *
import hashlib
from BitTornado.bencode import *
from shutil import *
import re
import datetime
from xml.dom import minidom, Node
import string
from pysqlite2 import dbapi2 as sqlite
import tempfile
import shutil

## constants
#INCOMING_TORRENT_DIR = '/share/incoming'
#COMPLETED_TORRENT_DIR = '/share/torrents'
#PERCENT_KEEP_FREE = .12

PERCENT_KEEP_FREE = .30
INCOMING_TORRENT_DIR = '/share/test/monitored'
COMPLETED_TORRENT_DIR = '/share/test/monitored.done'

DATA_DIR=os.path.join(INCOMING_TORRENT_DIR, '.data')
COMMAND_DIR='/share/bin'
TEMPLATE_DIR=os.path.join( DATA_DIR, 'templates' )
AUTOSTOPD_DIR=os.path.join( DATA_DIR, 'autostopd')
TORRENT_XML=os.path.join(DATA_DIR, 'torrents.xml')
MASTER_HASH_LIST = os.path.join( DATA_DIR,'stats.db' )
ALLOWED_TRACKER_LIST = os.path.join( DATA_DIR, 'allowed_trackers.dat')
USER_DL_DIR=os.path.join( os.path.expanduser( '~/tshare' ) )
EXPIRED_TORRENT_DIR='/share/expired'
MAX_SLEEP_TIME = 20
FILE_DELIMITER = ':'
ACTIVE_USER_TORRENTS = os.path.expanduser( '~/.torrents.active' )
## /constants

# ======================================================================
# return a torrent store
def initTorrentStore():
	ts = TorrentStore( INCOMING_TORRENT_DIR )
	return ts

# ======================================================================
# write a path to ~/torrents.list
# handy list of torrents one has downloaded so they can potentially script
# the scp'ing of them to their local machines
def recordLocalTorrent(path):
	filename = os.path.join( os.getenv( "HOME" ), 'torrents.list' )
	fn = open( filename, mode='a' )
	fn.write( path )
	fn.write( '\n' )
	fn.close()

# ======================================================================
class SafeWriteFile(object):
	def __init__(self,fileName,perms=0640):
		self._fileName=str(fileName)
		self._tempFile=str(tempfile.mktemp())
		self._fileHandle = open( self._tempFile, 'w' )
		self._permissions=perms

	def write(self,s):
		self._fileHandle.write( s )
		self._fileHandle.flush()

	def writeline(self,s):
		self.write( s+'\n' )

	def println(self,s):
		self.writeline(s)

	def close(self):
		self._fileHandle.close()
		shutil.move(self._tempFile, self._fileName)
		os.chmod( self._fileName, self._permissions )

# ======================================================================
class MessageLogger(object):
	def __init__(self,appName):
		self._appName=appName
		self._logfile=open( os.path.join(DATA_DIR, appName + '.log' ), 'a' )

	def printmsg(self,msg):
		t = time.strftime( '%Y-%m-%d @ %I:%M:%S %P' )
		print '%s [%s]: %s' % (self._appName,t, msg)
		self._logfile.write( '[%s]: %s\n' % (t,msg) )
		self._logfile.flush()

	def close(self):
		self._logfile.close()

# ======================================================================
class SqliteStats(object):
	def __init__(self,dbFile):
		self._dbFile = dbFile + '.sqlite'
		self.statsDb = sqlite.connect(  self._dbFile )

	def isHashAlreadyDownloaded(self,hash):
		rv = False
		c = self.statsDb.cursor()
		c.execute( 'SELECT hash FROM user_data WHERE hash=?', (hash,))
		row = c.fetchone()
		if row:
			rv = True
		c.close()
		return rv

	def close(self):
		self.statsDb.close()

	def saveStatsForHashAndUser(self,hash,uid,uploaded=0,downloaded=0):
		c = self.statsDb.cursor()
		## will work as long as hash+uid == pk
		c.execute( 'REPLACE INTO user_data (hash,uid,uploaded,downloaded) VALUES(?,?,?,?)',
			(hash,str(uid),uploaded,downloaded))
		c.close()
		self.statsDb.commit()

	def getStoredStatsForHashAndUser(self,hash,uid):
		up = 0
		dn = 0

		c = self.statsDb.cursor()
		c.execute( 'SELECT uploaded,downloaded FROM user_data WHERE uid=? AND hash=?', (uid,hash))
		row = c.fetchone()

		if row:
			up = long(row[0])
			dn = long(row[1])
		c.close()
		return up,dn

# ======================================================================
def hours(n):
	if n == 0:
		return 'complete!'
	try:
		n = int(n)
		assert n >= 0 and n < 5184000  # 60 days
	except:
		return 'unknown'
	m, s = divmod(n, 60)
	h, m = divmod(m, 60)
	if h > 0:
		return '%d hour %02d min %02d sec' % (h, m, s)
	else:
		return '%d min %02d sec' % (m, s)

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

# ======================================================================
# ratio for a given hash
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

# ======================================================================
# write an array to a file
def writeArrayToFile(array,fileName,newline=True):
	f = SafeWriteFile( fileName, 0600 )

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
		stats = SqliteStats(MASTER_HASH_LIST)
		found = stats.isHashAlreadyDownloaded(str(h))
		stats.close()
	except:
		print 'EXception caught!: %s' % str(exc_info())
		found = True

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
	## FIXME find the right method to call here
	info_hash = hashlib.sha1( bencode( info  ) ).hexdigest()
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
def getAllFilesFromTorrent(fn):
	info = infoFromTorrent(fn)
	paths = []

	if info != '':
		for file in info['files']:
			path = ''
			for item in file['path']:
				if (path != ''):
					path = path + "/"
				path = path + item
			paths.append( path )
	return paths

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

def hashFromInfo(info):
	return hashlib.sha1( bencode( info ) ).hexdigest()

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
					info_hash = hashFromInfo(info) #sha( bencode( info ) ).hexdigest()

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
