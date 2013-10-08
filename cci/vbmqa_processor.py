from processors import DEFAULT_MASIMATLAB_PATH,ScanProcessor

DEFAULT_VBMQA_PATH = DEFAULT_MASIMATLAB_PATH+'/trunk/xnatspiders/bin/Spider_VBMQA.py'
DEFAULT_WALLTIME = '01:00:00'
DEFAULT_MEM = 2048
DEFAULT_NAME = 'VBMQA'
DEFAULT_SPM_PATH='/gpfs21/scratch/mcr/spm8'
DEFAULT_SCAN_TYPES = ['T1', 'MPRAGE']

class VbmQa_Processor (ScanProcessor):
    def __init__(self, vbmqa_path=DEFAULT_VBMQA_PATH, masimatlab=DEFAULT_MASIMATLAB_PATH, walltime=DEFAULT_WALLTIME, mem_mb=DEFAULT_MEM, proc_name=DEFAULT_NAME, scan_types=DEFAULT_SCAN_TYPES, spm_path=DEFAULT_SPM_PATH):
        super(VbmQa_Processor, self).__init__(walltime,mem_mb,proc_name)
        self.vbmqa_path = vbmqa_path
        self.masimatlab = masimatlab
        self.spm_path = spm_path
        self.scan_types = scan_types

    def should_run(self, scan_dict):
        return (scan_dict['scan_type'].upper() in self.scan_types)
        
    def has_inputs(self, assessor):        
        scan_label = assessor.label().split('-x-')[3]
        return assessor.parent().scan(scan_label).resource('NIFTI').exists()
    
    def get_cmds(self,assessor,jobdir):
        proj = assessor.parent().parent().parent().label()
        subj = assessor.parent().parent().label()
        sess = assessor.parent().label()
        assr = assessor.label()
        scan = assr.split('-x-')[3]
        vbmqa_path = self.vbmqa_path
        masimatlab = self.masimatlab
        spm_path = self.spm_path
        
        cmd = 'python '+vbmqa_path+' -v -m '+masimatlab+' --spm '+spm_path+' -p '+proj+' -d '+jobdir+' -s '+subj+' -e '+sess+' -c '+scan
        return [cmd]
