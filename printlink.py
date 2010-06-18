#!/usr/bin/env python
#
# dont fully stop a torrent, but allow the contents to be downloaded
#
import os
import time
import getopt

from sys import *
from os.path import *
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
try:
	opts, args = getopt.getopt(argv[1:], 'dp', ['dont-log','path='])
except getopt.GetoptError:
	print '%s will allow you to download a torrent without stopping it.' % argv[0]
	print
	print 'USAGE: %s file1.torrent ... fileN.torrent' % argv[0]
	exit(2)

OUTPUT_PATH = USER_DL_DIR
logTorrent=True

for opt,arg in opts:
	if opt == '--path':
		OUTPUT_PATH=os.path.expandvars(os.path.expanduser(arg))
	if opt == '-p':
		OUTPUT_PATH=os.getcwd()
	if opt in ('-d','--dont-log'):
		logTorrent=False

outputs = []

for torrent_name in args:
	metainfo_name = findTorrent(torrent_name)
	
	if metainfo_name == '':
		print "Could not locate anything matching '%s', sorry!" % torrent_name
		continue
	# make sure we have a .torrent file
	if not metainfo_name.endswith('.torrent'):
		print '%s does not appear to be a torrent, skipping' % metainfo_name
		continue

	info = infoFromTorrent(metainfo_name)
	info_hash = hashFromInfo(info)

	torrentName = os.path.join( INCOMING_TORRENT_DIR, info_hash )

	if not os.path.exists( torrentName ):
		print '%s does not exist!' % metainfo_name
		continue

	if info.has_key('length'): # single file
		torrentName = os.path.join( INCOMING_TORRENT_DIR, info_hash, info['name'] )
		outputName = join( OUTPUT_PATH, escapeFilename( info['name'] ) )
		if os.path.exists( outputName ):
			printAlreadyLinkedToMessage( outputName )
			continue
		else:
			os.link(torrentName, outputName )
	else: # multiple files
		baseDir = os.path.join( OUTPUT_PATH, escapeFilename(info['name']) )

		if os.path.exists( baseDir ):
			printAlreadyLinkedToMessage( baseDir )
			continue
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
		if logTorrent:
			recordLocalTorrent( file )
		stderr.write( '/share/bin/cleartorrents %s\n' % file )
	stderr.flush()
