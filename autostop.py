#!/usr/bin/python
#
# auto stop a torrent
#

import sys
import getopt
from common import *
from xml.dom import minidom, Node
import glob

uid = os.getuid()

print ''

###################################################################################
class Autostopper(object):
	def __init__(self,autostopDir):
		self._autostopDir=autostopDir

	def getStopRatioForHash(self, hash,uid):
		ratio = float(0.0)
		stopFile = self._getAutostopFile( hash )

		if os.path.exists(stopFile):
			ratio = ratioFromAutostopFile(stopFile)
		else:
			stopFile = self._getAutostopFile( uid )
			if os.path.exists(stopFile):
				ratio = ratioFromAutostopFile(stopFile)
		return ratio

	def stopHashAtRatio( self, hash, ratio ):
		self._createAutostopFile( ratio,hash=hash)

	def stopAllAtRatio( self, ratio ):
		self._createAutostopFile( ratio )

	def _getAutostopFile( self, filePart ):
		return os.path.join( self._autostopDir, filePart + '.xml' )

	def isAutostopping( self, hash ):
		autostopFile = self._getAutostopFile(hash)
		return os.path.exists( autostopFile )

	def remove(self, hash):
		self.deleteAutostopForHash( hash )

	def deleteAutostopForHash( self, hash ):
		if self.isAutostopping(hash):
			file = self._getAutostopFile( hash )
			os.remove( file )

	def _createAutostopFile(self, ratioLevel, hash=None):
		stopFile = None

		if hash is not None:
			stopFile = hash
		else:
			stopFile = str(os.getuid())

		autostopFile = self._getAutostopFile(stopFile)

		try:
			f = open( autostopFile, 'w' )
			f.write( '<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n' )
			f.write( '<autostop>\n' )
			f.write( '\t<stop>\n' )	

			if hash:
				f.write( '\t\t<hash>%s</hash>\n' % hash )

			f.write( '\t\t<ratio>%s</ratio>\n' % ratioLevel )
			f.write( '\t</stop>\n' )
			f.write( '</autostop>\n' )
			f.close()
			os.chmod( autostopFile, 0640 )
		except:
			print 'Problem writing out this request!'
			raise

###################################################################################
#
def printUsageAndExit():
	print 'This will stop a torrent after a certain ratio is achieved.'
	print 'Usage: %s [-d] [-f] <ratio> <file1.torrent> ... <fileN.torrent>' % sys.argv[0]
	print '-d ==> delete a previous request for this torrent.'
	print '-f ==> overwrite another request if present.'
	print 'Optional: --all <ratio> ==> Set default stop ratio for all torrents'
	exit(2)

try:
	opts,args = getopt.getopt( sys.argv[1:], 'adf', ['force','delete','all'] )
except getopt.GetoptError:
	printUsageAndExit()

deleteExisting = False
ratioLevel = None
hash = None
forceOverwrite = False
stopAll = False

# stop on ratio?
for o,a in opts:
	if o in ('-d', '--delete'):
		deleteExisting = True
	if o in ('-f', '--force'):
		forceOverwrite = True
	if o in ('-a', '--all'):
		stopAll = True

if len(args) == 0:
	printUsageAndExit()

stopper = Autostopper(AUTOSTOPD_DIR)

startArg = 1

if not deleteExisting:
	if len(args):
		try:
			ratioLevel = float(args[0])
		except:
			print 'Bad ratio, try using numbers.'
			exit(2)
	else:
		printUsageAndExit()
else:
	startArg = 0

if stopAll:
	stopper.stopAllAtRatio( ratioLevel )
	print 'Will stop ALL torrents after a ratio of %.2f has been achieved.' % (ratioLevel)
	print 'If a separate request is made for a torrent, that request overrides the default'
else:
	for tfile in args[startArg:]:
		torrent = infoFromTorrent(tfile)
		if torrent == '':
			print 'Cannot find info on torrent %s' % tfile
			continue
	
		if not isFileOwnerCurrentUser(tfile):
			print 'You do not own %s' % tfile
			continue
	
		hash = sha( bencode( torrent ) ).hexdigest()
		torrentName = torrent['name']
	
		# make a request to autostopd
		if stopper.isAutostopping(hash) and not forceOverwrite:
			if deleteExisting:
				try:
					stopper.remove(hash)
					print 'Request for %s removed!' % tfile
				except:
					print 'Problem removing request for torrent %s' % tfile
				continue
			else:
				print 'Already have a request for torrent %s, use -d to delete it.' % tfile
				continue
		else:
			if deleteExisting:
				print 'No request for %s found' % torrentName
				continue
	
			stopper.stopHashAtRatio( hash, ratioLevel )
			print 'Will stop torrent %s at ratio %.2f.' % (torrentName, ratioLevel)
