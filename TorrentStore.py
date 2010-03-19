#
# torrent store and torrent object
#
import os
import os.path
import shutil
import hashlib
from BitTornado.bencode import *

class TorrentExistsException( Exception ):
	pass

class TorrentAlreadyDownloadedException( Exception ):
	pass

class MismatchedOwnersException( Exception ):
	pass

class Torrent:
	def __init__(self,fileName):
		self.fileName = os.path.abspath(fileName)

		if self.exists():
			f = open(self.fileName, 'rb')
			self.metainfo = bdecode(f.read())
			f.close()
			self.info = self.metainfo['info']

	def announceURL(self):
		return self.metainfo['announce']

	def filesInTorrent(self):
		paths = []

		if self.info != '':
			for file in self.info['files']:
				path = ''
				for item in file['path']:
					if (path != ''):
						path = path + "/"
					path = path + item
				paths.append( path )
		return paths

	def hash(self):
		return hashlib.sha1(bencode(self.info)).hexdigest()

	def exists(self):
		return os.path.exists( self.fileName )

	def archiveSize(self):
		pass

	def path(self):
		return self.fileName

	def torrentName(self):
		return self.info['name']

	def isFileOwnerCurrentUser(self):
		return os.stat(self.fileName).st_uid == os.getuid()

	def isActive(self):
		hash = self.infoHash()
		fn = os.path.join( INCOMING_TORRENT_DIR, hash + '.torrent' )
		return os.path.exists( fn )


class TorrentStore:
	__slots__ = ('incomingTorrentDir','fileDelimiter')

	def __init__(self,itd):
		self.incomingTorrentDir=itd
		self.fileDelimiter=':'
		self._initDataPath()

	def _initDataPath(self):
		if not os.path.exists( self.dataDir() ):
			os.mkdir( self.dataDir() )

		if not self._isDataPathPresent('allowed_trackers.dat'):
			print 'Creating allowed_trackers.dat!'
			self._createDataFile( 'allowed_trackers.dat' )

		if not self._isDataPathPresent( 'autostopd' ):
			print 'Making autostopd dir!'
			self._createDataDirectory('autostopd')
	
	def _isDataPathPresent(self,fn):
		return os.path.exists( os.path.join( self.dataDir(), fn ) )

	def _createDataFile(self,fileName):
		f = open( os.path.join( self.dataDir(), fileName ), 'w' )
		f.close()
		
	def _createDataDirectory(self,dirName):
		os.mkdir( os.path.join( self.dataDir(), dirName ) )

	def torrentXML(self):
		return os.path.join( self.dataDir(), 'torrents.xml' )

	def allowedTrackersList(self):
		return os.path.join( self.dataDir(), 'allowed_trackers.dat')

	def autostopDir(self):
		return os.path.join( self.dataDir(), 'autostop' )

	def dataDir(self):
		return os.path.join( self.incomingTorrentDir, '.data' )

	def masterHashList(self):
		return os.path.join( self.dataDir(),'hashes.dat' )

	def isTorrentActive(self,t):
		return self.isTorrentHashActive(t.hash())

	def isTorrentHashActive(self,hash):
		fn = os.path.join( self.incomingTorrentDir, hash + '.torrent' )
		return os.path.exists( fn )

	def checkDownloadStatus(self,hash):
		found = False
		db = shelve.open( self.masterHashList(), flag='r' )
		found =  db.has_key(hash)
		db.close()
		return found
	
	def isTrackerAllowed(self,torrentTracker):
		rv = False
		f = open( self.allowedTrackerList(), 'r' )
		for tracker in f.readlines():
			if tracker.startswith( '#'):
				continue
			tracker = tracker[:-1]
			if torrentTracker.rfind( tracker) > -1:
				rv = True
				break
		f.close();	
		return rv

	def isTorrentDataPresent(self,t):
		return self.isTorrentDataPresentForHash(t.hash())

	def isTorrentDataPresentForHash(self,hash):
		return os.path.exists( os.path.join( self.incomingTorrentDir, hash ) )

	def isTorrentPaused(self,t):
		return self.isTorrentHashPaused(t.hash())

	def isTorrentHashPaused(self,hash):
		if self.isTorrentHashActive(hash):
			return self.isTorrentDataPresent(hash)
		return False

	def stopTorrent(self,t):
		self.stopTorrentHash(t.hash())

	def pauseTorrent(self,t):
		self.stopTorrent(t)

	def stopTorrentHash(self,hash):
		torrentPath = os.path.join( self.incomingTorrentDir, hash + '.torrent' )
		try:
			os.remove( torrentPath )
			return True
		except:
			return False

	def startTorrent(self,t):
		if not isinstance(t,Torrent):
			t = Torrent(t)
		if t.exists():
			fn = t.path()
			hash = t.hash()
			if not self.isTorrentActive(t):
				self._startTorrentWithHash(fn,hash)
			else:
				raise TorrentExistsException,'Already exists'

	def _startTorrentWithHash(self,torrentPath,hash):
		startPath = os.path.join( self.incomingTorrentDir, hash + '.torrent' )
		shutil.copy( torrentPath, startPath )
		os.chmod( startPath, 0640 )

	def deleteTorrentHashContents(self,hash):
		if hash is None or hash=='':
			return
		try:
			shutil.rmtree( os.path.join( self.incomingTorrentDir, hash ) )
		except:
			raise

	def copyTorrentHashContents(self,hash,newLocation,fileName=None):
		if not self.isTorrentDataPresentForHash(hash):
			return None

		if not fileName:
			torrent = os.path.join( self.incomingTorrentDir, hash )
			os.rename( torrent, newLocation )
		else:
			torrent = os.path.join( self.incomingTorrentDir, hash, fileName )
			newLocation = os.path.join( newLocation, fileName )
			os.rename( torrent, newLocation )
		return newLocation

	def stopTorrentHashAtRatio(self,hash,ratio):
		return self._createAutostopFile(ratio,torrentHash=hash)

	def autostopExistsForHash(self,hash):
		return os.path.exists( self._autostopFileName(torrentHash=hash) )

	def _autostopFileName(self,torrentHash=None):
		f = str(os.getuid())
		if torrentHash:
			f = hash
		return os.path.join( self.autostopDir(), f+".xml" )

	def removeAutostopForHash(self,hash):
		if self.autostopExistsForHash(hash):
			os.remove(self._autostopFileName(torrentHash=hash))

	def _createAutostop(self,ratio,torrentHash=None,forceCreation=False):
		stopFile = self._autostopFileName(torrentHash=torrentHash)

		if not torrentHash:
			forceCreation = True

		if os.path.exists( stopFile ) and not forceCreation:
			raise
		try:
			f = open( stopFile, 'w' )
			f.write( '<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n' )
			f.write( '<autostop date="%s">\n' % time.ctime() )
			f.write( '\t<stop>\n' )

			if torrentHash:
				f.write( '\t\t<hash>%s</hash>\n' % torrentHash )

			f.write( '\t\t<ratio>%s</ratio>\n' % ratioLevel )
			f.write( '\t</stop>\n' )
			f.write( '</autostop>\n' )
			f.close()
			os.chmod( stopFile, 0640 )
		except:
			raise

		
