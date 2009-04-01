#!/usr/bin/python
#
# print defines from common.pyc
#
from common import *
ds = initDataStore()

print 'USER_DL_DIR == %s' % USER_DL_DIR
print 'EXPIRED_TORRENT_DIR == %s' % EXPIRED_TORRENT_DIR
print 'MAX_SLEEP_TIME == %s' % MAX_SLEEP_TIME
print 'PERCENT_KEEP_FREE == %s' % PERCENT_KEEP_FREE
print 'INCOMING_TORRENT_DIR == %s' % INCOMING_TORRENT_DIR
print 'COMPLETED_TORRENT_DIR == %s' % COMPLETED_TORRENT_DIR

print 'dataDir == %s ' % ds.dataDir()
print 'userDataStoreFile == %s' % ds.userDataStoreFile()
print 'torrentXML == %s' % ds.torrentXML()
print 'allowedTrackerList == %s' % ds.allowedTrackersList()
print 'autostopDir == %s' % ds.autostopDir()
print 'masterHashList == %s' % ds.masterHashList()
