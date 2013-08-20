
import secret
import launcher
from freesurfer_processor import Freesurfer_Processor
from dtiqa_processor import DtiQa_Processor
from fmriqa_processor import FmriQa_Processor
from vbmqa_processor import VbmQa_Processor

MAX_JOB_COUNT = 50
ROOT_JOB_DIR = '/gpfs21/scratch/boydb1/tmp'

# Initialize processors
freesurfer = Freesurfer_Processor()
dti = DtiQa_Processor()
fmri = FmriQa_Processor(secret.CCM_QA_API_KEY)
vbm = VbmQa_Processor()

# Setup processors for projects
project_process_dict = {'NewhouseCC' : [freesurfer, dti, fmri, vbm],
                        'NewhousePL' : [freesurfer, dti, fmri],
                        'NewhouseMDDHx' : [freesurfer, dti, fmri, vbm],
                        'NewhouseBC' : [freesurfer, dti, fmri],
                        'TAYLOR' : [freesurfer, dti, fmri], 
                        'GNB_V' : [freesurfer, dti, fmri],
                        'GNB' :  [freesurfer]}

# Update and Launch jobs until there are MAX_JOB_COUNT in the cluster queue
launcher.update_and_launch_jobs(MAX_JOB_COUNT,project_process_dict,ROOT_JOB_DIR)
