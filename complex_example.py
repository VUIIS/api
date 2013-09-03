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

fmri = FmriQa_Processor(redcapkey=CCM_QA_API_KEY, scan_types=['1.2 fmri_179_DYN_2000_TR_SENSE', 'FMRI_TASK', '1.2 fmri_179_DYN_2000_TR_SENSE', '1.2_FMRI_150_DYN_2000_TR_SENSE', 'N-BACK','POSNER','FMRI','FMRI_RESTING','FMRI_VCR','FMRI_NBACK','FMRI_EMOPIC','FMRI_EDP','FMRI_Task','TLT_EPI_1','TLT_EPI_2','TLT_EPI_3','TLT_EPI_4'])

# Configure a custom function for should_run
class GNB_Freesurfer_Processor(Freesurfer_Processor):
    def should_run(self, sess_info):
        try:
            sess_date = datetime.strptime(sess_info['date'], '%Y-%m-%d')
            return ((datetime.today() - sess_date).days < 30)
        except ValueError:
            return False
        
GNB_freesurfer = GNB_Freesurfer_Processor()

# Set up processors for projects
pp = {'NewhouseCC' : [freesurfer, dti, fmri, vbm],
      'NewhousePL' : [freesurfer, dti, fmri],
      'NewhouseBC' : [freesurfer, dti, fmri],
      'NewhouseMDDHx' : [freesurfer, dti, fmri, vbm],
      'TAYLOR' : [freesurfer, dti, fmri], 
      'GNB_V' : [freesurfer, dti, fmri],
      'GNB' :  [GNB_freesurfer],
      'R21Perfusion' : [freesurfer, dti, fmri, vbm]}

# Configure launcher with specific queue limit and job dir
myLauncher = Launcher(pp, queue_limit=1000, root_job_dir='/gpfs21/scratch/'+os.getlogin()+'/tmp')

# Now run the update
if 1:
    myLauncher.update()
if 1:
    myLauncher.update_open_tasks()
