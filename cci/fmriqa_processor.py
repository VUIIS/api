import task
import XnatUtils
import os
from processors import DEFAULT_MASIMATLAB_PATH,ScanProcessor

DEFAULT_FMRIQA_PATH = DEFAULT_MASIMATLAB_PATH+'/trunk/xnatspiders/bin/Spider_fMRIQA.py'
DEFAULT_FMRIQA_WALLTIME = '01:00:00'
DEFAULT_FMRIQA_MEM = 2048
DEFAULT_FMRIQA_NAME = 'fMRIQA'
    
class FmriQa_Processor (ScanProcessor):
    def __init__(self,redcapkey=''):
        super(FmriQa_Processor, self).__init__(DEFAULT_FMRIQA_WALLTIME,DEFAULT_FMRIQA_MEM,DEFAULT_FMRIQA_NAME)
        self.fmriqa_path = DEFAULT_FMRIQA_PATH
        self.masimatlab = DEFAULT_MASIMATLAB_PATH
        self.redcapkey=redcapkey
        self.xsitype = 'proc:genProcData'
        
    def should_run(self, scan_dict):
        return ('fmri' in scan_dict['type'].lower())
        
    def can_run(self, scan):
        if (scan.resource('PAR').exists() and scan.resource('REC').exists()):
            return True
        else:
            return False
    
    def get_cmds(self,assessor,jobdir):
        proj = assessor.parent().parent().parent().label()
        subj = assessor.parent().parent().label()
        sess = assessor.parent().label()
        assr = assessor.label()
        scan = assr.split('-x-')[3]
        fmriqa_path = self.fmriqa_path
        redcapkey = self.redcapkey
        masimatlab = self.masimatlab
        
        cmd = 'python '+fmriqa_path+' -m '+masimatlab+' -p '+proj+' -d '+jobdir+' -s '+subj+' -e '+sess+' -c '+scan
        if redcapkey != '':
            cmd +=' -k '+redcapkey
        return [cmd]
