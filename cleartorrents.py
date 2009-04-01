#!/usr/local/bin/python
# FIXME: rename to 'expire'
########################################################################
# sort torrents.list based on what's been downloaded
#########################################################################

import sys
import os
import os.path
import getopt
from common import *
import shutil
from UserDataStore import UserDataStore, UserData
import time

TORRENT_LIST  = 'torrents.list'    #os.path.join( os.environ["HOME"], "torrents.list" )

########################################################################
# move a torrent to the EXPIRED directory
def removeDownloadedTorrent(dir):
	if os.path.exists(dir):
		# flat out delete USER_DL_DIR files
		if dir.startswith( USER_DL_DIR):
			if os.path.isfile( dir ):
				os.remove(dir)
			else:
				shutil.rmtree(dir)
		else:
			newFile = os.path.join( EXPIRED_TORRENT_DIR, basename(dir) )
			os.rename(dir,newFile)

			# touch all files
			for root, dirs, files in os.walk( newFile ):
				for cf in files:
					currentFile = os.path.join( newFile, cf )
					if os.path.exists( currentFile ):
						os.utime( currentFile, None )
				for cd in dirs:
					currentDir = os.path.join( newFile, cd )
					if os.path.exists(currentDir):
						os.utime( currentDir, None )
			os.utime( newFile, None )

########################################################################
# print usage
def printUsageAndExit(appName):
	print "%s will clear downloaded files from your ~/torrents.list" % appName
	print
	print "USAGE: %s [file1 ... fileN]" % appName
	sys.exit(2)

########################################################################
# main 

# use getopt to see if we're processing a different FETCHED_FILES list
try:
	opts, args = getopt.getopt(sys.argv[1:], None, ['torrent-list='])
except:
	printUsageAndExit(sys.argv[0])

for o, a in opts:
	if o == "--torrent-list":
		TORRENT_LIST=os.path.expandvars(os.path.expanduser(a))

ts = initDataStore()
dataStore = dataStore.getUserDataStore(torrentList=TORRENT_LIST)
removeTorrents = []

# if args are specified, clear those torrents
if len(args) > 0:
	for currArg in args:
		currentArg = os.path.abspath( currArg )
		if os.path.exists(currentArg):
			removeTorrents.append( currentArg )

# clear files that have been stopped but are not on the command line
# bin/stop will need to replace the torrent name with the output filename
for currentTorrent in dataStore.allStoppedTorrents():
	remove = False
	ctOutput = currentTorrent.path

	if ctOutput in removeTorrents:
		remove = True

	if not os.path.exists( ctOutput ):
		if not currentTorrent in removeTorrents:
			remove = True

	if remove:
		sysprint('Retiring %s ...' % ctOutput )
		try:
			removeDownloadedTorrent( ctOutput )
			currentTorrent.download()
			sysprint( 'Done\n' )
		except:
			sysprint( sys.exc_info()[0] + '\n' )

# tell our data store we're done processing
dataStore.save()

# FIXME: write all stopped torrents out to ~/torrents.list
