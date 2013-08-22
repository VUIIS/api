import task
import XnatUtils
import os
from processors import DEFAULT_MASIMATLAB_PATH,ScanProcessor

DEFAULT_VBMQA_PATH = DEFAULT_MASIMATLAB_PATH+'/trunk/xnatspiders/bin/Spider_VBMQA.py'
DEFAULT_VBMQA_WALLTIME = '01:00:00'
DEFAULT_VBMQA_MEM = 2048
DEFAULT_VBMQA_NAME = 'VBMQA'
DEFAULT_SPM_PATH='/gpfs22/home/boydb1/apps/spm8'
    
class VbmQa_Processor (ScanProcessor):
    def __init__(self):
        super(VbmQa_Processor, self).__init__(DEFAULT_VBMQA_WALLTIME,DEFAULT_VBMQA_MEM,DEFAULT_VBMQA_NAME)
        self.vbmqa_path = DEFAULT_VBMQA_PATH
        self.masimatlab = DEFAULT_MASIMATLAB_PATH
        self.xsitype = 'proc:genProcData'
        self.spmpath = DEFAULT_SPM_PATH
        
    def should_run(self, scan_dict):
        return ('T1' in scan_dict['type'] or 'MPRAGE' in scan_dict['type'])
        
    def has_inputs(self, assessor):
        assr = assessor.label()
        scan_label = assr.split('-x-')[3]
        scan = assessor.parent().scan(scan_label)
        if scan.resource('NIFTI').exists():
            return True
        else:
            return False
    
    def get_cmds(self,assessor,jobdir):
        proj = assessor.parent().parent().parent().label()
        subj = assessor.parent().parent().label()
        sess = assessor.parent().label()
        assr = assessor.label()
        scan = assr.split('-x-')[3]
        vbmqa_path = self.vbmqa_path
        masimatlab = self.masimatlab
        spmpath = self.spmpath
        
        cmd = 'python '+vbmqa_path+' -m '+masimatlab+' --spm '+spmpath+' -p '+proj+' -d '+jobdir+' -s '+subj+' -e '+sess+' -c '+scan

        return [cmd]
