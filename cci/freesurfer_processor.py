import os
from os.path import expanduser
from datetime import datetime

import task
import XnatUtils
from processors import SessionProcessor, DEFAULT_MASIMATLAB_PATH

DEFAULT_FS_WALLTIME = '48:00:00'
DEFAULT_FS_MEM = 4096
DEFAULT_FS_NAME = 'FreeSurfer'
DEFAULT_FREESURFER_HOME = '/scratch/mcr/freesurfer'

# TODO: do we really want to run on any T1s that aren't marked unusable? or should we deal with questionable and only run on usable?
    
def is_t1(scan_type):
    return (scan_type == 'T1' or scan_type == 'MPRAGE')

def is_unusable(scan_quality):
    return (scan_quality == 'unusable')

class Freesurfer_Processor (SessionProcessor):
    def __init__(self, fs_home=DEFAULT_FREESURFER_HOME, masimatlab=DEFAULT_MASIMATLAB_PATH, walltime=DEFAULT_FS_WALLTIME, mem_mb=DEFAULT_FS_MEM, proc_name=DEFAULT_FS_NAME):
        super(Freesurfer_Processor, self).__init__(walltime,mem_mb,proc_name)
        self.fs_home = fs_home
        self.masimatlab = masimatlab
        self.xsitype = 'fs:fsData'

    def has_inputs(self, assessor):  
        session = assessor.parent()
        T1_scan_list = self.get_goodt1(session)
        T1_scan_count = len(T1_scan_list)
        if T1_scan_count == 0: 
            return False
        
        T1_id_list = []
        for T1 in T1_scan_list:
            T1_id_list.append(T1.id())
        T1_csv = ",".join(map(str,T1_id_list))
        assessor.attrs.set("fs:fsData/parameters/addParam[name=INCLUDED_T1]/addField",T1_csv)
        
        # Check for NIFTI versions of all T1s
        T1_nifti_count = 0
        for scan in T1_scan_list:
            cur_res = scan.resource('NIFTI')
            if cur_res.exists() and len(cur_res.files().get()) > 0:
                T1_nifti_count += 1

        return (T1_nifti_count == T1_scan_count)
     
    def should_run(self, sess_dict): 
        # We have no restrictions on Freesurfer by default, it may run on any session and will create 
        # an assessor regardless of whether it is able to run
        return True
    
    def get_assessor_name(self, session):            
        # Look for existing Freesurfer
        assessor_list = session.assessors()
        for assr in assessor_list:
            if assr.datatype() == self.xsitype:
                return assr.label()
        
        # Create label for new assessor
        proj_label = session.parent().parent().label()
        subj_label = session.parent().label()
        sess_label = session.label()
        return (proj_label+'-x-'+subj_label+'-x-'+sess_label+'-x-'+'FS')
            
    def get_goodt1(self,session):
        T1_scan_list = []
        for scan in session.scans().fetchall('obj'):
            if is_t1(scan.attrs.get('xnat:imageScanData/type')) and not is_unusable(scan.attrs.get('xnat:imageScanData/quality')):
                T1_scan_list.append(scan)
                
        return T1_scan_list

    def get_task(self, intf, sess_dict, upload_dir):
        session = XnatUtils.get_full_object(intf, sess_dict)
        assessor_name = self.get_assessor_name(session)
        assessor = session.assessor(assessor_name)
        if not assessor.exists():
            assessor.create(assessors='fs:fsData', **{'fs:fsData/fsversion':'0'})
            assessor.attrs.set('proc:genprocdata/date', datetime.today().strftime('%Y-%m-%d'))
            if self.has_inputs(assessor):
                assessor.attrs.set('fs:fsdata/validation/status', task.READY_TO_RUN)
            else:
                assessor.attrs.set('fs:fsdata/validation/status', task.NEED_INPUTS)
        return task.Task(self,assessor,upload_dir)
    
    def get_cmds(self,assessor,jobdir):         
        proj_label = assessor.parent().parent().parent().label()
        subj_label = assessor.parent().parent().label()
        sess_label = assessor.parent().label()
        sess_id = assessor.parent().id()
        FS_label = assessor.label()
        T1_csv = ''.join(assessor.xpath("//xnat:addParam[@name='INCLUDED_T1']/child::text()")).replace("\n","")
        FS_dir = jobdir+'/'+FS_label       
        jc_fname  = 'job.completed'
        jc_fpath  = FS_dir+'/'+jc_fname
        je_fname  = 'job.error'
        je_fpath  = FS_dir+'/'+je_fname  
        FS_subject_dir = FS_dir+'/Subjects/'+FS_label
        FS_inputs = ''
        
        cmd = """
# Get the inputs
mkdir -p {FS_DIR}"""
        
        # Get nifti file names from T1s, append to FS inputs, and add download commands
        T1_id_list = T1_csv.split(',')
        for T1_id in T1_id_list:
            nifti_res = assessor.parent().scan(T1_id).resource('NIFTI')
            nifti_fname = nifti_res.files().get()[0]
            FS_inputs += ' -i '+FS_dir + '/' + nifti_fname
            cmd += "\ncurl -u {XNAT_USER}:{XNAT_PASS} {XNAT_HOST}/data/archive/projects/{PROJ_LABEL}/subjects/{SUBJ_LABEL}/experiments/{SESS_LABEL}/scans/"+T1_id+"/resources/NIFTI/files/"+nifti_fname+" > {FS_DIR}/"+nifti_fname
            
        format_dict = {'SUBJECTS_DIR' : FS_dir+'/Subjects/',
            'FREESURFER_HOME' : self.fs_home,
            'MASIMATLAB' : self.masimatlab,
            'JOB_COMPLETED_FPATH' : jc_fpath,
            'JOB_ERROR_FPATH' : je_fpath,
            'FS_DIR'  : FS_dir,
            'FS_INPUTS' : FS_inputs,
            'FS_LABEL' : FS_label,
            'FS_SUBJECT_DIR' : FS_subject_dir,
            'T1_LIST' : T1_csv,
            'PROJ_LABEL' : proj_label, 
            'SUBJ_LABEL' : subj_label, 
            'SESS_LABEL' : sess_label,
            'EXP_ID' : sess_id,
            'XNAT_USER' : os.environ['XNAT_USER'],
            'XNAT_PASS' : os.environ['XNAT_PASS'],
            'XNAT_HOST' : os.environ['XNAT_HOST']}

        cmd += """
        
# Freesurfer Setup
mkdir -p {FS_DIR}/Subjects
export FREESURFER_HOME={FREESURFER_HOME}
source $FREESURFER_HOME/SetUpFreeSurfer.sh
                        
# Run main freesurfer                      
recon-all -sd {SUBJECTS_DIR} -s {FS_LABEL} {FS_INPUTS}
recon-all -sd {SUBJECTS_DIR} -s {FS_LABEL} -all -qcache -hippo-subfields

# Create QC snaps
export PERL5LIB=$PERL5LIB:{MASIMATLAB}/trunk/xnatspiders/bin/tools
xvfb-run --auto-servernum --server-num=1 -e {FS_DIR}/snaps_xvfb-run.err -f {FS_DIR}/snaps_xvfb-run.auth --server-args="-screen 0 1600x1280x24 -ac" snap_montage_fs5_bdb1.csh {FS_LABEL} {FS_DIR}/Subjects

# Zip snaps
zip -j {FS_DIR}/snapshots.zip {FS_SUBJECT_DIR}/snapshots/*.png
rm -r {FS_SUBJECT_DIR}/snapshots

# Create QA PDFs
xvfb-run --auto-servernum --server-num=1 -e {FS_DIR}/anat_xvfb-run.err -f {FS_DIR}/anat_xvfb-run.auth --server-args="-screen 0 1600x1280x24 -ac" \
matlab -nodesktop -nosplash > {FS_DIR}/anatQA_matlabOutput.txt << EOF
    addpath(genpath('{MASIMATLAB}/trunk/xnatspiders/matlab'));
    % Get variables from shell:
    v1 = '{FS_SUBJECT_DIR}';
    v2 = '{FS_LABEL}';
    v3 = '{FS_DIR}/anatQA';
    anatQa(v1,v2,v3);
    quit
EOF

# Combine left and right PDF in to single file
gs -dBATCH -dNOPAUSE -q -sDEVICE=pdfwrite -sOutputFile={FS_DIR}/{FS_LABEL}_anatQA.pdf {FS_DIR}/anatQA/{FS_LABEL}_lh_multiPagePDF.pdf {FS_DIR}/anatQA/{FS_LABEL}_rh_multiPagePDF.pdf  

# Move matlab output into anatQA
mv {FS_DIR}/anatQA_matlabOutput.txt {FS_DIR}/anatQA/matlabOutput.txt

# Zip anatQA
zip -j {FS_DIR}/anatqa.zip {FS_DIR}/anatQA/*
rm -r {FS_DIR}/anatQA

# Create assessor xml
cd {FS_DIR}
stats2xml_fs5.1.pl -p {PROJ_LABEL} -x {EXP_ID} -t Freesurfer -f {FS_LABEL} -m {T1_LIST} {FS_SUBJECT_DIR}/stats

# Zip data
cd {FS_DIR}/Subjects/
zip -r {FS_DIR}/data.zip {FS_LABEL}
rm -r {FS_LABEL}

# Set status
if [ $?=0 ]; then
        touch {JOB_COMPLETED_FPATH}
else
        touch {JOB_ERROR_FPATH}
fi

python {MASIMATLAB}/trunk/xnatspiders/bin/tools/FreeSurfer_Finisher.py --proj_label {PROJ_LABEL} --subj_label {SUBJ_LABEL} --sess_label {SESS_LABEL} --fs_label {FS_LABEL} --sess_id {EXP_ID} --dir {FS_DIR}

echo "DONE"
"""
        cmd = cmd.format(**format_dict)
        return [cmd]
