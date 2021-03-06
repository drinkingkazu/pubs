## @namespace dstream_online.verify_dropbox
#  @ingroup verify_dropbox
#  @brief Defines a project verify_dropbox
#  @author kirby

# python include
import time, os, sys
# pub_dbi package include
from pub_dbi import DBException
# pub_util package include
from pub_util import pub_smtp
# dstream class include
from dstream import DSException
from dstream import ds_project_base
from dstream import ds_status
from ds_online_util import *
import samweb_cli
import traceback
import glob

pnfs_prefixes = {
   "/pnfs/cdfen": "srm://cdfdca1.fnal.gov:8443/srm/managerv2?SFN=",
   "/pnfs/dzero": "srm://d0ca1.fnal.gov:8443/srm/managerv2?SFN=",
   "/pnfs/": "srm://fndca1.fnal.gov:8443/srm/managerv2?SFN=",
}

BASE = 65521

def get_prefix( path ) :
    list = pnfs_prefixes.keys()
    list.sort(reverse=1)
    for prefix in list:
        if path.startswith(prefix):
            return pnfs_prefixes[prefix]
    raise LookupError("no server known for %s" % path)

def get_pnfs_1_adler32_and_size( path ):
    checksum = 0
    first = True
    cmd = "srmls -2 -l %s/pnfs/fnal.gov/usr/%s" % ( get_prefix(path), path[5:])
    #print "running: " , cmd
    pf = os.popen(cmd)
    for line in pf:
        #print "read: " , line
        if first:
            if line[-1] == '/' or line[-2] == '/':
                pf.close()
                raise LookupError('path is a directory: %s' % path)

            size = long(line[2:line.find('/')-1])
            first = False
            continue

        if line.find("Checksum value:") > 0:
            ssum = line[line.find(':') + 2:]
            #print "got string: ", ssum
            checksum = long( ssum , base = 16 )
            #print "got val: %lx" % checksum
            pf.close()
            return  checksum, size

    pf.close()
    raise LookupError("no checksum found for %s" % path)

def convert_0_adler32_to_1_adler32(crc, filesize):
    crc = long(crc)
    filesize = long(filesize)
    size = int(filesize % BASE)
    s1 = (crc & 0xffff)
    s2 = ((crc >> 16) &  0xffff)
    s1 = (s1 + 1) % BASE
    s2 = (size + s2) % BASE
    return (s2 << 16) + s1


