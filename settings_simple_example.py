from launcher import Launcher
from freesurfer_processor import Freesurfer_Processor
from dtiqa_processor import DtiQa_Processor
from fmriqa_processor import FmriQa_Processor
from vbmqa_processor import VbmQa_Processor

# Initialize processors (using default settings for all)
freesurfer = Freesurfer_Processor()
dti = DtiQa_Processor()
fmri = FmriQa_Processor()
vbm = VbmQa_Processor()

# Set up processors for projects, dictionary with project as key and list of processors as value
p = {'NewhouseCC' : [freesurfer, dti, fmri, vbm],
      'NewhousePL' : [freesurfer, dti, fmri],
      'NewhouseBC' : [freesurfer, dti, fmri],
      'NewhouseMDDHx' : [freesurfer, dti, fmri, vbm],
      'TAYLOR' : [freesurfer, dti, fmri], 
      'GNB_V' : [freesurfer, dti, fmri],
      'GNB' :  [freesurfer]}

# Launch jobs
myLauncher = Launcher(p)
