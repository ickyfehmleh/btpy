#!/bin/sh
#
# wrapper around btdownloadcurses.py
#

#DISPLAY_INTERVAL="5"
DISPLAY_INTERVAL="3"
LOG="/share/incoming/.data/status.log"
ERROR_LOG="$LOG.ERROR"
TORRENT_XML="/share/incoming/.data/torrents.xml"
STOP_FLAG="N"

# permissions should do the same, but just in case: make sure
# only torrentuser can run this
if [ `id -u` -ne 1002 ]
then
        echo "You must be authorized to run this!"
        exit
fi

umask 0007

trap shutdownGracefully INT

runProcess()
{
	TORRENT_DIR="/share/incoming"
	BANDWIDTH="$1"
/share/torrents/bin/launchmanyxml \
$TORRENT_DIR \
--ip 67.222.150.58 \
--minport 7085 \
--maxport 7095 \
--max_upload_rate $BANDWIDTH \
--display_interval $DISPLAY_INTERVAL \
--alloc_type pre-allocate \
--saveas_style 3 \
--parse_dir_interval 15 \
--security 0 \
--alloc_rate 1 \
--crypto_allowed 1
}

logmsg()
{
	DATESTR=`date +"%Y-%m-%d @ %I:%M:%S %p"`
	MESSAGE="$DATESTR $1"
	echo $MESSAGE
	echo $MESSAGE >>$LOG
}

shutdownGracefully()
{
	STOP_FLAG="Y"
	logmsg "STOPPING GRACEFULLY"
}

if [ $# -eq 1 ]
then
	bandwidth=$1
else
	bandwidth="650"
fi

touch $TORRENT_XML
chmod 640 $TORRENT_XML

while [ "$STOP_FLAG" = "N" ]
do
	logmsg "Starting..."
	runProcess $bandwidth 2>>$ERROR_LOG
	sleep 5
	sync;sync
	logmsg "Restarting..."
done

logmsg "STOPPING GRACEFULLY"
