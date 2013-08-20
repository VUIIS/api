import task,XnatUtils
import os
from processors import DEFAULT_MASIMATLAB_PATH,ScanProcessor

DEFAULT_DTIQA_PATH = DEFAULT_MASIMATLAB_PATH+'/trunk/xnatspiders/bin/Spider_dtiQA_v2.py'
DEFAULT_DTIQA_WALLTIME = '30:00:00'
DEFAULT_DTIQA_MEM = 4096
DEFAULT_DTIQA_NAME = 'dtiQA_v2'

class DtiQa_Processor (ScanProcessor):
    def __init__(self):
        super(DtiQa_Processor, self).__init__(DEFAULT_DTIQA_WALLTIME,DEFAULT_DTIQA_MEM,DEFAULT_DTIQA_NAME)
        self.fmriqa_path = DEFAULT_DTIQA_PATH
        self.masimatlab = DEFAULT_MASIMATLAB_PATH
        self.xsitype = 'proc:genProcData'
        
    def should_run(self, scan_dict):
        return (scan_dict['type'].upper() == 'DIF' or scan_dict['type'].upper() == 'DTI')
        
    def can_run(self, scan):
        if (scan.resource('NIFTI').exists() and scan.resource('bval').exists() and scan.resource('bvec').exists() and \
            len(scan.resource('NIFTI').files.get()[0])>0 and len(scan.resource('bval').files.get()[0])>0 and len(scan.resource('bvec').files.get()[0])>0):
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
        masimatlab = self.masimatlab
        
        cmd = 'python '+fmriqa_path+' -m '+masimatlab+' -p '+proj+' -d '+jobdir+' -s '+subj+' -e '+sess+' -c '+scan
        return [cmd]
