import cluster

from cluster import PBS
from os.path import expanduser
from datetime import date

USER_HOME = expanduser("~")

READY_TO_RUN='NeedToRun'
READY_TO_UPLOAD='ReadyToUpload'
RUNNING='Running'
MISSING_INPUTS='MISSING_INPUTS'
NEED_PREPROCESS='NeedPreprocess'
COMPLETE='COMPLETE'
UPLOADING='Uploading'
FAILED='Failed'
FAILED_NEEDS_REPROC='Failed-needs reprocessing'
JOB_RUNNING='JOB_RUNNING'
NEEDS_QA='Needs QA'
PASSED_QA='Passed'
PASSED_EDITED_QA='Passed with edits'
DEFAULT_PBS_DIR=USER_HOME+'/PBS'
DEFAULT_OUT_DIR=USER_HOME+'/OUT'
DOES_NOT_EXIST = 'DOES_NOT_EXIST'

class Task(object):
    def __init__(self, processor, assessor):
        self.processor = processor
        self.assessor = assessor
        self.assessor_id = assessor.id() # cached for convenience
        self.assessor_label = assessor.label() # cached for convenience
        self.atype = processor.xsitype.lower() # cached for convenience
        
    def update_status(self):        
        if self.atype != 'fs:fsdata' and self.atype != 'proc:genprocdata':
            # TODO: throw error
            print 'ERROR:failed to get update status, unknown xsiType:'+self.atype
        elif not self.assessor.exists():
            # TODO: throw error
            print 'ERROR:assessor does not exist:'+self.assessor_label
        else:
            astatus = self.get_status()
            
            if astatus == READY_TO_RUN:
                # TODO: anything???
                pass
            elif astatus.upper() == COMPLETE or astatus == PASSED_QA or astatus == PASSED_EDITED_QA or astatus == NEEDS_QA:
                # TODO: check that memused and walltime are complete, if not get with tracejob
                pass
            elif astatus == FAILED or astatus == FAILED_NEEDS_REPROC:
                # TODO: check that memused and walltime are complete, if not get with tracejob
                pass
            elif astatus == MISSING_INPUTS or astatus == NEED_PREPROCESS:
                # Check it again in case available inputs changed
                if self.has_inputs():
                    astatus = READY_TO_RUN
                    self.set_status(READY_TO_RUN)
            elif astatus == RUNNING or astatus == JOB_RUNNING:
                astatus = self.check_running()
            elif astatus == READY_TO_UPLOAD:
                # TODO: anything???
                pass
            elif astatus == UPLOADING:
                # TODO: can we see if it's really uploading???
                pass
            else:
                print 'ERROR:unknown status:'+astatus
        return astatus
    
    def get_job_status(self):
        jobstatus = 'UNKNOWN'
        jobid = ''
        
        if self.atype == 'proc:genprocdata':
            jobid = self.assessor.attrs.get('proc:genprocdata/jobid')
        elif self.atype == 'fs:fsdata':
            jobid = ''.join(self.assessor.xpath("//xnat:addParam[@name='jobid']/child::text()")).replace("\n","")

        if jobid != '' and jobid != '0':
            jobstatus = cluster.job_status(jobid)
       
        return jobstatus
            
    def launch(self,jobdir):
        cmds = self.commands(jobdir+"/"+self.assessor_label)
        pbsfile = self.pbs_path()
        outlog = self.outlog_path()
        pbs = PBS(pbsfile,outlog,cmds,self.processor.walltime_str,self.processor.memreq_mb)
        pbs.write()
        jobid = pbs.submit()
        
        if jobid == '' or jobid == '0':
            # TODO: throw exception
            print 'ERROR:failed to launch job on cluster'
            return False
        else:
            self.set_status(RUNNING)
            self.set_jobid(jobid)
            self.set_jobstartdate()
            return True
    
    def set_jobstartdate(self):
        today = date.today()
        today_str = str(today)
        if self.atype == 'proc:genprocdata':
            self.assessor.attrs.set('proc:genProcData/jobstartdate', today_str)
        elif self.atype == 'fs:fsdata':
            self.assessor.attrs.set("fs:fsdata/parameters/addParam[name=jobstartdate]/addField", today_str)

        return today_str
    
    def get_status(self):
        if not self.assessor.exists():
            xnat_status = DOES_NOT_EXIST
        elif self.atype == 'proc:genprocdata':
            xnat_status = self.assessor.attrs.get('proc:genProcData/procstatus')
        elif self.atype == 'fs:fsdata':
            xnat_status = self.assessor.attrs.get('fs:fsdata/validation/status')
        else:
            xnat_status = 'UNKNOWN_xsiType:'+self.atype
        return xnat_status
                    
    def set_status(self,status):        
        if self.atype == 'fs:fsdata':
            self.assessor.attrs.set('fs:fsdata/validation/status', status)
        else:
            self.assessor.attrs.set('proc:genprocdata/procstatus', status)
            
    def has_inputs(self):
        return self.processor.has_inputs(self.assessor)
    
    def set_jobid(self,jobid):
        if self.atype == 'proc:genprocdata':
            self.assessor.attrs.set('proc:genprocdata/jobid', jobid)
        elif self.atype == 'fs:fsdata':
            self.assessor.attrs.set("fs:fsdata/parameters/addParam[name=jobid]/addField", jobid)

    def commands(self):
        return self.processor.get_cmds(self.assessor,self.jobdir)
    
    def pbs_path(self):
        return DEFAULT_PBS_DIR+'/'+self.assessor_label+'.pbs'
    
    def outlog_path(self):
        return DEFAULT_OUT_DIR+'/'+self.assessor_label+'_OUTLOG.txt'
    
    def check_running(self):
        # Check status on cluster
        jobstatus = self.get_job_status()
        if jobstatus == 'R' or jobstatus == 'Q':
            # Still running
            return RUNNING
        elif jobstatus == 'C':
            # TODO: see if it failed or completed successfully, if there's a folder in UPLOAD_DIR and it's not marked as READY_TO_UPLOAD then it failed
            return RUNNING
        else:
            print 'ERROR:unknown job status:'+jobstatus
            
            return RUNNING
        
