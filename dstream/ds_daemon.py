# Python include
import time, copy
from subprocess   import Popen, PIPE
# dstream include
from ds_exception import DSException
from ds_proc_base import ds_base
from ds_api       import ds_master
from ds_data      import ds_project
# pub_dbi package include
from pub_dbi      import pubdb_conn_info,DBException
# pub_util package include
from pub_util     import pub_logger
# dstream module include


class ds_action(ds_project):


    def __init__(self, project_info):

        if not isinstance(project_info,ds_project):
            raise ValueError

        self._info = copy.copy(project_info)
        self._proc = None

    def name(self): return self._name

    def active(self):
        if self._proc is None: return False
        else: return (self._proc.poll() is None)

    def clear(self):
        if self._proc is None: return (None,None)
        (out,err) = self._proc.communicate()
        del self._proc
        self._proc = None
        return (out,err)

    def execute(self):
        try:
            self._proc = Popen(self._info._command.split(None),
                               stdout = PIPE,
                               stderr = PIPE)
        except OSError as e:
            raise DSException()

class ds_daemon(ds_base):

    def __init__(self):

        super(ds_daemon,self).__init__()

        self._api = ds_master(pubdb_conn_info.writer_info(),
                              logger=self._logger)

        self._project_v  = {}
        self._exe_time_v = {}

        self._load_period = int(120)

    def load_projects(self):

        # First, remove project that is not active
        for x in self._project_v.keys():
            if not self._project_v[x].active():
                self._project_v.pop(x)

        # Second, load new/updated projects
        for x in self._api.list_projects():

            if x._project in self._project_v.keys():
                self.debug('Skipping update on project %s (still active)',x._project)
                continue

            self.debug('Updating project %s information' % x._project)
            self._project_v[x._project] = ds_action(x)
            if not x._project in self._exe_time_v:
                self._exe_time_v[x._project] = None

    def routine(self):

        ctr=0
        sleep=0
        while ctr >= 0 :

            ctr+=1
            time.sleep(1)
            now_str  = time.strftime('%Y-%m-%d %H:%M:%S')
            now_ts   = time.time()
            self.debug(now_str)
            
            if sleep: 
                sleep -=1
                continue

            try:
                self._api.connect()
            except DBException as e:
                self.error('Failed connection to DB @ %s ... Retry in 1 minute' % now_str)
                sleep = 60
                continue

            if (ctr-1) % self._load_period == 0:
                
                self.info('Routine project update @ %s ' % now_str)
                self.load_projects()

            for x in self._project_v.keys():

                proj_ptr = self._project_v[x]
                last_ts  = self._exe_time_v[x]

                if not proj_ptr.active():

                    (out,err) = proj_ptr.clear()

                    if out or err:

                        self.info('Finished project %s @ %s' % (x,now_str))
                        print out,err
                        
                    if ( last_ts is None or 
                         last_ts < ( now_ts - proj_ptr._info._period) ):
                        
                        try:
                            proj_ptr.execute()
                            self._exe_time_v[x] = now_ts
                        except OSError as e:
                            self.error('Error while executing a project %s @ %s' % (x,now_str))
                            self.error(e.strerror)


if __name__ == '__main__':
    k=ds_daemon()
    k.routine()
                    
                    
            


        

