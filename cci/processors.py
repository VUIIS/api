import task
import os,re
import XnatUtils
from os.path import expanduser
from datetime import datetime

USER_HOME = expanduser("~")
DEFAULT_MASIMATLAB_PATH = os.path.join(USER_HOME,'masimatlab')

class Processor(object):
    def __init__(self,walltime_str,memreq_mb,spider_path,ppn=1,xsitype='proc:genProcData'):
        self.walltime_str=walltime_str # 00:00:00 format
        self.memreq_mb=memreq_mb  # memory required in megabytes      
        self.spider_path=spider_path
        self.ppn = ppn
        self.xsitype = xsitype
        set_spider_info()
    
    #set information coming from the spider_path
    def set_spider_info(self):
        #Name is the procname with the X version (major version) and version has all the version in it
        if len(re.split("/*_v[0-9]/*", self.spider_path))>1:
            self.version = os.path.basename(self.spider_path)[7:-3].split('_v')[-1]
            self.name = os.path.basename(self.spider_path)[7:-3].split('_v')[0] +'_v'+ self.version.split('.')[0]
        else:
            self.version = '1.0.0'
            self.name = os.path.basename(self.spider_path)[7:-3]

    # has_inputs - does this object have the required inputs? e.g. NIFTI format of the required scan type and quality and are there no conflicting inputs, i.e. only 1 required by 2 found?
    def has_inputs(): # what other arguments here, could be Project/Subject/Session/Scan/Assessor depending on type of processor?
        raise NotImplementedError()
     
    # should_run - is the object of the proper object type? e.g. is it a scan? and is it the required scan type? e.g. is it a T1?
    def should_run(): # what other arguments here, could be Project/Subject/Session/Scan/Assessor depending on type of processor?
        raise NotImplementedError()
        
    def write_pbs(filename):
        raise NotImplementedError()

class ScanProcessor(Processor):
    def has_inputs():
        raise NotImplementedError()
     
    def should_run(): 
        raise NotImplementedError()
    
    def __init__(self,walltime_str,memreq_mb,name, ppn=1):
        super(ScanProcessor, self).__init__(walltime_str, memreq_mb, name, ppn)
         
    def get_assessor_name(self,scan_dict):
        subj_label = scan_dict['subject_label']
        sess_label = scan_dict['session_label']
        proj_label = scan_dict['project_label']
        scan_label = scan_dict['scan_label']
        return (proj_label+'-x-'+subj_label+'-x-'+sess_label+'-x-'+scan_label+'-x-'+self.name)
        
    def get_task(self, intf, scan_dict, upload_dir):
        scan = XnatUtils.get_full_object(intf,scan_dict)
        assessor_name = self.get_assessor_name(scan_dict)
        assessor = scan.parent().assessor(assessor_name)
        return task.Task(self,assessor,upload_dir)
        
class SessionProcessor(Processor):
    def has_inputs():
        raise NotImplementedError()
     
    def should_run(): 
        raise NotImplementedError()
    
    def __init__(self,walltime_str,memreq_mb,name,ppn=1):
        super(SessionProcessor, self).__init__(walltime_str,memreq_mb,name,ppn)
        
    def get_assessor_name(self,session_dict):  
        proj_label = session_dict['project']
        subj_label = session_dict['subject_label']
        sess_label = session_dict['label']  
        return (proj_label+'-x-'+subj_label+'-x-'+sess_label+'-x-'+self.name)
    
    def get_task(self, intf, session_dict, upload_dir):
        session = XnatUtils.get_full_object(intf,session_dict)
        assessor_name = self.get_assessor_name(session_dict)
        assessor = session.assessor(assessor_name)
        return task.Task(self,assessor,upload_dir)
    
def processors_by_type(proc_list):
    exp_proc_list = []
    scan_proc_list = []
            
    # Build list of processors by type
    for proc in proc_list:
        if issubclass(proc.__class__,ScanProcessor):
            scan_proc_list.append(proc)
        elif issubclass(proc.__class__,SessionProcessor):
            exp_proc_list.append(proc)
        else:
            print('ERROR:unknown processor type:'+proc)

    return exp_proc_list, scan_proc_list