class verify_dropbox( ds_project_base ):

    _project = 'verify_dropbox'


    ## @brief default ctor can take # runs to process for this instance
    def __init__( self, arg = '' ):

        # Call base class ctor
        super( verify_dropbox, self ).__init__( arg )

        if not arg:
            self.error('No project name specified!')
            raise Exception

        self._project = arg

        self._nruns = None
        self._in_dir = ''
        self._out_dir = ''
        self._infile_format = ''
        self._parent_project = []
        self._parent_status = []
        self._project_list = []
        self._project_requirement = []
        self._experts = ''
        self._data = ''
        self._min_run = 0

        self._success_status = kSTATUS_REMOVE_DATA
        self._sample_status  = None
        self._sample_modular = 0

        self._nskip = 0
        self._skip_ref_project = []
        self._skip_ref_status = None
        self._skip_status = None

    ## @brief method to retrieve the project resource information if not yet done
    def get_resource( self ):

        resource = self._api.get_resource( self._project )

        self._nruns = int(resource['NRUNS'])
        self._in_dir = '%s' % (resource['INDIR'])
        self._infile_format = resource['INFILE_FORMAT']
        self._out_dir = '%s' % (resource['OUTDIR'])
        self._ref_project = resource['REF_PROJECT']
        self._experts = resource['EXPERTS']
        try:
            self._parent_project = resource['PARENT_PROJECT'].split(':')
            self._parent_status  = []
            for x in resource['PARENT_STATUS'].split(':'):
                exec('self._parent_status.append(int(%s))' % x)
            if not len(self._parent_project) == len(self._parent_status):
                raise ValueError
        except Exception:
            self.error('Failed to load parent projects...')
            raise DSException

        exec('self._success_status=int(%s)' % resource['FINISHED_STATUS'] )
        exec('self._sample_status=int(%s)'  % resource['SAMPLE_STATUS']   )
        exec('self._sample_modular=int(%s)' % resource['SAMPLE_MODULAR']  )
        status_name(self._success_status)
        status_name(self._sample_status)
        
        #this constructs the list of projects and their status codes
        #we want the project to be status 1, while the dependent projects to
        # be status 0
        self._project_list = [self._project ]
        self._project_requirement = [ kSTATUS_INIT ]

        self._project_list += self._parent_project
        self._project_requirement += self._parent_status

        if 'MIN_RUN' in resource:
            self._min_run = int(resource['MIN_RUN'])

        if ( 'NSKIP' in resource and
             'SKIP_REF_PROJECT' in resource and
             'SKIP_REF_STATUS' in resource and
             'SKIP_STATUS' in resource ):
            self._nskip = int(resource['NSKIP'])
            self._skip_ref_project = resource['SKIP_REF_PROJECT']
            exec('self._skip_ref_status=int(%s)' % resource['SKIP_REF_STATUS'])
            exec('self._skip_status=int(%s)' % resource['SKIP_STATUS'])
            status_name(self._skip_ref_status)
            status_name(self._skip_status)

    ## @brief a function that should be used to set status
    def set_verify_status(self,run,subrun,status,data=''):

        status_name(status)

        self.log_status( ds_status( project = self._project,
                                    run = run,
                                    subrun = subrun,
                                    seq = 0,
                                    status = status,
                                    data = data ) )
            

    ## @brief calculate the checksum of a file
    def compare_dropbox_checksum( self ):
        
        # Attempt to connect DB. If failure, abort
        if not self.connect():
            self.error('Cannot connect to DB! Aborting...')
            return        
            
        # If resource info is not yet read-in, read in.
        if self._nruns is None:
            self.get_resource()

        if self._nskip and self._skip_ref_project:
            ctr = self._nskip
            for x in self.get_xtable_runs([self._project,self._skip_ref_project],
                                          [kSTATUS_INIT,self._skip_ref_status]):
                if ctr<=0: break
                self.set_verify_status( run     = int(x[0]),
                                        subrun  = int(x[1]),
                                        status  = self._skip_status) 
                ctr -= 1

            self._api.commit('DROP TABLE IF EXISTS temp%s' % self._project)
            self._api.commit('DROP TABLE IF EXISTS temp%s' % self._skip_ref_project)

        runlist_v = self.get_xtable_runs( self._project_list, self._project_requirement )

        self.compare_dropbox_checksum_from_runlist(runlist_v)

    ## @brief calculate the checksum of a file
    def compare_dropbox_checksum_from_runlist( self, runlist_v ):
        
        # Attempt to connect DB. If failure, abort
        if not self.connect():
            self.error('Cannot connect to DB! Aborting...')
            return

        # If resource info is not yet read-in, read in.
        if self._nruns is None:
            self.get_resource()

        # Fetch runs from DB and process for # runs specified for this instance.
        ctr = self._nruns

        # Array to hold a file location error
        locate_error_msg=''

        # Array to hold a checksum error
        checksum_error_msg=''
        sampled=False
        for i in xrange(len(runlist_v)):

            sampled=False
            if self._sample_modular and ( i % self._sample_modular == 0):
                sampled=True
            
            x = runlist_v[i]

            if ctr <= 0: break

            (run, subrun) = (int(x[0]), int(x[1]))
            if run < self._min_run: break

            # Counter decreases by 1
            ctr -= 1

            # Report starting
            self.info('Calculating the file checksum: run=%d, subrun=%d ...' % (run,subrun))

            statusCode = kSTATUS_INIT
            in_file_holder = '%s/%s' % (self._in_dir,self._infile_format % (run,subrun))
            filelist = glob.glob( in_file_holder )
            if (len(filelist)<1):
                self.error('Failed to find the file for (run,subrun) = %s @ %s !!!' % (run,subrun))
                self.set_verify_status( run     = run,
                                        subrun  = subrun,
                                        status  = kSTATUS_ERROR_INPUT_FILE_NOT_FOUND )
                continue

            if (len(filelist)>1):
                self.error('Found too many files for (run,subrun) = %s @ %s !!!' % (run,subrun))
                self.set_verify_status( run     = run,
                                        subrun  = subrun,
                                        status  = kSTATUS_ERROR_INPUT_FILE_NOT_UNIQUE )

            in_file = filelist[0]
            in_file_name = os.path.basename(in_file)
            out_file = '%s/%s' % ( self._out_dir, in_file_name )

            #Note that this has the sequence number hard coded as number 0
            RefStatus = self._api.get_status( ds_status(self._ref_project, run, subrun, 0))
            near1_checksum = RefStatus._data

            try:
                samweb = samweb_cli.SAMWebClient(experiment="uboone")
                meta = samweb.getMetadata(filenameorid=in_file_name)
                checksum_info = meta['checksum'][0].split(':')
                #self.warning("Found on tape %s" % in_file_name)
                if checksum_info[0] == 'enstore' and int(checksum_info[1]) == int(near1_checksum):
                    self._data = checksum_info[1]
                    statusCode = self._success_status
                    if sampled:
                        statusCode = self._sample_status
                else:
                    statusCode = kSTATUS_ERROR_CHECKSUM_MISMATCH

            except samweb_cli.exceptions.FileNotFound:
                locate_error_msg = 'File %s is not found at SAM!' % in_file
                statusCode = kSTATUS_INIT

                try:
                    pnfs_adler32_1, pnfs_size = get_pnfs_1_adler32_and_size( out_file )
                    near1_adler32_1 = convert_0_adler32_to_1_adler32(near1_checksum, pnfs_size)

                    if near1_adler32_1 == pnfs_adler32_1:
                        statusCode = self._success_status
                        if sampled:
                            statusCode = self._sample_status
                    else:
                        self.error('Found checksum disagreement @ (run,subrun) = (%d,%d)' % (run,subrun))
                        checksum_error_msg += 'Run %d, subrun %d\n' % ( run, subrun )
                        checksum_error_msg += 'Converted %s checksum: %s\n' % ( self._ref_project, near1_adler32_1 )
                        checksum_error_msg += 'Converted PNFS checksum: %s\n\n' % ( pnfs_adler32_1 )
                        statusCode = kSTATUS_ERROR_CHECKSUM_MISMATCH
                        self._data = '%s:%s;PNFS:%s' % ( self._ref_project, near1_adler32_1, pnfs_adler32_1 )

                except LookupError:
                    self.warning("Checksum check on dCache failed for %s" % out_file)

            # Create a status object to be logged to DB (if necessary)
            self.info('Finished: (run, subrun) = (%d,%d) status = %d' % (run,subrun,statusCode))
            self.set_verify_status( run     = run,
                                    subrun  = subrun,
                                    status  = statusCode,
                                    data    = self._data )

        # Report checksum error
        if checksum_error_msg:
            subject = 'Checksum different between %s and PNFS' % self._ref_project
            pub_smtp( os.environ['PUB_SMTP_ACCT'], 
                      os.environ['PUB_SMTP_SRVR'], 
                      os.environ['PUB_SMTP_PASS'], 
                      self._experts, subject, checksum_error_msg )
            
        if locate_error_msg:
            subject = 'Failed to locate file %s at SAM' % in_file
            pub_smtp( os.environ['PUB_SMTP_ACCT'], 
                      os.environ['PUB_SMTP_SRVR'], 
                      os.environ['PUB_SMTP_PASS'], 
                      self._experts, subject, locate_error_msg )


    ## @brief check the checksum is in the table
    def check_db( self ):
        # Attempt to connect DB. If failure, abort
        if not self.connect():
            self.error('Cannot connect to DB! Aborting...')
            return

        # If resource info is not yet read-in, read in.
        if self._nruns is None:
            self.get_resource()

        self.info('Here, self._nruns=%d ... ' % (self._nruns))

        # Fetch runs from DB and process for # runs specified for this instance.
        ctr = self._nruns
        for x in self.get_runs( self._project, 2 ):

            # Counter decreases by 1
            ctr -= 1

            (run, subrun) = (int(x[0]), int(x[1]))

            # Report starting
            self.info('Calculating the file checksum: run=%d, subrun=%d ...' % (run,subrun))

            statusCode = kSTATUS_TO_BE_VERIFIED
            in_file_name = self._infile_format % ( run, subrun )
            in_file = '%s/%s' % ( self._in_dir, in_file_name )

            # Get status object
            status = self._api.get_status(ds_status(self._project,
                                                    x[0],x[1],x[2]))

            self._data = status._data
            self._data = str( self._data )

            if self._data:
               statusCode = kSTATUS_DONE
            else:
                subject = 'Checksum of the file %s not in database' % in_file
                text = """File: %s
Checksum is not in database
                """ % ( in_file )

                pub_smtp( os.environ['PUB_SMTP_ACCT'], os.environ['PUB_SMTP_SRVR'], os.environ['PUB_SMTP_PASS'], self._experts, subject, text )

                statusCode = kSTATUS_ERROR_CHECKSUM_NOT_FOUND

            # Create a status object to be logged to DB (if necessary)
            self.set_verify_status( run     = run,
                                    subrun  = subrun,
                                    seq     = 0,
                                    status  = statusCode,
                                    data    = self._data )
            # Break from loop if counter became 0
            if not ctr: break


if __name__ == '__main__':

    proj_name = sys.argv[1]
        
    obj = verify_dropbox( proj_name )
        
    obj.info('Start project @ %s' % time.strftime('%Y-%m-%d %H:%M:%S'))

    if len(sys.argv) == 2:
        
        obj.compare_dropbox_checksum()
        
    elif len(sys.argv) == 3:

        runlist = open(sys.argv[2],'r').read()
        runid_v = []
        for line in runlist.split('\n'):
            words = line.split()
            if len(words) < 4:
                continue

            runid_v.append(int(words[0]),int(words[1]),int(words[2]),int(words[3]))
            
        obj.info('Run list fetched from txt file: %d entries' % len(runid_v))
        
        obj.compare_dropbox_checksum_from_runlist(runid_v)
        
    obj.info('End project @ %s' % time.strftime('%Y-%m-%d %H:%M:%S'))


