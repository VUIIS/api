import cluster
from cluster import PBS
from datetime import date
import os

READY_TO_RUN='NeedToRun'
READY_TO_UPLOAD='ReadyToUpload'
RUNNING='Running'
MISSING_INPUTS='MISSING_INPUTS'
NEED_PREPROCESS='NeedPreprocess'
COMPLETE='COMPLETE'
UPLOADING='Uploading'
FAILED='Failed'
JOB_FAILED='JOB_FAILED'
FAILED_NEEDS_REPROC='Failed-needs reprocessing'
JOB_RUNNING='JOB_RUNNING'
NEEDS_QA='Needs QA'
PASSED_QA='Passed'
PASSED_EDITED_QA='Passed with edits'
DEFAULT_PBS_DIR=os.environ['UPLOAD_SPIDER_DIR']+'/PBS'
DEFAULT_OUT_DIR=os.environ['UPLOAD_SPIDER_DIR']+'/OUTLOG'
DOES_NOT_EXIST = 'DOES_NOT_EXIST'
READY_TO_UPLOAD_FLAG_FILENAME = 'READY_TO_UPLOAD.txt'
ERROR = 'ERROR'

class Task(object):
    def __init__(self, processor, assessor, upload_dir):
        self.processor = processor
        self.assessor = assessor
        self.assessor_id = assessor.id() # cached for convenience
        self.assessor_label = assessor.label() # cached for convenience
        self.atype = processor.xsitype.lower() # cached for convenience
        self.upload_dir = upload_dir
        
    def get_processor_name(self):
        return self.processor.name
    
    def check_job_usage(self):
        # If already set, do nothing
        if self.get_memusedmb() != '' and self.get_walltime() != '':
            return
        
        jobstartdate = self.get_jobstartdate()
        
        # If we can't get info from cluster, do nothing
        if not cluster.is_traceable_date(jobstartdate):
            return
        
        jobinfo = cluster.tracejob_info(self.get_jobid(), jobstartdate)
        if jobinfo['mem_used'] != '': 
            memusedmb = str(int(jobinfo['mem_used'])/1024)
            self.set_memusedmb(memusedmb)
        if jobinfo['walltime_used'] != '':
            self.set_walltime(jobinfo['walltime_used'])
            
    def get_memusedmb(self):
        memusedmb = ''
        if self.atype == 'proc:genprocdata':
            memusedmb = self.assessor.attrs.get('proc:genProcData/memusedmb')
        elif self.atype == 'fs:fsdata':
            memusedmb = ''.join(self.assessor.xpath("//xnat:addParam[@name='memusedmb']/child::text()")).replace("\n","")
        return memusedmb
    
    def set_memusedmb(self,memusedmb):
        if self.atype == 'proc:genprocdata':
            self.assessor.attrs.set('proc:genProcData/memusedmb', memusedmb)
        elif self.atype == 'fs:fsdata':
            self.assessor.attrs.set("fs:fsdata/parameters/addParam[name=memusedmb]/addField", memusedmb)
            
    def get_walltime(self):
        walltime = ''
        if self.atype == 'proc:genprocdata':
            walltime = self.assessor.attrs.get('proc:genProcData/walltime')
        elif self.atype == 'fs:fsdata':
            walltime = ''.join(self.assessor.xpath("//xnat:addParam[@name='walltime']/child::text()")).replace("\n","")
        return walltime
    
    def set_walltime(self,walltime):
        if self.atype == 'proc:genprocdata':
            self.assessor.attrs.set('proc:genProcData/walltime', walltime)
        elif self.atype == 'fs:fsdata':
            self.assessor.attrs.set("fs:fsdata/parameters/addParam[name=walltime]/addField", walltime)

    def update_status(self):                
        old_status = self.get_status()
        new_status = old_status
        
        if old_status == READY_TO_RUN:
            # TODO: anything, not yet???
            pass
        elif old_status.upper() == COMPLETE or old_status == PASSED_QA or old_status == PASSED_EDITED_QA or old_status == NEEDS_QA:
            # TODO: check that memused and walltime are complete, if not get with tracejob
            pass
        elif old_status == FAILED or old_status == FAILED_NEEDS_REPROC:
            # TODO: check that memused and walltime are complete, if not get with tracejob
            self.check_job_usage()
        elif old_status == JOB_FAILED:
            # TODO: anything???
            self.check_job_usage()
        elif old_status == MISSING_INPUTS or old_status == NEED_PREPROCESS:
            # Check it again in case available inputs changed
            if self.has_inputs():
                new_status = READY_TO_RUN
        elif old_status == RUNNING or old_status == JOB_RUNNING:
            new_status = self.check_running()
        elif old_status == READY_TO_UPLOAD:
            # TODO: let upload spider handle it???
            pass
        elif old_status == UPLOADING:
            # TODO: can we see if it's really uploading???
            pass
        else:
            print 'ERROR:unknown status:'+old_status
            
        if (new_status != old_status):
            print('DEBUG:changing status from '+old_status+' to '+new_status)
            self.set_status(new_status)
            
        return new_status
    
    def get_jobid(self):    
        jobid = ''    
        if self.atype == 'proc:genprocdata':
            jobid = self.assessor.attrs.get('proc:genprocdata/jobid')
        elif self.atype == 'fs:fsdata':
            jobid = ''.join(self.assessor.xpath("//xnat:addParam[@name='jobid']/child::text()")).replace("\n","")
        return jobid
        
    def get_job_status(self):
        jobstatus = 'UNKNOWN'
        jobid = self.get_jobid()
        
        if jobid != '' and jobid != '0':
            jobstatus = cluster.job_status(jobid)
       
        return jobstatus
            
    def launch(self,jobdir):
        cmds = self.commands(jobdir)
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
        
    def get_jobstartdate(self):
        jobstartdate = ''
        if self.atype == 'proc:genprocdata':
            jobstartdate = self.assessor.attrs.get('proc:genProcData/jobstartdate')
        elif self.atype == 'fs:fsdata':
            jobstartdate = ''.join(self.assessor.xpath("//xnat:addParam[@name='jobstartdate']/child::text()")).replace("\n","")
        return jobstartdate
    
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

    def commands(self,jobdir):
        return self.processor.get_cmds(self.assessor,jobdir+"/"+self.assessor_label)
    
    def pbs_path(self):
        return DEFAULT_PBS_DIR+'/'+self.assessor_label+'.pbs'
    
    def outlog_path(self):
        return DEFAULT_OUT_DIR+'/'+self.assessor_label+'_OUTLOG.txt'
    
    def ready_flag_exists(self):
        flagfile = self.upload_dir+'/'+self.assessor_label+'/'+READY_TO_UPLOAD_FLAG_FILENAME
        print 'DEBUG:checking for flagfile:'+flagfile
        return os.path.isfile(flagfile)

    def check_running(self):
        # Check status on cluster
        jobstatus = self.get_job_status()
        
        if jobstatus == 'R' or jobstatus == 'Q':
            # Still running
            return RUNNING
        elif not self.ready_flag_exists():
            # Check for a flag file created upon completion, if it's not there then the job failed
            return JOB_FAILED
        else:
            # Let Upload Spider handle the upload
            return RUNNING
