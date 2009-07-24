#!/usr/local/bin/python
########################################################################
# btlaunchmany script to emit XML
# and log statistics
########################################################################

from BitTornado import PSYCO
if PSYCO.psyco:
	try:
		import psyco
		assert psyco.__version__ >= 0x010100f0
		psyco.full()
	except:
		pass

from BitTornado.launchmanycore import LaunchMany
from BitTornado.download_bt1 import defaults, get_usage
from BitTornado.parseargs import parseargs
from threading import Event
from sys import argv, exit
import sys, os
from BitTornado import version, report_email
from BitTornado.ConfigDir import ConfigDir
import os.path
import shelve
import time
import shutil
from stat import *
from common import *
from BitTornado.bencode import bdecode
from pysqlite2 import dbapi2 as sqlite

assert sys.version >= '2', "Install Python 2.0 or greater"
try:
	True
except:
	True = 1
	False = 0

def nameFromTorrent(fn):
	try:
		f = open( fn, 'rb' )
		metaInfo = bdecode( f.read())
		f.close()
		info = metaInfo['info']
		return info['name']
	except:
		return ''

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


Exceptions = []

class XMLDisplayer:
	outputXMLFile = TORRENT_XML
	dbmstats = {}
	livestats = {}
	owners = {}
	torrentNames = {}
	torrentDates = {}
	outputFile = None

	def __init__(self,basedir):
		dataDir = os.path.join(basedir,'.data')
		self.statsRecorder = SqliteStats(MASTER_HASH_LIST)
		self._log=MessageLogger('launchmany')
		self._log.printmsg('Starting...')

	def mergedStats(self,key):
		liveValue = self.livestats.get(key,'0:0')
		dbmValue = self.dbmstats.get(key,'0:0')
		(liveUp,liveDn) = liveValue.split(':')
		(dbmUp,dbmDn) = dbmValue.split(':')
		totUp = int(liveUp) + int(dbmUp)
		totDn = int(liveDn) + int(dbmDn)
		return (totUp,totDn)

	def cleanup(self):
		self.saveStats()
		os.unlink(self.outputXMLFile)
		self.statsRecorder.close()
		self._log.printmsg('STOPPING...')
		self._log.close()

	def saveStats(self):
		for hash in self.livestats:
			(up,dn) = self.mergedStats(hash)
			uid = self.owners[hash]
			self.saveStatsForHashAndUser(hash,uid,uploaded=up,downloaded=dn)

	def display(self, data):
		try:
			outputFile = SafeWriteFile(self.outputXMLFile,0640)
			outputFile.write( '<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n' )
			outputFile.write( '<torrents>\n' )
			totalBytesUp = 0
			totalBytesDn = 0
			totalSpeedUp = 0
			totalSpeedDn = 0
			totalIncoming = 0

			if data:
				for x in data:
					( fullPath, status, progress, peers, seeds, seedsmsg, dist,
					  uprate, dnrate, liveUp, liveDn, size, t, msg ) = x

					# find stats in our dbm
					hash = os.path.basename(fullPath).split('.')[0]
					self.livestats[hash] = '%s:%s' % (liveUp,liveDn)

					(upamt,dnamt) = self.mergedStats(hash)

					t = hours(t)
					if not t:
						t = status

					outputFile.write( '\t<torrent>\n' )
					self.printXML(outputFile, 'name', self.torrentNames.get(hash, hash))
					self.printXML(outputFile, 'hash', hash)
					self.printXML(outputFile, 'fullpath', fullPath)
					self.printXML(outputFile, 'owner', self.owners.get(hash,'0'))
					self.printXML(outputFile, 'started', self.torrentDates.get(hash,'0') )
					self.printXML(outputFile,'status',status)
					self.printXML(outputFile,'progress', progress)
					self.printXML(outputFile,'peers', peers)
					self.printXML(outputFile,'seeds',seeds)
					self.printXML(outputFile,'seedmsg', seedsmsg)
					self.printXML(outputFile,'distcopies', dist)
					self.printXML(outputFile,'uploadRate', uprate)
					self.printXML(outputFile,'downloadRate', dnrate)

					# store session (livestats[]) up/dn bytes
					self.printXML(outputFile, 'sessionUploadBytes', liveUp)
					self.printXML(outputFile, 'sessionDownloadBytes', liveDn)

					# totalUploadBytes, totalDnBytes
					self.printXML(outputFile,'totalUploadBytes', upamt)
					self.printXML(outputFile,'totalDownloadBytes', dnamt)
					self.printXML(outputFile,'filesize', size)
					self.printXML(outputFile,'eta', t)
					self.printXML(outputFile,'msg', msg)
					outputFile.write( '\t</torrent>\n' )

			outputFile.write( '</torrents>\n' )
			outputFile.close()
		except:
			self.message( 'Failed to write output XML!')
			#self.message( sys.exc_info[0] )

		# save our stats every go-around
		self.saveStats()

		# tell launchmany not to stop
		return False

	def saveStatsForHashAndUser(self,hash,uid,uploaded=0,downloaded=0):
		self.statsRecorder.saveStatsForHashAndUser(hash,uid,uploaded,downloaded)

	def getStoredStatsForHashAndUser(self,hash,uid):
		return self.statsRecorder.getStoredStatsForHashAndUser(hash,uid)

	def addTorrent(self,s):
		(msg,path) = s.replace('"','').split( ' ')
		(hash,ext) = os.path.basename(path).split('.')
		fileStat = os.stat(path)
		ownerUID = fileStat.st_uid
		self.owners[hash] = str(ownerUID)
		name = nameFromTorrent(path)
		if name:
			self.torrentNames[hash] = name
		else:
			name = 'Unavailable'
		# get date added
		self.torrentDates[hash] = fileStat.st_ctime

		storedUp,storedDn = self.getStoredStatsForHashAndUser(hash, ownerUID)
		self.dbmstats[hash] = '%d:%d' % (storedUp,storedDn)
		self.printlog( '%d added torrent [%s] hash=%s' % (ownerUID, name, hash) )

	def dropTorrent(self,s):
		(msg,path) = s.replace('"','').split( ' ')
		(hash,ext) = os.path.basename(path).split('.')
		uid = self.owners.get(hash,'0')
		## save our statistics
		(totUp,totDn) = self.mergedStats(hash)
		self.saveStatsForHashAndUser(hash, uid, uploaded=totUp, downloaded=totDn)
		## wipe all of our lookups
		torrentName = self.torrentNames.get(hash,'UNKNOWN')
		del self.dbmstats[hash]
		del self.livestats[hash]
		del self.owners[hash]
		del self.torrentNames[hash]
		del self.torrentDates[hash]
		self.printlog( 'Stopped torrent \'%s\' [%s]' % (torrentName,hash))
			
	def message(self, s):
		if s.startswith( "added" ):
			self.addTorrent(s)
		elif s.startswith( "dropped" ):
			self.dropTorrent(s)
		else:
			self.printlog( s )

	def printXML(self, fh, tag, value):
		if tag == 'name':
			fh.write( '\t\t<%s><![CDATA[%s]]></%s>' % (tag, value, tag) )
		else:
			fh.write( '\t\t<%s>%s</%s>' % (tag, value, tag) )
		fh.write( '\n' )

	def exception(self, s):
		Exceptions.append(s)
		self.message('EXCEPTION CAUGHT: %s' % s)

	def printlog(self,msg):
		self._log.printmsg(msg)

