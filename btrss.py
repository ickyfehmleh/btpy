#!/usr/bin/env python
#############################################################################
# FIXME can urllib2 handle redirects by default?
# FIXME really need all these imports?
#############################################################################
# TODO gnu_getopt() ?
# TODO cache interests when starting, lots of file i/o parsing the file each 
#      and every time
# TODO reverse methology: loop thru contents of interest file looking for 
#      matches in the RSS, not vice versa
# TODO rely on BitTorrent libs, not BitTornado's
# TODO handle 302 redirects?
# TODO add exclusionary file (eg dont download *-MOBILE) ?
# TODO checkInterestForTitle() should return the string that matches the 
#      torrent; makes for easily saying "Matched RSSITEM from INTEREST_STR"
#############################################################################
#
# FIXME make sure URLs have ' ' replaced with '%20': 
#
#############################################################################

import sys
import cookielib
import urllib2
from urllib import unquote_plus
import feedparser
import re
import os
import os.path
import string
from sha import *
from BitTornado.bencode import *
import shutil
import tempfile
import getopt
import time

USER_AGENT='Mozilla/4.0 (compatible; btrss-python v1.5; talk to likeomglol@gmail.com if this is a problem)'
DATA_FILE=os.path.join( os.environ['HOME'], '.btrss', 'btrss.dat')
COOKIE_FILE=os.path.join( os.environ['HOME'], '.btrss', 'cookies.txt')
BE_VERBOSE=False

########################################################################
# expand a filename
def expandFilename(fileName):
	return os.path.expandvars(os.path.expanduser(fileName))

########################################################################
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
########################################################################
# make a note that we've downloaded a hash, rss item, and url
def logTorrent(hash,title,url):
	t = time.strftime( '%Y-%m-%d %I:%M:%S %P' ) 
	logStr = "%s:%s:%s:%s" % (hash, t, title,url)

	printdebug('Writing info to DATA_FILE %s' % DATA_FILE )
	
	df = open( DATA_FILE, 'a' )
	df.write( logStr )
	df.write( '\n' )
	df.close()

########################################################################
# print a log line
def printdebug(str):
	if BE_VERBOSE:
		printmsg( str )

def printmsg(msg,showDate=True):
	app=os.path.basename(sys.argv[0])

	if showDate:
		t = time.strftime( '%Y-%m-%d @ %I:%M:%S %P' )
		print '[%s]: %s' % (t, msg)
	else:
		print msg

########################################################################
# escape a filename
def escapeFilename(s):
	return re.sub("[^A-Za-z0-9\-\.]", "_", s)

########################################################################
#
def fetchFileFromURL(url,writeToDir=None,headers=None):
	# make an http request
	try:
		req = urllib2.Request(url, None, headers)
		f = urllib2.urlopen(req)
	except urllib2.HTTPError, e:
		printmsg( 'HTTP Error accessing %s: %d' % (url, e.code ) )
		return ''
	except urllib2.URLError, e:
		printmsg( 'Network Error accessing %s: %s' % (url,e.reason.args[1] ) )
		return ''

	if f.info().has_key('content-disposition'):
		filestr = escapeFilename(f.info()['content-disposition'].replace("inline; filename=\"",'').replace('"','')).replace('attachment__filename_','')
	else:
		filestr = escapeFilename(unquote_plus(os.path.basename(url)))

	# write out to a local file
	if writeToDir:
		outfile = os.path.join(writeToDir, filestr)
	else:
		outfile = filestr

	of = open(outfile, "wb")
	of.write( f.read() )
	of.close()
	f.close()

	return filestr
########################################################################
# function to check if the title matches an interest
def checkInterestForTitle( title, interestFile ):
	fn = open( interestFile, 'r' )

	for line in fn.readlines():
		if not line.startswith('#') and len(line) > 0:
			line = line[:-1]
			if re.search(line, title, re.IGNORECASE):
				printdebug( 'Matched interest \'%s\'' % line )
				fn.close()
				return True

	fn.close()
	return False

########################################################################
# get metainfo from a given torrent
def infoHashFromTorrent(fn):
	try:
		metainfo_file = open(fn, 'rb')
		metainfo = bdecode(metainfo_file.read())
		metainfo_file.close()
		info = metainfo['info']
		info_hash = sha( bencode( info ) ).hexdigest()
		return info_hash
	except:
		return ''

########################################################################
# function to see if we've already grabbed the hash
def checkDownloadStatusForURL( url ):
	torrentLog = open( DATA_FILE, 'r')
	lines = torrentLog.readlines()
	torrentLog.close()

	for line in lines:
		line = line[:-1] # trim newline
		splitLine = line.split( ':' )
		fetchedURL = string.join(splitLine[-2:], ':')
		if fetchedURL == url:
			return True

	return False
########################################################################
# should really be combined with the above method i think
def checkDownloadStatusForHash(hash):
	torrentLog = open( DATA_FILE, 'r')
	lines = torrentLog.readlines()
	torrentLog.close()

	for line in lines:
		splitLine = line.split( ':' )
		fetchedHash = splitLine[0]

		if fetchedHash == hash:
			return True
	return False
