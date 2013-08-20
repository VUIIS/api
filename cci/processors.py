import task
import os
import XnatUtils
from os.path import expanduser

USER_HOME = expanduser("~")
DEFAULT_MASIMATLAB_PATH = os.path.join(USER_HOME,'masimatlab')

class Processor(object):
    def __init__(self,walltime_str,memreq_mb,name):
        self.walltime_str=walltime_str # 00:00:00 format
        self.memreq_mb=memreq_mb  # memory required in megabytes      
        self.name=name 
    
    # can_run - does this object have the required inputs? e.g. NIFTI format of the required scan type and quality and are there no conflicting inputs, i.e. only 1 required by 2 found?
    def can_run(): # what other arguments here, could be Project/Subject/Session/Scan/Assessor depending on type of processor?
        raise NotImplementedError()
     
    # should_run - is the object of the proper object type? e.g. is it a scan? and is it the required scan type? e.g. is it a T1?
    def should_run(): # what other arguments here, could be Project/Subject/Session/Scan/Assessor depending on type of processor?
        raise NotImplementedError()
        
    def write_pbs(filename):
        raise NotImplementedError()

class ScanProcessor(Processor):
    def can_run():
        raise NotImplementedError()
     
    def should_run(): 
        raise NotImplementedError()
    
    def __init__(self,walltime_str,memreq_mb,name):
        super(ScanProcessor, self).__init__(walltime_str, memreq_mb, name)
         
    def get_assessor_name(self,scan):  
        proj_label = scan.parent().parent().parent().label()
        subj_label = scan.parent().parent().label()
        sess_label = scan.parent().label()
        scan_label = scan.label()
        
        return (proj_label+'-x-'+subj_label+'-x-'+sess_label+'-x-'+scan_label+'-x-'+self.name)
        
    def get_task(self, intf, scan_dict):
        scan = XnatUtils.get_full_object(intf,scan_dict)
        assessor_name = self.get_assessor_name(scan)
        assessor = scan.parent().assessor(assessor_name)
        if not assessor.exists():
            assessor.create(assessors='proc:genprocdata')
            assessor.attrs.set('proc:genprocdata/proctype', self.name)
            if self.can_run(scan):
                 assessor.attrs.set('proc:genprocdata/procstatus', task.READY_TO_RUN)
            else:
                 assessor.attrs.set('proc:genprocdata/procstatus', task.MISSING_INPUTS)
                 
        return task.Task(self,assessor)
        
class SessionProcessor(Processor):
    def can_run():
        raise NotImplementedError()
     
    def should_run(): 
        raise NotImplementedError()
    
    def __init__(self,walltime_str,memreq_mb,name):
        super(SessionProcessor, self).__init__(walltime_str,memreq_mb,name)
