#
# common methods
# 
import os
import time

from pythonutils.pathutils import Lock, LockError, LockFile
from sys import *
from os.path import *
from sha import *
from BitTornado.bencode import *
from shutil import *
import re
import datetime
from xml.dom import minidom, Node
import string
from UserDataStore import UserDataStore, UserData
from FlatFileUserDataStore import FlatFileUserDataStore
from TorrentStore import TorrentStore
import sys

## constants
#INCOMING_TORRENT_DIR = '/share/incoming'
#COMPLETED_TORRENT_DIR = '/share/torrents'
#PERCENT_KEEP_FREE = .12

PERCENT_KEEP_FREE = .30
INCOMING_TORRENT_DIR = '/share/test/monitored'
COMPLETED_TORRENT_DIR = '/share/test/monitored.done'

USER_DL_DIR=os.path.join( '/home/torrentuser/torrents', str(os.getuid()) )
EXPIRED_TORRENT_DIR='/share/expired'
MAX_SLEEP_TIME = 20
## /constants

def initDataStore():
	ok = True
	ds = TorrentStore(INCOMING_TORRENT_DIR)

	# make sure things exist
	if not isDirectoryWriteable(INCOMING_TORRENT_DIR):
		ok = False
		printmsg( 'Cannot write to incoming torrent dir (%s)' % INCOMING_TORRENT_DIR )
	
	if not isFileReadable( ds.torrentXML() ):
		ok = False
		printmsg( 'Cannot read torrent XML (%s)' % ds.torrentXML() )

	if not isFileReadable( ds.allowedTrackersList() ):
		ok  = False
		printmsg( 'Cannot read tracker list (%s)' % ds.allowedTrackersList() )

	if not isDirectoryWriteable( ds.autostopDir() ):
		ok = False
		printmsg( 'Cannot init autostop dir (%s)' % ds.autostopDir() )

	if not isFileReadable( ds.masterHashList() ):
		ok = False
		printmsg( 'Cannot read master hash list (%s)' % ds.masterHashList() )

	if not isFileWriteable( ds.masterHashList() ):
		ok = False
		printmsg( 'Cannot write to master hash list (%s)' % ds.masterHashList() )

	if ok:
		return ds

	printmsg( 'Unable to initialize TorrentStore!' )
	sys.exit()
	return None

# make sure a file exists and is readable
def isFileReadable(fileName):
        if os.path.exists(fileName) and os.path.isfile(fileName) and os.access(fileName, os.R_OK):
                return True
        return False

def isFileWriteable(fileName):
        if os.path.exists(fileName) and os.path.isfile(fileName) and os.access(fileName, os.W_OK):
                return True
        return False

def isDirectoryWriteable(dirName):
        if os.path.exists(dirName) and os.path.isdir(dirName) and os.access( dirName, os.W_OK ):
                return True
        return False
# ======================================================================
# print a msg with the datetime attached
def printmsg(msg,showDate=True):
	if showDate:
		t = time.strftime( '%Y-%m-%d @ %I:%M:%S %p' )
		print '[%s]: %s' % (t, msg)
	else:
		print msg

def sysprint(msg):
	sys.stdout.write( msg )
	sys.stdout.flush()

# locate a named node, return its value
def findNodeName(parentNode, name):
	for childNode in parentNode.childNodes:
		if name == childNode.nodeName:
			content = []
			for textNode in childNode.childNodes:
				content.append( textNode.nodeValue )
			return string.join( content )
	return ''


# find ratio for an autostop file
def ratioFromAutostopFile(fn):
	asf = minidom.parse( fn )
	req = asf.documentElement.childNodes[1]
	ratio = findNodeName( req, 'ratio' )
	if ratio:
		return float(ratio)
	return 0.00

# ======================================================================
def isFileOwnerCurrentUser(fn):
	return os.stat(fn).st_uid == os.getuid()

# ======================================================================
# replace crazy chars with _ to make scp life easier and scriptable
def escapeFilename(s):
	return re.sub("[^A-Za-z0-9\.]", "_", s)

# ======================================================================
## REFACTOR to launchmanyxml.py
def nameFromTorrent(fn):
	info = infoFromTorrent(fn)

	if info == '':
		return None
	else:
		return info['name']

## get metainfo from a given torrent
def infoFromTorrent(fn):
	try:
		metainfo_file = open(fn, 'rb')
		metainfo = bdecode(metainfo_file.read())
		metainfo_file.close()
		info = metainfo['info']
		return info
	except:
		return ''
