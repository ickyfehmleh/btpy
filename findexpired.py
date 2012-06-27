#!/usr/local/bin/python
#
# find torrents >15 days
#

from sys import *
from os.path import *
import os
from shutil import *
import datetime
import time
from common import *
import getopt

########################################################################
# delete a dir hierarchy
def deleteDownloadedTorrent(dir):
	if os.path.isfile(dir):
		os.unlink(dir)
	else:
		for root, dirs, files in os.walk(dir):
			for currentDir in dirs:
				deleteDownloadedTorrent(os.path.join( dir, currentDir ) )
			for currentFile in files:
				fullFilePath = os.path.join( dir, currentFile )
				os.remove( fullFilePath )
		os.rmdir( dir )

########################################################################
# find a string in a file
def fileNameExistsInFile(fname,readFile):
	try:
		fn = open( readFile, 'r' )
	except:
		#print 'Cant open %s' % readFile
		# if we can't open torrents.list, dont bother
		return False
	
	for line in fn:
		line = line[:-1]
		if basename(line) == fname:
			fn.close()
			return True
	fn.close()
	return False

########################################################################
# stat()s a dir/file, checks to see if its older than n number of days
def isFileOld(fn, daysOld=15):
	stats = os.stat(fn)
	lastmod = datetime.date.fromtimestamp(stats[8])
	today = datetime.date.today()
	oldTime = today + datetime.timedelta(days=-1 * daysOld)
	rv = oldTime > lastmod
	#print 'isFileOld(%s,%d): %s' % (fn,daysOld, rv)
	return rv

########################################################################
# find old files
def findOldTorrents(rootdir,daysOld=15):
	oldFiles=[]

	for root, dirs, files in os.walk(rootdir):
		for currentDir in dirs:
			fn = os.path.join(root,currentDir)
			if isFileOld( fn,daysOld ):
				#print '%s' % fn
				oldFiles.append( fn )

		for currentFile in files:
			if not currentFile.startswith('.'):
				fn = os.path.join(root, currentFile)
				if isFileOld( fn, daysOld ):
					oldFiles.append( fn )
	return oldFiles
########################################################################
# main 
####
# 1- walk through /share/expired
# 2- find files older than n number of days
# 3- make sure basename(torrentname) is not in someone's torrents.list file
# 4- if it is, make a note
# 5- if it is not, delete the torrent

if os.getuid() > 0:
	print 'Only root can run this!'
	exit()

doDelete=True
oldtime=15

try:
	opts, args = getopt.getopt(argv[1:], None, ['dry-run','time='])
except getopt.GetoptError:
	print 'Usage: %s [args] <directory>' % argv[0]
	print '--dry-run => Don\'t delete files'
	print '--time => Specify days to remove'
	exit(2)

for opt,arg in opts:
	if opt == '--dry-run':
		doDelete=False
	if opt == '--time':
		oldtime=int(arg)

# first arg == dir to scan
if len(args) == 0:
	print 'USAGE: %s <dir name>' % argv[0]
	exit(2)

rootDirectoryToScan=args[0]

oldies = findOldTorrents( rootDirectoryToScan, oldtime )

for old in oldies:
	if os.path.exists(old):
		if doDelete == True:
			deleteDownloadedTorrent(old)
			print 'Removed: %s' % old
		else:
			print 'Found: %s' % old
