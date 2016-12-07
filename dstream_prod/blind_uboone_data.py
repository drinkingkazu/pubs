#! /usr/bin/env python
## @namespace blind_uboone_data
#  @ingroup dstream_prod
# Author: Kirby Nov 29, 2016
# Purpose: This python script is designed to set the r/w status of all files at MicroBooNE that contain BNB data
#          to unreadable by analyzers. It queries the SAM database for a run range of files from the command line for:
#          binary, swizzled, reco, and anatree categories of files.
#          Note that there is an optional fraction of files to be left readable by analyzers and it will not process
#          files that have already been processed. Therefore, there will not be any double fraction of open files.
# Note that you need to have a proxy in the environment if you want to change the metadata
# You'll probably need something like: export X509_USER_PROXY=/opt/uboonepro/uboonepro.Production.proxy"

# python include
import time, os, shutil, sys, gc
# pub_dbi package include
import datetime, json, time
import random
import pdb
import subprocess
import glob
import copy
import samweb_cli

#def _construct_directory(base_directory,run_number_tmp):
#    if type(run_number)!=<type 'int'>:
#        print "bad run_number in the range! Not an integer!"
#        exit(1)
#    else:
#        run_number_tmp_str=format(run_nubmer_tmp,'08')
#        run_directory=base_directory+'*/'+run_number_tmp_str[0:2]+'/'+run_number_tmp_str[2:4]+'/'+run_number_tmp_str[4:6]+'/'+run_number_tmp_str[6:8]+'/'
#        return run_directory

def _chunk(iterable, chunksize):
    """ Helper to divide an iterable into chunks of a given size """
    iterator = iter(iterable)
    from itertools import islice
    while True:
        l = list(islice(iterator, chunksize))
        if l: yield l
        else: return

try:
    samweb = samweb_cli.SAMWebClient(experiment="uboone")
except:
    raise Exception('Not able to open up the SAMWeb Connection')

if len(sys.argv)<3 :
    print("\nMissing the needed input variables for blinding of data!!!\n")
    print("Usage: blind_uboone_data.py <binary|swizzled|reco|anatree> <lower_run_limit> [upper_run_limit] [fraction_for_unblind] [reprocess_old_files]\n")
    print("You have to give a lower limit to the files you want to blind, and possibly an upper limit.")
    print("The fraction_for_unblind is an optional integer percentage to leave unblind.")
    print("Files marked with ub_blinding.processed: true with only be processed if you set [reprocess_old_files] to true.")
    exit(1)

if len(sys.argv)>6 :
    print("\nMissing the needed input variables for blinding of data!!!\n")
    print("Usage: blind_uboone_data.py <binary|swizzled|reco|anatree> <lower_run_limit> [upper_run_limit] [fraction_for_unblind] [reprocess_old_files]\n")
    print("You have to give a lower limit to the files you want to blind, and possibly an upper limit. upper limit is not included!")
    print("The last fraction is what percentage to leave open one is optional.")
    print("Files marked with ub_blinding.processed: true with only be processed if you set [reprocess_old_files] to true.")
    exit(1)

unblinding_fraction=0
reprocess_old_files=False

