
class Task(object):
    READY_TO_RUN='READY_TO_RUN'
    RUNNING='RUNNING'
    MISSING_INPUTS='MISSING_INPUTS'
    COMPLETE='COMPLETE'
    processor
    assessor
    
    def __init__(self, processor, assessor):
        self.processor = processor
        self.assessor = assessor
        
    def update_status(self):
        pass
    
    def launch(self):
        self.write_pbs()
        job_id = self.submit_pbs()
        self.set_status(RUNNING)
        self.set_job_id(job_id)

    def get_status(self):
        xnat_status = self.assessor.attrs.get('proc:genProcData/procstatus')
        return xnat_status
                    
    def set_status(self, status):
        self.assessor.attrs.set('proc:genProcData/jobid',job_id)
    
    def set_job_id(self, job_id):
        assessor.attrs.set('proc:genProcData/jobid',job_id)
        pass
    
    def exists(self):
        return self.assessor.create(assessors='proc:genProcData')
    
    def pbs_path(self):
        # return canonical storage place for pbs
        # ~/.pbs/%(name).pbs?
        pass
    
    def write_pbs(self):
        commands = self.commands()
        header = self.header()
        with open(self.pbs_path(), 'w') as f:
            f.writelines(header + commands)
        # Or break this into a PBSGenerator class that we could better test
        # and provide to lower-level users
        # BB - Yes let's have a PBS Generator