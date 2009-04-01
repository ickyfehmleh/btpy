#!/usr/bin/python
#
# 1- fetch a certain url
# 2- compare contents of url to whats on disk
# 3- if contents are different/newer:
#    a- make new download file 
#    b- call rsync-ssh on each file (via popen)
#    c- email results to gmail account or write out a file and scp it back
# 4- if contents are same, do nothing
# 5- re-call ourself so we can continue monitoring
#
import sys
import urllib2
import time
import subprocess
import os.path
import ssh

SLEEP_TIME=120 # two minutes, should fill up logs anyway
PAUSE_TIME=60  # one minute to pause between rsync-ssh requests

ssh = ssh.Connection( 'hmsphx.com' )

def getTorrentFile(filename):
	printmsg( 'Now downloading: %s' % filename )
	##procArgs = ['ls', '-al', filename]
	procArgs = ['rsync', '-L', '--partial', '-e', 'ssh', '-r', '-v', 'hmsphx.com:' + filename, '.' ]
	p = subprocess.Popen( procArgs, stdout=subprocess.PIPE, stderr=subprocess.PIPE,close_fds=True )

	status = p.wait()

	output = p.stdout.readlines()
	rsyncTotal = output.pop()
	rsyncSent = output.pop()
	# get last 2 lines
	# sent 196 bytes  received 1602630887 bytes  135340.21 bytes/sec
	# total size is 1602434426  speedup is 1.00

	if status != 0:
		printmsg( 'Failed to execute rsync!' )
	else:
		rsyncSent = rsyncSent[:-1] # remove trailing \n
		printmsg( rsyncSent )
		printmsg( 'Fetched file %s' % filename )
		clearTorrentFile(filename)

def clearTorrentFile(filename):
	for line in ssh.execute('/share/torrents/bin/cleartorrents --torrent-list=~/files.to.get %s' % filename ):
		line = line[:-1]
		printmsg( line )

def printmsg(msg,showDate=True):
	if showDate:
		t = time.strftime( '%Y-%m-%d @ %I:%M:%S %p' )
		msg = '[%s]: %s' % (t, msg)
	print msg
	ssh.execute( 'echo "%s" >>~/fetched.files' % msg )

############################################################################
def process():
	ssh.get( 'files.to.get' )
	f = open( 'files.to.get', 'r' )
	
	for line in f.readlines():
		line = line[:-1]
		
		if len(line) > 0 and not (line == ''):
			getTorrentFile( line )
			#printmsg( 'Sleeping for %d seconds between requests...' % PAUSE_TIME )
		time.sleep( PAUSE_TIME )
	f.close()

	return True

############################################################################
cont = True

printmsg( 'Starting %s' % sys.argv[0] )

while cont:
	try:
		cont = process()
		#printmsg( 'Sleeping for %d seconds...' % SLEEP_TIME )
		time.sleep( SLEEP_TIME )
	except KeyboardInterrupt:
		cont = False
	#except:
	#	print 'Unhandled exception: ', sys.exc_info()
	#	cont = False

printmsg( 'Exiting gracefully!')
sys.exit()
