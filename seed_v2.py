#!/usr/bin/env python
#
# seed an existing file by hardlinking it into the incoming dir
#
import os
import time

from sys import *
from os.path import *
from sha import *
from BitTornado.bencode import *
from shutil import *

from common import *

#==============================================================================

if len(argv) == 1:
	print '%s will allow you to download a torrent without stopping it.' % argv[0]
	print
	print 'USAGE: %s file1.torrent ... fileN.torrent' % argv[0]
	exit(2)

for torrent_name in argv[1:]:
	metainfo_name = findTorrent(torrent_name)
	
	if metainfo_name == '':
		print "Could not locate anything matching '%s', sorry!" % torrent_name
		continue
	info = infoFromTorrent(metainfo_name)
	info_hash = sha( bencode( info ) ).hexdigest()

	if isTorrentHashActive( info_hash ):
		print 'A torrent the signature %s is already being downloaded' % info_hash
		continue

	torrentName = os.path.join( INCOMING_TORRENT_DIR, info_hash )

	if info.has_key('length'): # single file
		## FIXME reverse this logic, link from the current dir
		## to the incoming torrent dir
		torrentName = os.path.join( INCOMING_TORRENT_DIR, info_hash, info['name'] )
		outputName = join( USER_DL_DIR, escapeFilename( info['name'] ) )
		os.link(torrentName, outputName )
	else: # multiple files
		baseDir = os.path.join( USER_DL_DIR, escapeFilename(info['name']) )

		if not os.path.exists( baseDir ):
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