data_tier=str(sys.argv[1])
lower_run_limit=int(sys.argv[2])
open_run_list = " minus (run_number 5121, 5122, 5124, 5125, 5127, 5128, 5130, 5643, 5134, 5647, 5136, 5720, 5138, 5653, 5142, 5655, 5656, 5146, 5147, 5151, 5153, 5154, 5155, 5157, 5160, 5161, 5162, 5164, 5167, 5168, 5169, 5170, 5171, 5684, 5726, 5385, 5176, 5177, 5179, 5181, 5694, 5695, 5184, 5185, 5187, 5189, 5191, 5192, 5705, 5194, 5195, 5708, 5197, 5710, 5712, 5713, 5203, 5204, 5718, 5719, 5208, 5722, 5211, 5724, 5725, 5214, 5215, 5216, 5729, 5730, 5731, 5733, 5393, 5226, 5229, 5565, 5233, 5235, 5748, 5237, 5239, 5755, 5756, 5758, 5397, 5761, 5762, 5511, 5654, 5766, 5767, 5769, 5771, 5772, 5262, 5263, 5776, 5777, 5266, 5779, 5781, 5270, 5783, 5272, 5273, 5597, 5275, 5277, 5278, 5280, 5281, 5804, 5805, 5806, 5808, 5809, 5810, 5583, 5819, 5820, 5821, 5822, 5823, 5824, 5825, 5826, 5315, 5829, 5830, 5831, 5832, 5411, 5322, 5326, 5839, 5328, 5329, 5650, 5331, 5332, 5333, 5334, 5847, 5849, 5338, 5851, 5340, 5343, 5344, 5463, 5860, 5864, 5353, 5354, 5870, 5360, 5361, 5362, 5363, 5364, 5365, 5366, 5367, 5368, 5881, 5370, 5371, 5885, 5374, 5375, 5376, 5377, 5891, 5892, 5382, 5895, 5384, 5897, 5703, 5899, 5390, 5391, 5392, 5905, 5394, 5909, 5910, 5399, 5912, 5401, 5914, 5403, 5916, 5850, 5918, 5765, 5408, 5409, 5339, 5412, 5925, 5425, 5929, 5418, 5419, 5932, 5933, 5935, 5424, 5937, 5938, 5427, 5940, 5941, 5942, 5924, 5432, 5428, 5946, 5436, 5437, 5440, 5442, 5515, 5444, 5430, 5450, 5451, 5452, 5517, 5923, 5459, 5774, 5462, 5433, 5464, 5470, 5474, 5691, 5478, 5480, 5906, 5482, 5485, 5509, 5693, 5489, 5490, 5921, 5493, 5495, 5497, 5498, 5499, 5500, 5501, 5741, 5504, 5506, 5507, 5508, 5782, 5697, 5512, 5513, 5271, 5516, 5904, 5518, 5519, 5520, 5521, 5522, 5523, 5525, 5526, 5527, 5528, 5531, 5532, 5533, 5445, 5536, 5539, 5540, 5541, 5930, 5896, 5845, 5487, 5557, 5558, 5561, 5564, 5706, 5566, 5877, 5569, 5878, 5879, 5581, 5709, 5880, 5586, 5588, 5589, 5778, 5593, 5567, 5598, 5601, 5606, 5607, 5608, 5609, 5614, 5617, 5827, 5886)"

run_limit_str = " run_number >= " + str(lower_run_limit) + " "
if len(sys.argv)>3 :
    upper_run_limit=int(sys.argv[3])
    run_limit_str = run_limit_str + "and run_number <= " + str(upper_run_limit) + " "
    list_o_runs = range(lower_run_limit,upper_run_limit)
    if len(list_o_runs)<1:
        print("\n The lower and upper run limits given didn't produce any runs to process.\n")
        print("Usage: blind_uboone_data.py <binary|swizzled|reco|anatree> <lower_run_limit> [upper_run_limit] [fraction_for_unblind] [reprocess_old_files]\n")
        exit(1)

if len(sys.argv)>4 :
    unblinding_fraction=int(sys.argv[4])
if len(sys.argv)>5 :
    if (sys.argv[5]=='true') :
        reprocess_old_files=True
    elif (sys.argv[5]=='false') :
        reprocess_old_files=False
    else :
        print("That wasn't true or false!!!" + sys.argv[5])
        exit(1)


list_o_files = []
check_file_age=False

if data_tier=="binary" :
    query = run_limit_str + " and file_type data and data_tier raw and file_format binary% and file_name Phys%" + open_run_list
    try:
        list_o_files=samweb.listFiles(query)
    except:
        raise Exception('Unable to get list of files for this query:' + query)
    check_file_age=True
elif data_tier=="swizzled" :
    query = run_limit_str + " and file_type data and data_tier raw and file_format artroot and data_stream outbnb% and file_name Phys% "
    try:
        list_o_files=samweb.listFiles(query)
    except:
        raise Exception('Unable to get list of files for this query:' + query)
elif data_tier=="reco" :
    query = run_limit_str + " and file_type data and data_tier reco% and file_format artroot and file_name Phys% and ub_project.name reco_outbnb%"
    try:
        list_o_files=samweb.listFiles(query)
    except:
        raise Exception('Unable to get list of files for this query:' + query)
