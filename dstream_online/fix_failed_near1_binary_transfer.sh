#!/bin/bash
#./fix_failed_near1_binary_transfer.sh
#this script is here in order to fix the PUBS status for files that fail the near1 binary transfer
#failing to generate metadata from a binary files often happens when the file was transferred but
#but a timeout of some sort caused the ifdh transfer to report an error
#you must check that the file is already in SAM with a location before running this script.
#Running this command will correct all of the PUBS project statuses
#so that the run/subrun is no longer listed in the GUI. it will leave the binary near1 cleanup still
#with status 1 so that you won't forget to clean up the incomplete/dead binary file

if [ $# -lt 2 ]; then
    echo "Didn't provide a run and subrun number!!!"
    echo "Usage: fix_failed_metadata_gen_files.sh <run> <subrun>"
    exit 1
fi

RUN=$1
SUBRUN=$2

if [ -z "$PUB_TOP_DIR" ]; then
    echo "You have to setup pubs first!!!!!"
    exit 1
fi
echo ""
echo "Fixing the PUBS status for the near1 binary file associated with run = $RUN and subrun = $SUBRUN"
echo""
$PUB_TOP_DIR/dstream_online/correct_file_status.py prod_transfer_binary_near12dropbox_near1 160 1006 $RUN $SUBRUN
$PUB_TOP_DIR/dstream_online/correct_file_status.py prod_verify_binary_near12dropbox_near1 1 1004 $RUN $SUBRUN

echo "Finished processing all of the databases. Please double check that everything is updated."
