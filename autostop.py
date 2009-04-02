#!/usr/bin/python
#
# auto stop a torrent
#

import sys
import getopt
from common import *
from xml.dom import minidom, Node
import glob

uid = os.getuid()

print ''

###################################################################################
#
def showAllRequests(torrentFileList):
	defaultRatio = None
	showHashes = False
	hashes = []

	if len(torrentFileList) > 0:
		print 'Showing matching requests for you:'
		showHashes = True
		for torrent in torrentFileList:
			info = infoFromTorrent(torrent)
			if info == '':
				continue
			hash = sha( bencode( info ) ).hexdigest()
			hashes.append( hash )
		if len(hashes) == 0:
			print 'No torrents listed could be found'
			return
	else:
		print 'Showing all requests for you:'


	for root, dir, files in os.walk( AUTOSTOPD_DIR ):
		for sf in files:
			stopFile = os.path.join( AUTOSTOPD_DIR, sf )

			if not stopFile.endswith( '.xml'):
				continue
			if os.stat(stopFile).st_uid != os.getuid():
				continue
			stopRatio = ratioFromAutostopFile( stopFile )

			if os.path.basename(stopFile) == str(os.getuid()) + '.xml':
				defaultRatio = stopRatio
			else:
				# find torrent with hash?
				thash = sf.split('.')[0]
				torrentFile = os.path.join( INCOMING_TORRENT_DIR, (thash + '.torrent') )
				info = infoFromTorrent( torrentFile )
				
				if info != '':
					if showHashes:
						if thash in hashes:
							print '\'%s\': %.2f' % (info['name'], stopRatio)
					else:
						print '\'%s\': %.2f' % (info['name'], stopRatio)
		if defaultRatio:
			print ''
			print 'Will stop all torrents at %.2f unless specified otherwise.' % defaultRatio
###################################################################################
# 
def createAutostopFile(autostopFile, hash=None):
	try:
		f = open( autostopFile, 'w' )
		f.write( '<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n' )
		f.write( '<autostop>\n' )
		f.write( '\t<stop>\n' )

		if hash:
			f.write( '\t\t<hash>%s</hash>\n' % hash )

		f.write( '\t\t<ratio>%s</ratio>\n' % ratioLevel )
		f.write( '\t</stop>\n' )
		f.write( '</autostop>\n' )
		f.close()
		os.chmod( autostopFile, 0640 )
	except:
		print 'Problem writing out this request!'
		raise

###################################################################################
#
def printUsageAndExit():
	print 'This will stop a torrent after a certain ratio is achieved.'
	print 'Usage: %s [-d] [-f] <ratio> <file1.torrent> ... <fileN.torrent>' % sys.argv[0]
	print '-d ==> delete a previous request for this torrent.'
	print '-f ==> overwrite another request if present.'
	print 'Optional: --all=<ratio> ==> Set default stop ratio for all torrents'
	exit(2)

try:
	opts,args = getopt.getopt( sys.argv[1:], 'dsf', ['force','delete','show-all','show','all='] )
except getopt.GetoptError:
	printUsageAndExit()

deleteExisting = False
ratioLevel = None
hash = None
forceOverwrite = False
showRequests = False

# stop on ratio?
for o,a in opts:
	if o in ('-d', '--delete'):
		deleteExisting = True
	if o in ('-f', '--force'):
		forceOverwrite = True
	if o in ('-s', '--show-all','--show'):
		showAllRequests(args)
		exit()
	if o == '--all':
		ratioLevel = 0.0

		try:
			ratioLevel = float(a)
		except:
			print 'Invalid number for default ratio!'
			exit(2)

		createAutostopFile( os.path.join( AUTOSTOPD_DIR, str(os.getuid()) ) + '.xml' )
		print 'Will stop ALL torrents after a ratio of %.2f has been achieved.' % (ratioLevel)
		print 'If a separate request is made for a torrent, that request overrides the default'
		exit()

if len(args) == 0 and showRequests == False:
	printUsageAndExit()

startArg = 1

if not deleteExisting:
	if len(args):
		try:
			ratioLevel = float(args[0])
		except:
			print 'Bad ratio, try using numbers.'
			exit(2)
	else:
		printUsageAndExit()
else:
	startArg = 0

for tfile in args[startArg:]:
	torrent = infoFromTorrent(tfile)
	if torrent == '':
		print 'Cannot find info on torrent %s' % tfile
		continue

	if not isFileOwnerCurrentUser(tfile):
		print 'You do not own %s' % tfile
		continue

	hash = sha( bencode( torrent ) ).hexdigest()
	autostopFile = os.path.join( AUTOSTOPD_DIR, hash )
	torrentName = torrent['name']

	autostopFile += '.xml'

	# make a request to autostopd
	if os.path.exists( autostopFile ) and not forceOverwrite:
		if deleteExisting:
			try:
				os.remove( autostopFile )
				print 'Request for %s removed!' % tfile
			except:
				print 'Problem removing request for torrent %s' % tfile
			continue
		else:
			print 'Already have a request for torrent %s, use -d to delete it.' % tfile
			continue
	else:
		if deleteExisting:
			print 'No request for %s found' % torrentName
			continue

		createAutostopFile(autostopFile, hash)

		print 'Will stop torrent %s at ratio %.2f.' % (torrentName, ratioLevel)
