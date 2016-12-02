#!/bin/bash
#./fix_failed_metadata_gen_files.sh
#this script is here in order to fix the PUBS status for files that fail the metadata generation
#failing to generate metadata from a binary files normally happens when the file doesn't have
#any complete files. So the file will have closed improperly during the writing of the first
#event coming out of the DAQ. Running this command will correct all of the PUBS project statuses
#so that the run/subrun is no longer listed in the GUI. it will leave the binary evb cleanup still
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
echo "Fixing the PUBS status for the dead file associated with run = $RUN and subrun = $SUBRUN"
echo""
$PUB_TOP_DIR/dstream_online/correct_file_status.py prod_binary_metadata_near1 120 0 $RUN $SUBRUN
$PUB_TOP_DIR/dstream_online/correct_file_status.py prod_register_binary_evb 1 0 $RUN $SUBRUN
$PUB_TOP_DIR/dstream_online/correct_file_status.py prod_transfer_binary_evb2dropbox_evb 1 1002 $RUN $SUBRUN
$PUB_TOP_DIR/dstream_online/correct_file_status.py prod_verify_binary_evb2dropbox_near1 1 1004 $RUN $SUBRUN
$PUB_TOP_DIR/dstream_online/correct_file_status.py prod_transfer_binary_evb2near1_near1 1 1006 $RUN $SUBRUN
$PUB_TOP_DIR/dstream_online/correct_file_status.py prod_transfer_binary_near12dropbox_near1 1 1006 $RUN $SUBRUN
$PUB_TOP_DIR/dstream_online/correct_file_status.py prod_verify_binary_near12dropbox_near1 1 1006 $RUN $SUBRUN
$PUB_TOP_DIR/dstream_online/correct_file_status.py prod_clean_near_binary_near1 1 1006 $RUN $SUBRUN

echo "Finished processing all of the databases. Please double check that everything is updated."