if __name__ == '__main__':
	if argv[1:] == ['--version']:
		print version
		exit(0)
	defaults.extend( [
		( 'parse_dir_interval', 20,
		  "how often to rescan the torrent directory, in seconds" ),
		( 'saveas_style', 3,
		  "How to name torrent downloads (1 = rename to torrent name, " +
		  "2 = save under name in torrent, 3 = save in directory under torrent name)" ),
		( 'display_path', 1,
		  "whether to display the full path or the torrent contents for each torrent" ),
	] )
	try:
		configdir = ConfigDir('launchmany')
		defaultsToIgnore = ['responsefile', 'url', 'priority']
		configdir.setDefaults(defaults,defaultsToIgnore)
		configdefaults = configdir.loadConfig()
		defaults.append(('save_options',0,
		 "whether to save the current options as the new default configuration " +
		 "(only for btlaunchmany.py)"))
		if len(argv) < 2:
			print "Usage: btlaunchmany.py <directory> <global options>\n"
			print "<directory> - directory to look for .torrent files (semi-recursive)"
			print get_usage(defaults, 80, configdefaults)
			exit(1)
		config, args = parseargs(argv[1:], defaults, 1, 1, configdefaults)
		if config['save_options']:
			configdir.saveConfig(config)
		configdir.deleteOldCacheData(config['expire_cache_data'])
		if not os.path.isdir(args[0]):
			raise ValueError("Warning: "+args[0]+" is not a directory")
		config['torrent_dir'] = args[0]
	except ValueError, e:
		print 'error: ' + str(e) + '\nrun with no args for parameter explanations'
		exit(1)

	# properly instantiate XMLDisplayer, pass it off as a variable
	xmlDisplayer = XMLDisplayer( config['torrent_dir']  )
	try:
		LaunchMany(config, xmlDisplayer)
	finally:
		xmlDisplayer.cleanup()
