"""\
xml-ized recordActiveTorrent and company
"""

import sys
from xml.dom import minidom, Node
from UserDataStore import UserDataStore
import time

class XMLUserDataStore(UserDataStore):
	_doc = None

	def __init__(self,s):
		UserDataStore.__init__(self,s)
		self._document = minidom.parse( self._outputFileName )

	def addNodeWithValue( self, nodeName, nodeValue ):
		newNode = self._document.createElement(nodeName)
		nodeValue = self._document.createTextNode( nodeValue )
		newNode.appendChild( nodeValue )
		return newNode

	def writeToOutput(self):
		# update doc with last written time
		userNode = self._document.childNodes[0]
		userNode.setAttribute( 'lastWritten', time.ctime() )

		f = LockFile( self._outputFileName, mode='w', timeout=5, step=0.1 )
		self._document.writexml( f )
		f.write( '\n' )
		f.close()

	def recordActiveTorrent(self,torrentPath, name=None, hash=None):
		torrentPath = os.path.abspath( torrentPath )
		startTimeT = time.time()
		startTime = time.ctime()
		torrentNode = document.createElement('torrent')
		torrentNode.appendChild( self.addNodeWithValue( document, 'path', torrentPath ) )
		torrentNode.appendChild( self.addNodeWithValue( document, 'hash', hash ) )
		torrentNode.appendChild( self.addNodeWithValue( document, 'name', '<![CDATA[%s]]>' % name ) )
		startTimeNode = self.addNodeWithValue( document, 'startTime', startTime )
		# set timet attribute
		startTimeNode.setAttribute( 'timet', str(startTimeT) )
		torrentNode.appendChild( startTimeNode )
		self._document.childNodes[0].appendChild( torrentNode )

	def allActiveTorrentHashes(self):
		hashes = []
		for torrent in self._document.documentElement.childNodes:
		return hashes

	def removeActiveTorrent(self,hash):
		for torrent in self._document.documentElement.childNodes:
			if torrent.nodeName == 'torrent':
				torrentHash = findNodeName( torrent, 'hash' )

				if torrentHash == hash:
					print 'Removing %s' % hash
					self._document.documentElement.removeChild(torrent)