########################################################################
# cleanup temp dir
def cleanupAndExit(dir=None):
	if dir:
		shutil.rmtree(dir)
	sys.exit()
########################################################################
# usage
def printUsageAndExit(appName):
	print "Usage: %s <url> <interest file> <output path>" % appName
	print "Optional arguments: "
	print "   --cookie=<path to cookies.txt>"
	print "   --data=<path to data>"
	print "   -v/--verbose"
	cleanupAndExit()

########################################################################
# main method

# setup args
try:
	opts, args = getopt.getopt(sys.argv[1:], 'v', ['cookie=','data=','--verbose'])
except getopt.GetoptError:
	printUsageAndExit(sys.argv[0])

if len(args) != 3:
	printUsageAndExit(sys.argv[0])

for o, a in opts:
	if o == "-v" or o == "--verbose":
		BE_VERBOSE=True
	elif o == "--cookie":
		COOKIE_FILE=expandFilename(a)
	elif o == "--data":
		DATA_FILE=expandFilename(a)

rssURL = args[0]
interestFile = expandFilename(args[1])
btDownloadDir = expandFilename(args[2])

printdebug( 'Using %s as the RSS URL' % rssURL )
printdebug( 'Using %s as the interest file' % interestFile )
printdebug( 'Using %s as the output dir' % btDownloadDir )
printdebug( 'Using %s as the cookies file' % COOKIE_FILE )
printdebug( 'Using %s as the data file' % DATA_FILE )

## make sure things exist
if isFileReadable( COOKIE_FILE ):
	cj = cookielib.MozillaCookieJar()
	try:
		cj.load( COOKIE_FILE )
	except:
		printmsg( 'Cookie file %s could not be loaded' % COOKIE_FILE )
		cleanupAndExit()
	opener = urllib2.build_opener( urllib2.HTTPCookieProcessor( cj ) )
	urllib2.install_opener( opener )
else:
	printmsg( 'Cannot find/read cookie file %s' % COOKIE_FILE )
	cleanupAndExit()

if not os.path.exists( DATA_FILE ):
	# create one quickly
	try:
		f = open( DATA_FILE, "w" )
	except:
		printmsg( 'Failed to create %s' % DATA_FILE )
		cleanupAndExit()
	f.close()

if not isFileReadable( interestFile ):
	printmsg( 'Cannot read interest file %s' % interestFile )
	cleanupAndExit()

if not isDirectoryWriteable( btDownloadDir ):
	printmsg( '%s does not exist or cannot be written to' % btDownloadDir )
	cleanupAndExit()

httpHeaders = {'User-Agent' : USER_AGENT}

printdebug('')

# grab rss feed; feedparser wont use our opener so lets fetch it ourselves...
try:
	f = None
	if rssURL.startswith('http:') or rssURL.startswith('https:'):
		req = urllib2.Request(rssURL, None, httpHeaders)
		f = urllib2.urlopen(req)
	else:
		f = open(rssURL,'r')
except urllib2.HTTPError, e:
	printmsg( 'HTTP Error accessing %s: %d' % (rssURL,e.code ))
	cleanupAndExit()
except urllib2.URLError, e:
	printmsg( 'Network Error accessing %s: %s' % (rssURL,e.reason.args[1] ) )
	cleanupAndExit()

feed = feedparser.parse( f.read() )
f.close()

printdebug( 'Processing feed %s' % feed.feed.title )
btTempDownloadDir = tempfile.mkdtemp('btrss')

# loop through rss feed's items
for rssItem in feed['entries']:
	if rssItem['link'].startswith( 'http://' ):
		torrentLink = rssItem['link']
	elif rssItem['link'].startswith( 'https://' ):
		torrentLink = rssItem['link']

	## FIXME is this needed?
	torrentLink = unquote_plus(torrentLink)

	# check interest in current rssItem's title
	if checkInterestForTitle( rssItem['title'], interestFile):
		# make sure we havent fetched from this url before
		# as to not artificially inflate interest in torrent
		if checkDownloadStatusForURL(torrentLink):
			printdebug( 'Already fetched %s' % torrentLink )
		else:
			printdebug( 'Downloading  \'%s\'' % rssItem['title'] )

			fetchedTorrent = fetchFileFromURL(torrentLink,headers=httpHeaders,writeToDir=btTempDownloadDir)

			# did we grab this hash already?
			torrentHash = infoHashFromTorrent(os.path.join(btTempDownloadDir,fetchedTorrent))

			if checkDownloadStatusForHash(torrentHash):
				printdebug( 'Already downloaded this torrent' )
				# note that we've already got this one so we 
				# dont fetch again
				logTorrent(torrentHash,rssItem['title'],torrentLink)
			else:
				printmsg( 'Feed: %s -- Downloading \'%s\' from thread \'%s\'' % ( feed.feed.title, fetchedTorrent, rssItem['title']) )
				## move file from temp dir to real dl dir
				tmpfile=os.path.join(btTempDownloadDir, fetchedTorrent)
				outfile=os.path.join(btDownloadDir,fetchedTorrent)
				shutil.move(tmpfile, outfile)
				## log that we've fetched this torrent
				logTorrent(torrentHash,rssItem['title'],torrentLink)

cleanupAndExit(btTempDownloadDir)
