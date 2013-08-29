from processors import DEFAULT_MASIMATLAB_PATH,ScanProcessor

DEFAULT_DTIQA_PATH = DEFAULT_MASIMATLAB_PATH+'/trunk/xnatspiders/bin/Spider_dtiQA_v2.py'
DEFAULT_WALLTIME = '36:00:00'
DEFAULT_MEM = 9216
DEFAULT_NAME = 'dtiQA_v2'

class DtiQa_Processor (ScanProcessor):
    def __init__(self, dtiqa_path=DEFAULT_DTIQA_PATH, masimatlab=DEFAULT_MASIMATLAB_PATH, walltime=DEFAULT_WALLTIME, mem_mb=DEFAULT_MEM, proc_name=DEFAULT_NAME):
        super(DtiQa_Processor, self).__init__(walltime,mem_mb,proc_name)
        self.dtiqa_path = dtiqa_path
        self.masimatlab = masimatlab
        
    def should_run(self, scan_dict):
        return (scan_dict['scan_type'].upper() == 'DIF' or scan_dict['scan_type'].upper() == 'DTI')
        
    def has_inputs(self, assessor):
        assr = assessor.label()
        scan_label = assr.split('-x-')[3]
        scan = assessor.parent().scan(scan_label)
        if (scan.resource('NIFTI').exists() and scan.resource('bval').exists() and scan.resource('bvec').exists() and \
            len(scan.resource('NIFTI').files()) > 0 and len(scan.resource('bval').files()) > 0 and len(scan.resource('bvec').files()) > 0 ):
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