elif data_tier=="anatree" :
    query = run_limit_str + " and file_type data and data_tier root-tuple and file_name ana% and ub_project.name anatree_outbnb%"
    try:
        list_o_files=samweb.listFiles(query)
    except:
        raise Exception('Unable to get list of files for this query:' + query)
elif data_tier=="test" :
    query = run_limit_str + " and file_name BeamOffRun-2016_5_11_8_8_51-0006268-00008.ubdaq"
    try:
        list_o_files=samweb.listFiles(query)
    except:
        raise Exception('Unable to get list of files for this query:' + query)
else :
    print("listed data tier doesn't match binary|swizzled|reco|anatree!!!!!!")
    exit(1)

if len(list_o_files)<1:
    print("\nThere were no files found matching that query!")
    print("Finished processing files for this query: %s" % query)
    exit(1)

for filenames in _chunk(list_o_files, 100):
    
    mdlist = samweb.getMultipleMetadata(filenames)
    new_mdlist = []
    for md in mdlist:
        if ( ('ub_blinding.processed' in md) and (md['ub_blinding.processed']=='true') and not reprocess_old_files ):
            print("\nCommand line flag: <reprocess_old_files> not set!!!\n")
            print("So cowardly refusing to reprocessing file: " + md['file_name']+"\n")
            continue
        in_file = md['file_name']
        try:
            location=samweb.locateFile(in_file)
        except:
            raise Exception('No location available for file: '+in_file)

        file_full_path_tmp=(location[0]['full_path'].split(":"))[1]+"/"+in_file
        if not (os.path.exists(file_full_path_tmp)) :
            print("The file location return from SAM doesn't exist on this machine!!!")
            print("The location from was: "+file_full_path_tmp)
            print("Skipping this file and not modifying the metadata.")
            continue
        #print(file_full_path_tmp)
        
        if ( (md['data_tier']=="raw") and ((time.time() - os.path.getmtime(file_full_path_tmp)) < 172800) ) :
            print("The binary file isn't old enough to blind: "+file_full_path_tmp)
            print("This raw data file was younger than the 48 hour limit requested by the operations group.")
            print("I'm not going to throw a random number to unblind the file, so marked it as ub_blinding.processed: false")
            new_md = { 'file_name' : in_file, 'ub_blinding.processed' : 'false', 'ub_blinding.blind' : 'false' }
            new_mdlist.append(new_md)
            continue

        if (random.uniform(0.00000001,100)<unblinding_fraction) :
            cmd = "chmod 0644 " + file_full_path_tmp

            print("I would change that file to be NOT-BLIND.")
            print("Would execute this command: " + cmd)
                  
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in p.stdout.readlines():
                print line,
            retval = p.wait()
            if (retval):
                print("There was an error trying to change the permissions of file "+file_full_path_tmp)
                continue
            
            new_md = { 'file_name' : in_file, 'ub_blinding.processed' : 'true', 'ub_blinding.blind' : 'false' }
            new_mdlist.append(new_md)
        else:
            cmd = "chmod 0600 " + file_full_path_tmp

            print("I would change that file to be BLIND.")
            print("Would execute this command: " + cmd)

            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in p.stdout.readlines():
                print line,
            retval = p.wait()
            if (retval):
                print("There was an error trying to change the permissions of file "+file_full_path_tmp)
                continue

            new_md = { 'file_name' : in_file, 'ub_blinding.processed' : 'true', 'ub_blinding.blind' : 'true' }
            new_mdlist.append(new_md)

    if new_mdlist:
        print new_mdlist
        # This should be a proper api call, but currently it isn't
        try:
            samweb.putURL('/files', params={'continue_on_error': 0}, data=json.dumps(new_mdlist), content_type='application/json', secure=True, role='*')
        except:
            print("\nThere was an error trying to access the ")
            print("You probably don't have a proxy available!!!")
            print("Try something like: export X509_USER_PROXY=/opt/uboonepro/uboonepro.Production.proxy")
            raise Exception('Exception trying to update the metadata of processed files!!!')

print("Finished processing files for this query: %s" % query)

exit(0)
