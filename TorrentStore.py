#
# data store for all users
#
import os
import os.path
import shutil
from UserDataStore import UserData

class TorrentStore:
	__slots__ = ('incomingTorrentDir','fileDelimiter')

	def __init__(self,itd):
		self.incomingTorrentDir=itd
		self.fileDelimiter=':'

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

	def isTorrentActive(self,userData):
		return self.isTorrentHashActive(userData.hash)

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

	def isTorrentDataPresent(self,userData):
		return self.isTorrentDataPresentForHash(userData.hash)

	def isTorrentDataPresentForHash(self,hash):
		return os.path.exists( os.path.join( self.incomingTorrentDir, hash ) )

	def isTorrentPaused(self,userData):
		return self.isTorrentHashPaused(userData.hash)

	def isTorrentHashPaused(self,hash):
		if self.isTorrentHashActive(hash):
			return self.isTorrentDataPresent(hash)
		return False

	def stopTorrent(self,userData):
		self.stopTorrentHash(userData.hash)

	def pauseTorrent(self,userData):
		self.stopTorrent(userData)

	def stopTorrentHash(self,hash):
		torrentPath = os.path.join( self.incomingTorrentDir, hash + '.torrent' )
		try:
			os.remove( torrentPath )
			return True
		except:
			return False

	def startTorrent(self,torrentPath,hash):
		startPath = os.path.join( self.incomingTorrentDir, hash + '.torrent' )
		if not self.isTorrentHashActive(hash):
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

		
