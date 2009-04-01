#!/usr/bin/env python
#
# (1) get mdsum of torrent
# (2) make sure torrent isnt being grabbed already
# (3) mkdir /share/incoming/<mdsum>
# (4) make all appropriate dirs in mdsum dir
# (5) HARDLINK all appropriate files (see printlink)
# (6) copy .torrent file to /share/incoming/<mdsum>.torrent
# (7) make sure /share/incoming/mdsum.torrent is at least 644!
#

from sys import *
import os.path
from sha import *
from BitTornado.bencode import *
import statvfs
import os
from shutil import *

from common import *

print

if len(argv) == 1:
	print '%s file1.torrent file2.torrent file3.torrent ...' % argv[0]
	exit(2) # common exit code for syntax error

for metainfo_name in argv[1:]:
	info = infoFromTorrent( metainfo_name )
	info_hash = sha( bencode( info  ) )

	# figure out what to name the torrent
	torrentDir = os.path.join( INCOMING_TORRENT_DIR, info_hash.hexdigest() )
	torrentName = torrentDir + '.torrent'

	if isTorrentHashActive( info_hash):
		print "A torrent the signature %s is already being downloaded" % info_hash.hexdigest()
		continue
	else:
		# one file or multiple files?
		if info.has_key('length'):
			# mkdir, copy file into dir
			os.mkdir( torrentDir, 0755 )
			copy( info['name'], torrentDir )
			os.remove( info['name'] )
		else:
			# copy the dir over
			## VV FIXME: os.link() it! VV
			os.rename( info['name'], torrentDir )
			os.chmod( torrentDir, 0755 )		
		copy( metainfo_name, torrentName )
		os.chmod( torrentName, 0644 )

		print 'Will begin seeding %s shortly.' % metainfo_name
