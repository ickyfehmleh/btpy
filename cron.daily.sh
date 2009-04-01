#!/bin/sh
#
# remove 15-day-old expired torrents
#

#DAYS_OLD="10"
DAYS_OLD="14"

LOG="/var/log/findexpired.log"

echo "=============================================================" >>$LOG
date >>$LOG

# wipe expired items that are >14 days old
/share/torrents/bin/findexpired $DAYS_OLD >>$LOG 2>>$LOG

# wipe torrents that have been stopped and are >14 days old
/share/torrents/bin/rm-inactive-torrents >>$LOG 2>>$LOG

# wipe torrent files that are inactive
/share/torrents/bin/rm-inactive-torrent-files >>$LOG 2>>$LOG
