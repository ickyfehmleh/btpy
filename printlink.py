#!/usr/bin/env python
#
# dont fully stop a torrent, but allow the contents to be downloaded
##
# BUGS
# 
# 1- when using the uid directory, getfiles.sh will log the uid dir.  cleartorrents
#    will then fail.  cleartorrent (singular, the new one) may work fine and
#    do the expected thing...
#
# 2- should probably log uid dir + file(s) to ~/torrents.list
##
import os
import time

from sys import *
from os.path import *
from sha import *
from BitTornado.bencode import *
from shutil import *

from common import *

def printAlreadyLinkedToMessage(f):
	stderr.write( '%s has already been linked to!\n' % f )
	stderr.flush()

#==============================================================================

if not os.path.exists(USER_DL_DIR):
	try:
		os.mkdir( USER_DL_DIR, 0700 )
	except:
		print 'Failed to create %s!' % USER_DL_DIR
		exit(2)

#==============================================================================

if len(argv) == 1 or argv[1] == '--help':
	print '%s will allow you to download a torrent without stopping it.' % argv[0]
	print
	print 'USAGE: %s file1.torrent ... fileN.torrent' % argv[0]
	exit(2)

outputs = []

for torrent_name in argv[1:]:
	metainfo_name = findTorrent(torrent_name)
	
	if metainfo_name == '':
		print "Could not locate anything matching '%s', sorry!" % torrent_name
		continue
	# make sure we have a .torrent file
	if not metainfo_name.endswith('.torrent'):
		print '%s does not appear to be a torrent, skipping' % metainfo_name
		continue

	info = infoFromTorrent(metainfo_name)
	info_hash = sha( bencode( info ) ).hexdigest()

	torrentName = os.path.join( INCOMING_TORRENT_DIR, info_hash )

	if info.has_key('length'): # single file
		torrentName = os.path.join( INCOMING_TORRENT_DIR, info_hash, info['name'] )
		outputName = join( USER_DL_DIR, escapeFilename( info['name'] ) )
		if os.path.exists( outputName ):
			printAlreadyLinkedToMessage( outputName )
		else:
			os.link(torrentName, outputName )
	else: # multiple files
		baseDir = os.path.join( USER_DL_DIR, escapeFilename(info['name']) )

		if os.path.exists( baseDir ):
			printAlreadyLinkedToMessage( baseDir )
		else:
			os.mkdir( baseDir )
			for file in info['files']:
				path = ''
				for item in file['path']:
					if (path != ''):
						path = path + "/"
					path = path + item
					# check to see if path is a dir in the torrent
					# because we cant hardlink dirs
					if os.path.isdir(os.path.join( torrentName, path )):
						tmpOutputDir = os.path.join( baseDir, path )
						if not os.path.exists(tmpOutputDir):
							try:
								os.mkdir(tmpOutputDir)
							except:
								print 'Failed to create dir %s' % path
				tfile = path
	
				fullOutputPath = os.path.join( baseDir, tfile )
				fullTorrentPath = os.path.join( torrentName, tfile )
				os.link( fullTorrentPath, fullOutputPath )
			outputName = baseDir
	
	print '%s' % outputName
	outputs.append( outputName )
	
if len(outputs) > 0:
	stderr.write( '\n*** Please remember to use cleartorrents after downloading ***\n' )
	for file in outputs:
		stderr.write( '/share/torrents/bin/cleartorrents %s\n' % file )
	stderr.flush()
