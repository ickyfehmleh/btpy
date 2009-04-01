import sys
from pythonutils.pathutils import Lock, LockError, LockFile
import time
from UserDataStore import UserDataStore,UserData

class FlatFileUserDataStore(UserDataStore):
	_FILE_DELIMITER=':'
	_PATH_POSITION=0
	_HASH_POSITION=1
	_NAME_POSITION=2
	_TIME_POSITION=3
	_STATUS_POSITION=4
	_TIMESTATUS_POSITION=5
	_OUTPUT_PATH_POSITION=6

	def __init__(self,s):
		UserDataStore.__init__(self,s)
		self._fetchData()

	def writeToOutput(self):
		f = LockFile( self._outputFileName, mode='w', timeout=5, step=0.1 )
		for item in self._items[:]:
			f.write( item.path )
			f.write( self._FILE_DELIMITER )
			f.write( item.hash )
			f.write( self._FILE_DELIMITER )
			f.write( item.name )
			f.write( self._FILE_DELIMITER )
			f.write( str(item.startTime) )
			f.write( self._FILE_DELIMITER )
			f.write( item.status )
			f.write( self._FILE_DELIMITER )
			f.write( str(item.statusChangeTime) )
			f.write( '\n' )
		f.close()

	def _fetchData(self):
		f = LockFile( self._outputFileName, mode='r', timeout=5, step=0.1)
		for line in f.readlines():
			line = line[:-1]
			userDataLine = self._convertToUserData( line )
			self.addTorrent( userDataLine )
		f.close()

	def _convertToUserData(self,line):
		ud = UserData()
		info = line.split(':')
		ud.path = info[self._PATH_POSITION]
		ud.hash = info[self._HASH_POSITION]
		ud.name = info[self._NAME_POSITION]
		ud.startTime = float(info[self._TIME_POSITION])
		ud.status = info[self._STATUS_POSITION]
		ud.statusChangeTime = float(info[self._TIMESTATUS_POSITION])
		return ud
