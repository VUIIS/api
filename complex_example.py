import os
import secret
from launcher import Launcher
from freesurfer_processor import Freesurfer_Processor
from dtiqa_processor import DtiQa_Processor
from fmriqa_processor import FmriQa_Processor
from vbmqa_processor import VbmQa_Processor


# Initialize processors with custom settings

freesurfer = Freesurfer_Processor(fs_home='/gpfs21/scratch/mcr/freesurfer')

dti = DtiQa_Processor(walltime='30:00:00',mem_mb=4096, dtiqa_path='/home/boydb1/svn/masimatlab/trunk/xnatspiders/bin/Spider_dtiQA_v2.py', masimatlab='/home/boydb1/svn/masimatlab')

fmri = FmriQa_Processor(secret.CCM_QA_API_KEY)

vbm = VbmQa_Processor(spm_path='/gpfs22/home/boydb1/apps/spm8')

# Configure a custom function for should_run
class GNB_Freesurfer_Processor(Freesurfer_Processor):
    def should_run(self, sess_info):
        return (sess_info['date'] == '2012-04-05')
GNB_freesurfer = GNB_Freesurfer_Processor()
    
#GNB_freesurfer = Freesurfer_Processor(fs_home='/gpfs21/scratch/mcr/freesurfer',walltime='36:00:00')
#GNB_freesurfer.should_run = GNB_freesurfer_should_run

# Set up processors for projects
pp = {'NewhouseCC' : [freesurfer, dti, fmri, vbm],
      'NewhousePL' : [freesurfer, dti, fmri],
      'NewhouseBC' : [freesurfer, dti, fmri],
      'NewhouseMDDHx' : [freesurfer, dti, fmri, vbm],
      'TAYLOR' : [freesurfer, dti, fmri], 
      'GNB_V' : [freesurfer, dti, fmri],
      'GNB' :  [GNB_freesurfer]}

# Configure launcher with specific queue limit and job dir
myLauncher = Launcher(queue_limit=1000, root_job_dir='/gpfs21/scratch/'+os.getlogin()+'/tmp')

# Now run the update
Launcher().update(pp)
