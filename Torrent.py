# 
# representation of a torrent file
#

import os.path

class Torrent:
	#__slots__

	def __init__(self,fileName):
		self.fileName = os.path.abspath(fileName)
		## FIXME fetch all data from torrent

	def announceURL(self):
	def filesInTorrent(self):
	def infoHash(self):
	def archiveSize(self):
	def fileName(self):
		return self.fileName

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
