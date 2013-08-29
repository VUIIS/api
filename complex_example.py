import os
from secret import CCM_QA_API_KEY
from launcher import Launcher
from freesurfer_processor import Freesurfer_Processor
from dtiqa_processor import DtiQa_Processor
from fmriqa_processor import FmriQa_Processor
from vbmqa_processor import VbmQa_Processor
from datetime import datetime

# Initialize processors with custom settings
freesurfer = Freesurfer_Processor(fs_home='/gpfs21/scratch/mcr/freesurfer')

dti = DtiQa_Processor(walltime='30:00:00',mem_mb=4096, dtiqa_path='/home/boydb1/svn/masimatlab/trunk/xnatspiders/bin/Spider_dtiQA_v2.py', masimatlab='/home/boydb1/svn/masimatlab')

vbm = VbmQa_Processor(spm_path='/gpfs22/home/boydb1/apps/spm8')

# Configure a custom function for should_run
class GNB_Freesurfer_Processor(Freesurfer_Processor):
    def should_run(self, sess_info):
        try:
            sess_date = datetime.strptime(sess_info['date'], '%Y-%m-%d')
            return ((datetime.today() - sess_date).days < 30)
        except ValueError:
            return False
        
GNB_freesurfer = GNB_Freesurfer_Processor()

# Configure a custom function for should_run
class CCM_FmriQa_Processor(FmriQa_Processor):
    TYPE_LIST = ['N-BACK', 'POSNER', 'fMRI_Resting', 'fMRI_VCR', 'fMRI_nback', 'fMRI_EMOPIC', 'fMRI_EDP', 'fMRI_Task', 'TLT_EPI_1', 'TLT_EPI_2', 'TLT_EPI_3',  'TLT_EPI_4']
    def should_run(self, scan_info):
        return (scan_info['scan_type'] in self.TYPE_LIST)

CCM_fmri = CCM_FmriQa_Processor(redcapkey=CCM_QA_API_KEY)

# Set up processors for projects
pp = {'NewhouseCC' : [freesurfer, dti, CCM_fmri, vbm],
      'NewhousePL' : [freesurfer, dti, CCM_fmri],
      'NewhouseBC' : [freesurfer, dti, CCM_fmri],
      'NewhouseMDDHx' : [freesurfer, dti, CCM_fmri, vbm],
      'TAYLOR' : [freesurfer, dti, CCM_fmri], 
      'GNB_V' : [freesurfer, dti, CCM_fmri],
      'GNB' :  [GNB_freesurfer]}

# Set up processors for projects
pp = {'NewhouseBC' : [freesurfer, CCM_fmri],
      'NewhouseMDDHx' : [freesurfer, CCM_fmri]}

# Configure launcher with specific queue limit and job dir
myLauncher = Launcher(queue_limit=1000, root_job_dir='/gpfs21/scratch/'+os.getlogin()+'/tmp')

# Now run the update
myLauncher.update(pp)
#myLauncher.update_open_tasks(pp)
