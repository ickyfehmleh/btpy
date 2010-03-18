#!/usr/local/bin/python
########################################################################
# sort torrents.list based on what's been downloaded
########################################################################
# BUGS
# 1- doesnt take into account the current working dir.  maybe os.path.normpath()
#    or os.path.abspath() ?
#########################################################################

from sys import exit, argv
import os
import os.path
import getopt
from common import *
import shutil

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
	print "USAGE: %s [--fetched-files=FILENAME] [file1 ... fileN]" % appName
	print "--fetched-files= Specify a path to filenames you've downloaded"
	print "(defaults to ~/.fetched_files)"
	exit(2)

########################################################################
# main 
FETCHED_FILES = os.path.join( os.environ["HOME"], ".fetched_files" )
TORRENT_LIST  = os.path.join( os.environ["HOME"], "torrents.list" )

# use getopt to see if we're processing a different FETCHED_FILES list
try:
	opts, args = getopt.getopt(argv[1:], None, ['fetched-files=','torrent-list='])
except:
	printUsageAndExit(argv[0])

for o, a in opts:
	if o == "--fetched-files":
		FETCHED_FILES=os.path.expandvars(os.path.expanduser(a))
	if o == "--torrent-list":
		TORRENT_LIST=os.path.expandvars(os.path.expanduser(a))

# dont make the user have a fetched_files list
if os.path.exists(FETCHED_FILES):
	fetchedFiles = cacheFileContents( FETCHED_FILES )
else:
	fetchedFiles = []

if not os.path.exists(TORRENT_LIST):
	print 'Unable to find %s' % TORRENT_LIST
	printUsageAndExit(argv[0])

# cache our data
torrentList = cacheFileContents( TORRENT_LIST )
newTorrents = []
removeTorrents = []

# if args are specified, clear those torrents
if len(args) > 0:
	for currentArg in args:
		if not os.path.isabs( currentArg ):
			currentArg = os.path.abspath( currentArg )

		if os.path.exists(currentArg):
			removeTorrents.append( currentArg )
			# append to fetched files if not there already
			if not currentArg in fetchedFiles:
				fetchedFiles.append( currentArg )

# find out which files have already been fetched
for currentTorrent in torrentList:
	if  currentTorrent in fetchedFiles:
		if not currentTorrent in removeTorrents:
			removeTorrents.append( currentTorrent )
	else: # hasnt been downloaded yet
		if os.path.exists( currentTorrent ): # make sure file exists
			newTorrents.append( currentTorrent )
		else:
			removeTorrents.append( currentTorrent )

# wipe all the torrents-to-be-removed
if len(removeTorrents) > 0:
	print 'Retiring torrents:'
	for currentRmTorrent in removeTorrents:
		print "%s" % currentRmTorrent
		removeDownloadedTorrent( currentRmTorrent )

# write out to our original files and unlock
writeArrayToFile( newTorrents, TORRENT_LIST )

writeArrayToFile( fetchedFiles, FETCHED_FILES )
