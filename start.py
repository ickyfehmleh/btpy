#!/usr/local/bin/python
##############################################################################
# TODO
# - move .hashes to a .dbm file for quicker lookups
##############################################################################

from sys import *
from os.path import *
from sha import *
from BitTornado.bencode import *
import statvfs
import os
from shutil import *

import cookielib
import urllib2
from urllib import unquote_plus
import re
from common import *
import getopt

########################################################################
def activateTorrent(userDataStore=None, dataStore=None, userData=None ):
	userData.start()
	dataStore.startTorrent( userData )
	userDataStore.addActiveTorrent( userData )
########################################################################

cookieFile = os.path.join(os.environ["HOME"], ".btrss", "cookies.txt" )
forceDownload = False

print

# setup args
try:
	opts, args = getopt.getopt(argv[1:], 'f', ['force', 'cookie='])
except getopt.GetoptError:
	print '%s file1.torrent [--force/-f] [--cookie=path] fileN.torrent' % argv[0]
	exit(2)

for opt,arg in opts:
	if opt in ("-f", "--force"):
		forceDownload = True
	if opt == "--cookie":
		cookieFile =  os.path.expandvars(os.path.expanduser(arg))

if len(args) == 0:
	print '%s file1.torrent file2.torrent file3.torrent ...' % argv[0]
	exit(2)

## setup http stuffs
cj = cookielib.MozillaCookieJar()
if os.path.exists( cookieFile ):
	cj.load( cookieFile )
opener = urllib2.build_opener( urllib2.HTTPCookieProcessor( cj ) )
urllib2.install_opener( opener )
headers = {'User-Agent' : 'Mozilla/4.0 (compatible; python-based client; talk to liekomglol@gmail.com if this is problematic)'}
## end http stuffs

## get the filesize here so each torrent can take off what it needs
## in terms of disk; will give a more accurate picture of the available space
st = os.statvfs(os.getcwd())
totalSpace = st[statvfs.F_BLOCKS] * st[statvfs.F_FRSIZE]
#freeSpace = st[statvfs.F_BAVAIL] * st[statvfs.F_FRSIZE]
freeSpace = st[statvfs.F_BFREE] * st[statvfs.F_FRSIZE]
## take off 12%; dont let disk get above 88% full
freeSpace -= (totalSpace * PERCENT_KEEP_FREE)

dataStore = initDataStore()
userDataStore = dataStore.getUserDataStore()
	
for metainfo_name in args:
	if metainfo_name.startswith( 'http://' ) or metainfo_name.startswith( 'https://' ):
		# make an http request
		try:
			req = urllib2.Request(metainfo_name, None, headers)
			f = urllib2.urlopen(req)
		except urllib2.HttpError, e:
			print 'HTTP Error: %d' % e.code
			continue # skip this torrent
		except urllib2.URLError, e:
			print 'Network Error: %s' % e.reason.args[1]
			continue # skip this torrent
		if f.info().has_key('content-disposition'):
			filestr = escapeFilename(f.info()['content-disposition'].replace("inline; filename=\"",'').replace('"','')).replace('attachment__filename_','')
		else:
			filestr = basename(metainfo_name)
			pos = filestr.find('&')
			if pos > -1:
				eqpos = filestr.find('=',pos)+1 # drop =
				filestr = filestr[eqpos:]
			filestr = escapeFilename(unquote_plus(filestr))
		# write out to a local file
		of = open( filestr, "wb" )
		of.write( f.read() )
		of.close()
		metainfo_name = filestr

	# owners have to match
	if not isFileOwnerCurrentUser( metainfo_name ):
		print 'You do not own torrent \'%s\'' % metainfo_name
		continue

	metainfo_file = open(metainfo_name, 'rb')
	metainfo = bdecode(metainfo_file.read())
	metainfo_file.close()
	info = metainfo['info']
	info_hash = sha( bencode( info  ) ).hexdigest()

	data = userDataStore.createNewTorrent(path=os.path.abspath(metainfo_file), name=info['name'], hash=info_hash )

	# allowed tracker?
	if not dataStore.isTrackerAllowed( metainfo['announce'] ):
		print 'Tracker for \'%s\' is not allowed.' % info['name']
		continue

	if dataStore.isTorrentActive( data ):
		print 'A torrent the signature %s is already being downloaded' % info_hash
		continue

	## make sure we havent downloaded this already
	if dataStore.checkDownloadStatus( info_hash ) and not forceDownload:
		print "A torrent with the hash %s has already been downloaded." % info_hash
	else:	
		if info.has_key('length'):
		        fileSize = info['length']
		else:
		        fileSize = 0;
			for file in info['files']:
				fileSize += file['length']
	
		# filesize > disk free-10%?
		if fileSize > freeSpace:
			print "Sorry, not enough space for torrent %s!" % metainfo_name
		else:
			freeSpace -= fileSize
	
			# log the torrent info
			activateTorrent( dataStore=dataStore, userDataStore=userDataStore, userData=data )
			print 'Will begin downloading %s shortly.' % metainfo_name
userDataStore.save()
