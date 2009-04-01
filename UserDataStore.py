import sys
import time
from BitTornado.bencode import *

class UserData:
	__slots__ = ('name', 'hash', 'path', 'startTime', 'status', 'statusChangeTime')

	# todo : getters and setters for these?
	def __init__(self):
		self.name = None
		self.hash = None
		self.path = None
		self.startTime = time.time()
		self.status = None
		self.statusChangeTime = time.time()

	def isActive(self):
		return self.status == 'A'

	def isDownloaded(self):
		return self.status == 'D'

	def isPaused(self):
		return self.status == 'P'

	def isRemoved(self):
		return self.status == 'R'

	def isStopped(self):
		if not self.isActive() and not self.isPaused() and not self.isDownloaded():
			return True
		return False

	def _changeItemStatus(self,statusCode):
		self.status = statusCode
		self.statusChangeTime = time.time()

	def removeWithoutDownloading(self):
		self._changeItemStatus('R')

	def pause(self):
		self._changeItemStatus('P')

	def stop(self):
		self._changeItemStatus('S')

	def start(self):
		self._changeItemStatus('A')

	def download(self):
		self._changeItemStatus('D')

class UserDataStore:
	_outputFileName = None
	_items = []

	def __init__(self):
		print 'no-arg constructor'

	def __init__(self,s):
		self._outputFileName = s

	def findTorrentFromFile(self,fileName):
		data = self.dataFromTorrentFile(fileName)
		if data is not None:
			return self.findTorrentWithHash(data.hash)
		return None

	def dataFromTorrentFile(self,fileName):
		fileName = os.path.abspath(fileName)
		info = infoFromTorrent(fileName)
		if info is None:
			return None
		return self.createNewTorrent(path=fileName,
			name=info['name'],
			hash=sha(bencode(info)).hexdigest())

	def createNewTorrent(self,path=None,name=None,hash=None):
		ud = UserData()
		ud.name=name
		ud.path=path
		ud.hash=hash
		ud.status='U' # unknown status

	def addTorrent(self,userData):
		self._items.append( userData )

	def addActiveTorrent(self,userData):
		userData.status = 'A'
		self.addTorrent( userData )

	def save(self):
		self.writeToOutput()

	def writeToOutput(self):
		raise NotImplementedError, "Subclasses must define writeToOutput"

	def allActiveTorrents(self):
		return self.allItemsWithStatus( 'A' )

	def allStoppedTorrents(self):
		return self.allItemsWithStatus( 'S' )

	def allPausedTorrents(self):
		return self.allItemsWithStatus( 'P' )

	def findTorrentWithHash(self,hash):
		for item in self._items[:]:
			if item.hash == hash:
				return item
		return None

	def changeItemStatus(self,item,newStatusCode):
		item.status = newStatusCode
		item.statusChangeTime = time.time()

	def allItemsWithStatus(self,statusCode):
		matches = []
		for item in self._items[:]:
			if item.status == statusCode:
				matches.append( item )
		return matches

	def allActiveTorrentHashes(self):
		hashes = []
		for item in self._items[:]:
			if item.isActive():
				hashes.append( item.hash )
		return hashes
