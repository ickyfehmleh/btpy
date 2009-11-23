#!/usr/local/bin/python
###########################################################################
# TODO
# - consult .stats.db to find out if a 1:1 ratio is achieved.  if not, do not
#   let torrent stop without -f flag (force)
#
# BUGS
# X a paused torrent cannot be stopped, it has to be started again and then
#   stopped.  should probably check to see if INCOMING/<mdsum> exists, then
#   proceed with writing the output
# 
###########################################################################
import os
import time
import sys
import os.path
from BitTornado.bencode import *
from shutil import *
import getopt
from common import *

escapeFilenames = True

#
# return a list of all the files contained in a torrent
#
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
		f = open( ACTIVE_USER_TORRENTS, mode='r' )
		for line in f.readlines():
			tname = line.split(FILE_DELIMITER)[0]
			hash = line.split(FILE_DELIMITER)[1]

			if not isTorrentHashActive(hash):
				if not tname in args:
					args.append( tname )
		f.close()
		if len(args) == 0:
			print 'No inactive torrents found!'
			exit()

if len(args) == 0:
	printUsageAndExit(sys.argv[0])

for torrent_name in args:
	print
	metainfo_name = findTorrent(torrent_name)
	
	if metainfo_name == '':
		print "Could not locate anything matching '%s', sorry!" % torrent_name
		continue

	if not isFileOwnerCurrentUser(metainfo_name):
		print 'You do not own torrent \'%s\'' % metainfo_name
		continue

	info = infoFromTorrent(metainfo_name)

	if info == '':
		print 'Could not fetch info for %s' % metainfo_name
		continue

	info_hash = hashFromInfo(info) #sha( bencode( info ) ).hexdigest()

	# figure out what the name of the torrent is
	torrentPath = os.path.join( INCOMING_TORRENT_DIR, info_hash )
	torrentName = torrentPath + '.torrent'

	# torrent may be paused so we'll check for the path first
	if exists( torrentPath ):
		if not pauseOnly:
			## log that this torrent was downloaded
			recordDownloadedTorrent(info)

		if isTorrentHashActive( info_hash ):
			os.remove( torrentName )

			if pauseOnly:
				print 'Paused torrent %s' % basename( metainfo_name )
				continue
		
			print 'Shutting down torrent %s' % basename( metainfo_name )

			# - wait 20 seconds for btlaunchmanycurses to notice the rm'ed
			# torrent file.
			print 'Sleeping for %d seconds...' % MAX_SLEEP_TIME
			printSleepingStatus( MAX_SLEEP_TIME )

		if deleteOnly:
			try:
				sys.stdout.write( 'Removing contents...' )
				sys.stdout.flush()
				rmtree( torrentPath )
				sys.stdout.write( 'Done!\n' )
				sys.stdout.flush()				
			except:
				sys.stdout.flush()
				print 'Failed to remove torrent contents (%s)' % sys.exc_info()
				continue
		else:
			# - move INCOMING_TORRENT_DIR/mdsum/ to /share/torrents/%torrentFileNameMinus-dot_torrent%
			#   UNLESS the torrent has a directory specified in it, in which
			#   case move the mdsum dir to that directory.
			cwd = os.path.realpath( os.getcwd() )
			if escapeFilenames:
				output = os.path.join( cwd, escapeFilename( info['name'] ) )
			else:
				output = os.path.join( cwd, info['name'] )

			if info.has_key('length'):	## assume a single file
				torrentedFile = os.path.join( torrentPath, info['name'] )
				os.rename(torrentedFile, output)
				os.utime( output, None )

				## now wipe the directory
				os.rmdir( torrentPath )
				print 'Wrote output to %s' % output
			else:
				os.rename( torrentPath, output )

				for tf in allFilesFromTorrentInfo(info):
					fp = os.path.join( output, tf )
					if os.path.exists(fp):
						os.utime( fp, None )

				print 'Wrote contents to dir %s' % output

			## log to our list of torrents
			recordLocalTorrent(output)

		## now remove the local torrent file
		try:
			os.remove( metainfo_name )
		except:
			print "Could not remove local torrent."
	else:
		print 'No torrent found with a signature of %s' % info_hash
