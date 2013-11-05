from processors import DEFAULT_MASIMATLAB_PATH,ScanProcessor

DEFAULT_FMRIQA_PATH = DEFAULT_MASIMATLAB_PATH+'/trunk/xnatspiders/bin/Spider_fMRIQA.py'
DEFAULT_WALLTIME = '00:30:00'
DEFAULT_MEM = 2048
DEFAULT_NAME = 'fMRIQA'
DEFAULT_SCAN_TYPES = ['FMRI', 'REST', 'FMRI_RESTING', 'RESTING']
    
class FmriQa_Processor (ScanProcessor):
    def __init__(self, fmriqa_path=DEFAULT_FMRIQA_PATH, masimatlab=DEFAULT_MASIMATLAB_PATH, walltime=DEFAULT_WALLTIME, mem_mb=DEFAULT_MEM, proc_name=DEFAULT_NAME, scan_types=DEFAULT_SCAN_TYPES):
        super(FmriQa_Processor, self).__init__(walltime,mem_mb,proc_name)
        self.fmriqa_path = fmriqa_path
        self.masimatlab = masimatlab
        self.scan_types = scan_types

    def should_run(self, scan_dict):
        return (scan_dict['scan_type'].upper() in self.scan_types)
        
    def has_inputs(self, assessor):
        scan_label = assessor.label().split('-x-')[3]
        scan = assessor.parent().scan(scan_label)
        return ((scan.resource('PAR').exists() and scan.resource('REC').exists()) or scan.resource('NIFTI').exists())
    
    def get_cmds(self,assessor,jobdir):
        proj = assessor.parent().parent().parent().label()
        subj = assessor.parent().parent().label()
        sess = assessor.parent().label()
        assr = assessor.label()
        scan = assr.split('-x-')[3]
        fmriqa_path = self.fmriqa_path
        masimatlab = self.masimatlab
        
        cmd = 'python '+fmriqa_path+' -v -m '+masimatlab+' -p '+proj+' -d '+jobdir+' -s '+subj+' -e '+sess+' -c '+scan
        return [cmd]
