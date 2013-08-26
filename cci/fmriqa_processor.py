from processors import DEFAULT_MASIMATLAB_PATH,ScanProcessor

DEFAULT_FMRIQA_PATH = DEFAULT_MASIMATLAB_PATH+'/trunk/xnatspiders/bin/Spider_fMRIQA.py'
DEFAULT_WALLTIME = '01:00:00'
DEFAULT_MEM = 2048
DEFAULT_NAME = 'fMRIQA'
    
class FmriQa_Processor (ScanProcessor):
    def __init__(self, fmriqa_path=DEFAULT_FMRIQA_PATH, masimatlab=DEFAULT_MASIMATLAB_PATH, walltime=DEFAULT_WALLTIME, mem_mb=DEFAULT_MEM, proc_name=DEFAULT_NAME, redcapkey=''):
        super(FmriQa_Processor, self).__init__(walltime,mem_mb,proc_name)
        self.fmriqa_path = fmriqa_path
        self.masimatlab = masimatlab
        self.redcapkey = redcapkey

    def should_run(self, scan_dict):
        return ('fmri' in scan_dict['type'].lower())
        
    def has_inputs(self, assessor):
        assr = assessor.label()
        scan_label = assr.split('-x-')[3]
        scan = assessor.parent().scan(scan_label)
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
