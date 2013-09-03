from launcher import Launcher
from freesurfer_processor import Freesurfer_Processor
from dtiqa_processor import DtiQa_Processor
from fmriqa_processor import FmriQa_Processor
from vbmqa_processor import VbmQa_Processor

# Initialize processors
freesurfer = Freesurfer_Processor()
dti = DtiQa_Processor()
vbm = VbmQa_Processor(spm_path='/gpfs21/scratch/masispider/spm8')
fmri = FmriQa_Processor()

# Set up processors for project
p = {'BLSA' : [freesurfer, dti, fmri, vbm]}

# Launch update
Launcher(p).update
