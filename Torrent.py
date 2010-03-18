# 
# representation of a torrent file
#

import os.path

class Torrent:
	def __init__(self,fileName):
		self.fileName = os.path.abspath(fileName)
		f = open(self.fileName, 'rb')
		self.metainfo = bdecode(f.read())
		f.close()
		self.info = metainfo['info']

	def announceURL(self):
		return self.metainfo['announce']

	def filesInTorrent(self):
		pass

	def infoHash(self):
		return sha(bencode(self.info)).hexdigest()

	def archiveSize(self):
		pass

	def fileName(self):
		return self.fileName

	def torrentName(self):
		return self.info['name']

	def isFileOwnerCurrentUser(self):
		return os.stat(self.fileName).st_uid == os.getuid()

	def isActive(self):
		hash = self.infoHash()
		fn = os.path.join( INCOMING_TORRENT_DIR, hash + '.torrent' )
		return os.path.exists( fn )
