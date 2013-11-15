from processors import DEFAULT_MASIMATLAB_PATH,SessionProcessor

DEFAULT_SCRIPT_PATH = DEFAULT_MASIMATLAB_PATH+'/trunk/xnatspiders/bin/Spider_TBSS_pre.py'
DEFAULT_WALLTIME = '00:30:00'
DEFAULT_MEM = 2048
DEFAULT_NAME = 'TBSS_pre'
 
def is_unusable(scan_quality):
    return (scan_quality == 'unusable')

class TbssPre_Processor (SessionProcessor):
    def __init__(self, script_path=DEFAULT_SCRIPT_PATH, masimatlab=DEFAULT_MASIMATLAB_PATH, walltime=DEFAULT_WALLTIME, mem_mb=DEFAULT_MEM, proc_name=DEFAULT_NAME):
        super(TbssPre_Processor, self).__init__(walltime,mem_mb,proc_name)
        self.script_path = script_path
        self.masimatlab = masimatlab
    
    def get_gooddti(self,session):
        dti_list = []
        for assr in session.assessors().fetchall('obj'):
            if assr.datatype() == 'proc:genProcData' and assr.attrs.get('proc:genProcData/proctype') == 'dtiQA_v2' and 'Passed' in assr.attrs.get('proc:genProcData/validation/status'):
                dti_list.append(assr)
                
        return dti_list

    def should_run(self, sess_dict): 
        # We have no restrictions by default, it may run on any session and will create 
        # an assessor regardless of whether it is able to run
        return True
        
    def has_inputs(self, assessor):  
        session = assessor.parent()
        
        # Check for only one good dtiQA
        dti_list = self.get_gooddti(session)
        dti_count = len(dti_list)    
                
        if not dti_count > 0:
            print 'WARN:cannot run, no dtiQA found'
            return False    
        if dti_count > 1:
            print 'WARN:cannot run, multiple dtiQA found'
            return False 
        
        dti = dti_list[0]
        print('DEBUG:dti label='+dti.label())
        dti_res = dti.out_resource('TGZ')
        if not dti_res.exists() or len(dti_res.files().get()) <= 0:
            print 'WARN:cannot run, no TGZ found for dtiQA'
            return False  
    
        # All inputs found
        return True
    
    def get_cmds(self,assessor,jobdir):
        proj = assessor.parent().parent().parent().label()
        subj = assessor.parent().parent().label()
        sess = assessor.parent().label()
        script_path = self.script_path
        dti_list = self.get_gooddti(assessor.parent())
        dti_label = dti_list[0].label()
        masimatlab = self.masimatlab
        
        cmd = 'python '+script_path+' -m '+masimatlab+' -p '+proj+' -s '+subj+' -e '+sess+' -d '+jobdir+' -a '+dti_label
        return [cmd]
