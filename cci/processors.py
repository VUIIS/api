import task

# Could can_run or may_run be called when task is created and throws errors if task cannot be created?

# The processor's can_run method should do everything to make sure that when job is created and submitted it will run

# can implemented method have different number of arguments than abstract method?

class Processor:
    def __init__(self,memreq_mb,walltime_str,name):
        self.walltime_str=walltime_str # 00:00:00 format
        self.memreq_mb=memreq_mb  # memory required in megabytes      
        self.name=name 
    
    # can_run - does this object have the required inputs? e.g. NIFTI format of the required scan type and quality and are there no conflicting inputs, i.e. only 1 required by 2 found?
    def can_run(self): # what other arguments here, could be Project/Subject/Session/Scan/Assessor depending on type of processor?
        raise NotImplementedError()
     
    # may_run - is the object of the proper object type? e.g. is it a scan? and is it the required scan type? e.g. is it a T1?
    def may_run(self): # what other arguments here, could be Project/Subject/Session/Scan/Assessor depending on type of processor?
        raise NotImplementedError()
        
    def write_pbs(filename):
        raise NotImplementedError()

class ScanProcessor:
    def can_run(self, intf, projectid, subjectid, experimentid, scanid):
        raise NotImplementedError()
     
    def may_run(self, intf, projectid, subjectid, experimentid, scanid): 
        raise NotImplementedError()
        
class SessionProcessor:
    def can_run(self, intf, projectid, subjectid, experimentid):
        raise NotImplementedError()
     
    def may_run(self, intf, projectid, subjectid, experimentid): 
        raise NotImplementedError()

class FreesurferPerSession_Processor (SessionProcessor):
    root_job_dir='/tmp/Freesurfer'
    FREESURFER_HOME='/scratch/mcr/freesurfer'

    def is_t1(scan):
        scan_type = scan['type']
        return (scan_type == 'T1' or scan_type == 'MPRAGE')
    
    def is_usable(scan):
        scan_quality = scan['quality']
        return (scan_quality == 'usable')
    
    def is_questionable(scan):
        scan_quality = scan['quality']
        return (scan_quality == 'questionable')
    
    def __init__(self):
        # Invokes the class constructor of the parent class
        super(FreesurferPerSession_Processor, self).__init__('48:00:00',4096,'Freesurfer')
        
    def can_run(self, intf, simple_session):
        # Does this Session have at least one T1 with quality of usable and no T1s of questionable quality?

        # Get list of all scans
        scan_list = xnat.list_scans(intf, simple_session.projectid, simple_session.subjectid, simple_session.id)

        # Trim list to only T1 scans
        T1_scan_list = [x for x in scan_list if is_t1(x)] 
    
        # Look for any questionable T1s
        if (len([x for x in T1_scan_list if is_questionable(x)]) > 0):
            return False

        # Check for at least one usable T1
        if (len([x for x in T1_scan_list if is_usable(x)]) > 0):
            return True
        else:
            return False
     
    def may_run(self, intf, simple_session): 
        # We have not restrictions on Freesurfer by default, it may run on any experiment and will create 
        # an assessor regardless of whether it is able to run
        return True
    
    def get_assessor_name(self,simple_session):
        return 
    
    def get_task(self, simple_session):
        assessor
        return Task(self,assessor)
