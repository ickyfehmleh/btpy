#!/usr/local/bin/python
###########################################################################
# TODO
# - consult .stats.db to find out if a 1:1 ratio is achieved.  if not, do not
#   let torrent stop without -f flag (force)
#
###########################################################################
import os
import time
import sys
import os.path
from sha import *
from BitTornado.bencode import *
from shutil import *
import getopt
from common import *
from UserDataStore import UserData,UserDataStore
from FlatFileUserDataStore import FlatFileUserDataStore

escapeFilenames = True

USER_TORRENT_LIST=os.path.join( os.getenv( "HOME" ), 'torrents.list' )

#==============================================================================
def printSleepingStatus(timeToSleep):
	timeToSleep = timeToSleep + 1
	for i in range(1, timeToSleep ):
		sysprint( "\r%d" % i )
		time.sleep( 1 );
	sysprint( "\n" );

#==============================================================================
# handy list of torrents one has downloaded so they can potentially script
# the scp'ing of them to their local machines
def recordLocalTorrent(path):
	filename = USER_TORRENT_LIST
	fn = LockFile( filename, mode='a', timeout=5, step=0.1 )
	fn.write( path )
	fn.write( '\n' )
	fn.close()
#==============================================================================
def printUsageAndExit(appName):
	print 'USAGE: %s [--delete/-d] [--no-escape] [--pause/-p] file1.torrent ... fileN.torrent' % appName
	print 'Option \'no-escape\' will prevent filenames from being escaped.'
	print 'Option \'delete\' will simply remove the torrent without writing any output.'
	print 'Option \'pause\' will pause a torrent.'
	#print 'Option \'all-active\' will remove all your active torrents.'
	print 'Option \'all-inactive\' or \'-i\' will remove all your INACTIVE torrents.'
	sys.exit(2)

#==============================================================================

deleteOnly = False
pauseOnly = False
forceStop = False

try:
	opts, args = getopt.getopt(sys.argv[1:], 'dpfi', ['pause', 'no-escape', 'escape=','delete','force','all-mine', 'all-active','all-inactive','inactive'])
except getopt.GetoptError:
	printUsageAndExit(sys.argv[0])

dataStore = initDataStore()
userDataStore = dataStore.getUserDataStore(torrentList=USER_TORRENT_LIST)

for opt,arg in opts:
	if opt == "--no-escape":
		escapeFilename = False
	if opt == "--escape":
		print 'escape=REGEX not yet implemented'
	if opt in ("--delete", "-d"):
		deleteOnly = True
	if opt in("--pause", "-p"):
		pauseOnly = True
	if opt in("-f","--force"):
		forceStop = True
	if opt in("--all-mine", "--all-active"):
		print 'ERROR: Argument --all-active not implemented!'
	if opt in('--all-inactive','-i','--inactive'):
		for line in userDataStore.allActiveTorrents():
			tname = line.name
			hash = line.hash

			if not dataStore.isTorrentHashActive(hash) and dataStore.isTorrentDataPresent(hash) and not tname in args:
				args.append( tname )
		if len(args) == 0:
			print 'No inactive torrents found!'
			exit()

if len(args) == 0:
	printUsageAndExit(sys.argv[0])

for metainfo_name in args:
	print

	if not os.path.exists( metainfo_name ) or not isFileReadable( metainfo_name):
		print '%s not found or not readable.' % metainfo_name
		continue

	if not isFileOwnerCurrentUser(metainfo_name):
		print 'You do not own torrent \'%s\'' % metainfo_name
		continue

	data = userDataStore.findTorrentFromFile( metainfo_name )
	if data is None:
		print 'Could not fetch info for %s' % metainfo_name
		continue

	# torrent may be paused so we'll check for the path first
	if dataStore.isTorrentDataPresent(data):
		if pauseOnly:
			data.pause()
		else:
			data.stop()

		if dataStore.isTorrentActive( data ):
			if pauseOnly:
				print 'Paused torrent %s' % basename( metainfo_name )
				dataStore.pauseTorrent(data)
				continue
			dataStore.stopTorrent(data)

			print 'Shutting down torrent %s' % basename( metainfo_name )

			# - wait 20 seconds for btlaunchmanycurses to notice the rm'ed
			# torrent file.
			print 'Sleeping for %d seconds...' % MAX_SLEEP_TIME
			printSleepingStatus( MAX_SLEEP_TIME )

		if deleteOnly:
			try:
				sysprint( 'Removing contents...' )
				dataStore.deleteTorrentContents(data)
				sysprint( 'Done!\n' )
			except:
				sys.stdout.flush()
				print 'Failed to remove torrent contents (%s)' % sys.exc_info()
				continue
		else:
			out = None

			if info.has_key('length'):	## assume a single file
				if escapeFilenames:
					dataStore.copyTorrentContents( info_hash, os.path.realpath( os.getcwd() ), escapeFilename( info['name'] ) )
				else:
					dataStore.copyTorrentContents( info_hash, os.path.realpath( os.getcwd() ), info['name'] )

				## now wipe the directory
				out = dataStore.deleteTorrentContents(info_hash)
				print 'Wrote file to %s' % out
			else:
				if escapeFilenames:
					outdir = os.path.join( cwd, escapeFilename( info['name'] ) )
				else:
					outdir = os.path.join( cwd, info['name'] )

				out = dataStore.copyTorrentContents(info_hash,outdir)
				print 'Wrote directory to %s' % out

			dataStore.deleteTorrentContents(info_hash)

			## log to our list of torrents
			recordLocalTorrent(out)

		## now remove the local torrent file
		try:
			os.remove( metainfo_name )
		except:
			print "Could not remove local torrent."
	else:
		print 'No torrent found with a signature of %s' % info_hash

userDataStore.save()
