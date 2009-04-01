#!/bin/bash
#
# wholly revamped ~/bin/getfiles.sh
#

SCP_USER="howie"
#SCP_HOST="hmsphx.com"
SCP_HOST="72.232.49.178"

# ==========================================================================
OUTFILE=".getfiles"
INFILE="torrents.list"
FETCHED_FILES="~/.already_fetched_files"

SCPHOST="$SCP_USER@$SCP_HOST"

## trap ctrl-c
trap ctrl_c INT

function ctrl_c()
{
    echo ""
    echo "** Trapped CTRL-C, exiting!"
    exit
}

function logFile()
{
    file="$1"

    #echo "$file" >>$FETCHED_FILES
    #ssh $SCPHOST "echo \"$file\" >>$FETCHED_FILES"
    ssh $SCPHOST "/share/torrents/bin/cleartorrents $file"
}

function fileHasBeenDownloaded()
{
    file="$1"
    ## -x == match whole line
    ssh $SCPHOST "grep -x \"$file\" $FETCHED_FILES"

    #grep $file $HOME/$FETCHED_FILES
}

## get a remote file
function getRemoteFile()
{
	file="$1"

	echo ""
	echo "Now downloading $file"
	rsync -L --partial --progress --rsh=ssh --recursive $SCPHOST:$file .
}

## if we've not specified args, do everything normally
if [ $# -eq 0 ]
then
    echo "Fetching file listing..."
    ssh $SCPHOST "cat $INFILE" >$OUTFILE
    #ssh $SCPHOST "cp /dev/null $INFILE"
else
    echo "Processing files in \"$1\""
    OUTFILE="$1"
fi

if [ -s "$OUTFILE" ]
then
	for file in `cat $OUTFILE | grep -v ^\#`
	do
		LOCAL_FILE=`basename "$file"`
		HAS_BEEN_FETCHED=`fileHasBeenDownloaded "$file"`

		## make sure we havent completely fetched this file 
		## by checking our FETCHED_FILES list
		if [ -n "$HAS_BEEN_FETCHED" ]
		then
			## did we already grab this?
			if [ -e "$LOCAL_FILE" ]
			then
				## if file DOES exist locally, rsync just 
			        ## in case it's a partial
				echo "Already fetched $LOCAL_FILE, synchronizing..."
				getRemoteFile $file
			else
		                ## file does not exist locally but it's in our
			        ## processed list, assume it's been burned to
			        ## dvd
		    	        echo "Already seem to have fetched and processed $file, proceeding..."
			fi
		else
		    ## file does not exist locally
		    ## and it's not in our processed list
		    getRemoteFile $file
		    logFile $file
		fi
	done
fi

