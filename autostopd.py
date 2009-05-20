#!/usr/bin/python
#
# auto stop a torrent
#
##
# TODO:
#
# - add default ratio for users
#   ^^ store in <their-uid>.xml (autostop needs to be modified for this)
#   ^^ check all torrents owned by that uid
##
#

import sys
import getopt
from common import *
from xml.dom import minidom, Node
import glob
import string
import pwd
import time

uid = os.getuid()
os.chdir( COMPLETED_TORRENT_DIR )

def allFilesFromTorrentInfo( info ):
	files = []

	if info.has_key('length'):
		files.append( info['name'] )
	else:
		for file in info['files']:
			path = ''
			for item in file['path']:
				if (path != ''):
					path = path + "/"
				path = path + item
			files.append( path )
	return files


################################################################################
class AutostopDaemon(object):
	def __init__(self):
		self._log=MessageLogger('autostopd')
		self.printmsg('Starting...')

	def touchFile(self,file):
		if os.path.exists(file):
			os.utime(file, None)
			self.printmsg( 'Touched %s' % file)
		else:
			self.printmsg( 'Cannot touch %s: does not exist' % file )

	def touchAllTorrentFiles(self,info,torrentDir):
		for tf in allFilesFromTorrentInfo(info):
			self.touchFile( os.path.join( torrentDir, tf ) )
		self.touchFile( torrentDir )

	def isTorrentProcessing(self,hash):
		if isTorrentHashActive(hash):
			return True
		else:
			fn = os.path.join( INCOMING_TORRENT_DIR, hash )
			return os.path.exists( fn )

	def usernameForUID(self,uid):
		return pwd.getpwuid( int(uid) )[0]

	def printmsg(self,s):
		self._log.printmsg(s)

	def processLiveFiles(self):
		self.printmsg('processLiveFiles()...')

		# first find out if we even have pending requests
		if len( glob.glob( os.path.join(AUTOSTOPD_DIR, '*.xml' ) ) ) == 0:
			return

		try:
			doc = minidom.parse( TORRENT_XML )
		except:
			return True
	
		for torrent in doc.documentElement.childNodes:
			if torrent.nodeName == 'torrent':
				hash = findNodeName( torrent, 'hash' )
				bytesUp = int( findNodeName( torrent, 'totalUploadBytes' ) )
				bytesDn = int( findNodeName( torrent, 'totalDownloadBytes' ) )
				fsize = int( findNodeName( torrent, 'filesize' ) )
				torrentOwnerUID = findNodeName( torrent, 'owner' )
				ownerDefaultsFile = os.path.join( AUTOSTOPD_DIR, torrentOwnerUID ) + '.xml'
				autostopFile = os.path.join( AUTOSTOPD_DIR, hash ) + '.xml'

				# should we even operate on it?  is it completed?
				if findNodeName( torrent, 'status' ) != "seeding":
					continue

				# any requests for this?
				if os.path.exists( autostopFile ) or os.path.exists( ownerDefaultsFile ):
					removeStopFile = False
					stopFile = None

					if os.path.exists( ownerDefaultsFile ):
						stopFile = ownerDefaultsFile

					# per-torrent overrides defaults
					if os.path.exists( autostopFile ):
						removeStopFile = True
						stopFile = autostopFile
				
					actionRatio = float(ratioFromAutostopFile( stopFile ))
					diskOwnerUID = os.stat(stopFile).st_uid
				
					liveTorrent = findNodeName( torrent, 'fullpath' )
	
					# check owners, see if they match the .torrent and the .xml
					torrentOwnerUID = int(torrentOwnerUID)

					if torrentOwnerUID != diskOwnerUID:
						torrentOwnerName = self.usernameForUID(torrentOwnerUID)
						stopOwnerName = self.usernameForUID(diskOwnerUID)
						self.printmsg( 'SKIPPING %s: torrent owned by %s, stop file owned by %s' % (hash, torrentOwnerName, stopOwnerName))
						continue
	
					if bytesUp == 0 or bytesDn == 0:
						continue

					currentRatio = float( bytesUp ) / float( bytesDn )

					if currentRatio > actionRatio and actionRatio > 0.0:
						info = infoFromTorrent( liveTorrent )

						if info == '':
							self.printmsg( 'Stopped hash %s due to ratio [%.2f] > desired ratio [%.2f]' % (hash, currentRatio, actionRatio))
						else:
							self.printmsg( 'Stopped "%s" (hash: %s) due to ratio [%.2f] > desired ratio [%.2f]' % (info['name'], hash, currentRatio, actionRatio))

						if os.path.exists( liveTorrent ):
							self.removeFile( liveTorrent )
							self.touchAllTorrentFiles(info, os.path.join( INCOMING_TORRENT_DIR, hash) )
						else:
							self.printmsg( 'Error: %s does not exist' % liveTorrent )

						if removeStopFile:
							self.removeFile( stopFile )
	def processExpiredFiles(self):
		self.printmsg('processExpiredFiles()...')

		# now cycle through all the files and make sure they're for 
		# torrents that are still running
		for root, dir, files in os.walk( AUTOSTOPD_DIR ):
			for sf in files:
				stopFile = os.path.join( AUTOSTOPD_DIR, sf )

				if not stopFile.endswith( '.xml'):
					continue

				# check to see if its a user defaults file
				hash = sf.split('.')[0]

				try:
					int(hash)
					continue
				except:
					# dealing with a hashfile
					if not self.isTorrentHashActive(hash):
						self.printmsg( 'Removed stopped torrent %s' % stopFile )
						self.removeFile( stopFile )

	def process(self):
		self.processLiveFiles()
		self.processExpiredFiles()
		return True

	def close(self):
		self.printmsg('Shutting down...')
		self._log.close()

	def removeFile(self,file):
		self.printmsg('Removing file: %s' % file )
		os.remove( file )
############################################################################################################

# main:
sleepTime = MAX_SLEEP_TIME
p = AutostopDaemon()
p.printmsg( 'Will sleep for %d secs' % sleepTime)
p.printmsg( 'Checking dir %s' % AUTOSTOPD_DIR)

cont = True

while cont:
	try:
		cont = p.process()
		time.sleep(sleepTime)
	except KeyboardInterrupt:
		cont = False
	except:
		print 'Unhandled exception: ', sys.exc_info()[0]

p.printmsg( 'Exiting gracefully!')
p.close()
exit()
