#!/usr/bin/python
#
# show info en-mass on torrents
#

from common import *
from TorrentStore import *
import getopt
import sys
import string

# setup args
try:
	opts, args = getopt.getopt(sys.argv[1:], 'ctnha', ['--contents', '--tracker', '--name', '--hash', '--all'] )
except getopt.GetoptError:
	print '%s file1.torrent [--tracker/-t] [--name/-n] [--hash/-h] [--all/-a] fileN.torrent' % sys.argv[0]
	sys.exit(2)

showTracker = False
showName = False
showHash = False
showContents = False

for opt,arg in opts:
	if opt in ("-t", "--tracker"):
		showTracker = True
	if opt in ("-n", "--name"):
		showName = True
	if opt in ("-h", "--hash"):
		showHash = True
	if opt in ('-c', '--contents'):
		showContents=True
	if opt in ("-a", "--all"):
		showTracker = True
		showName = True
		showHash = True
		showContents = True

if len(args) == 0:
	print '%s file1.torrent file2.torrent file3.torrent ...' % argv[0]
	exit(2)

ts = initTorrentStore()

for metainfo_name in args:
	print
	metainfo_file = open(metainfo_name, 'rb')
	metainfo = bdecode(metainfo_file.read())
	metainfo_file.close()
	info = metainfo['info']
	info_hash = hashFromInfo(info)

	if ts.isTorrentHashActive(info_hash):
		print '%s is a live torrent' % metainfo_name
	else:
		print '%s is a dead torrent' % metainfo_name

	if showHash:
		print 'Hash    : %s' % info_hash
	if showTracker:
		print 'Tracker : %s' % metainfo['announce']
	if showName:
		print 'Name    : %s' % info['name']
	if showContents:
		if info.has_key('length'):
			print 'Contents: %s [%d]' % (info['name'], info['length'])
		else:
			print 'Contents: '
			for file in info['files']:
				path = ''
				for item in file['path']:
					if (path != ''):
						path = path + "/"
					path = path + item
				fsize = human_readable(file['length'])
				print '        * %s [%s]' % (path, fsize)
