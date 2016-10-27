#! /usr/bin/env python
## @namespace dstream_online.get_metadata
#  @ingroup dstream_online
#  @brief Defines a project dstream_online.get_metadata
#  @author echurch, yuntse

# python include
import time, os, shutil, sys, gc
# pub_dbi package include
import datetime, json
import pdb
import subprocess
import glob
import copy
import samweb_cli

try:
    samweb = samweb_cli.SAMWebClient(experiment="uboone")
except:
    raise Exception('Not able to open up the SAMWeb Connection')

if len(sys.argv)<2 :
    print("\nMissing a query string to search for files!!")
    print("Usage: correct_metadata.py <file_query>\n")
    exit(1)

file_query=str(sys.argv[1])

if len(file_query)<2:
    print("\nError: file_query needs to have have something to if otherwise no files will be found!!!\n")
    exit(1)

list_o_files = samweb.listFiles(file_query)

#if len(list_o_files)> 1000:
#    print("\nError: Holy Cow!!! That's way too many files to process at one time. it's like %d files!!!\n" % len(list_o_files))
#    exit(1)

def _chunk(iterable, chunksize):
    """ Helper to divide an iterable into chunks of a given size """
    iterator = iter(iterable)
    from itertools import islice
    while True:
        l = list(islice(iterator, chunksize))
        if l: yield l
        else: return

for filenames in _chunk(list_o_files, 100):  
    mdlist = samweb.getMultipleMetadata(filenames)
    new_mdlist = []
    for md in mdlist:
        in_file = md['file_name']
        in_file_split = in_file.split('-')
        if in_file_split[0]=='PhysicsRun':
            run_type='physics'
        elif in_file_split[0]=='NoiseRun':
            run_type='noise'
        elif in_file_split[0]=='CalibrationRun':
            run_type='calibration'
        elif in_file_split[0]=='PMTCalibrationRun':
            run_type='pmtcalibration'
        elif in_file_split[0]=='TPCCalibrationRun':
            run_type='tpccalibration'
        elif in_file_split[0]=='LaserCalibrationRun':
            run_type='lasercalibration'
        elif in_file_split[0]=='BeamOffRun':
            run_type='beamoff'
        elif in_file_split[0]=='BeamOff':
            run_type='beamoff'
        elif in_file_split[0]=='TestRun':
            run_type='test'
        else:
            run_type='unknown'

        new_md = { 'file_name' : in_file, 'runs' : copy.deepcopy(md['runs']) }
        if new_md['runs']:
            for run in new_md['runs']:
                run[2]=run_type
            new_mdlist.append(new_md)

    if new_mdlist:
        print new_mdlist
        # This should be a proper api call, but currently it isn't
        #samweb.putURL('/files', params={'continue_on_error': 0}, data=json.dumps(new_mdlist), content_type='application/json', secure=True, role='*')

print("Finished processing files for this query: %s" % file_query)

exit(0)
