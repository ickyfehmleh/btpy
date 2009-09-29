#!/bin/sh
#
# remove expired torrents
#

#DAYS_OLD="14"
DAYS_OLD="5"

LOG="/share/incoming/.data/findexpired.log"

echo "=============================================================" >>$LOG
date >>$LOG

# wipe expired items that are >14 days old
/share/bin/findexpired $DAYS_OLD >>$LOG 2>>$LOG

# wipe torrents that have been stopped and are >14 days old
/share/bin/rm-inactive-torrents >>$LOG 2>>$LOG

# wipe torrent files that are inactive
/share/bin/rm-inactive-torrent-files >>$LOG 2>>$LOG
