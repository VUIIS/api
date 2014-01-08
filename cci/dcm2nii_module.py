from modules import ScanModule
import os
import subprocess as sb

DEFAULT_DCM2NII='/gpfs21/scratch/mcr/mricron'
DEFAULT_TPM_PATH='/tmp/dcm2nii_temp/'
DEFAULT_MODULE_NAME='dcm2nii'
DEFAULT_TEXT_REPORT='ERROR/WARNING for dcm2nii :\n'
DEFAULT_EMAIL='nan'

class dcm2nii_Module(ScanModule):
    def __init__(self,module_name=DEFAULT_MODULE_NAME,directory=DEFAULT_TPM_PATH,email=DEFAULT_EMAIL,Text_report=DEFAULT_TEXT_REPORT,dcm2niipath=DEFAULT_DCM2NII):
        super(dcm2nii_Module, self).__init__(module_name,directory,email,Text_report=DEFAULT_TEXT_REPORT)
        self.dcm2niipath=dcm2niipath
    
    def prerun(self):
        #make directory
        self.make_dir()
    
    def afterrun(self,xnat,project):
        if self.email!='nan' and self.send_an_email:
            try:
                EMAIL_ADDR = os.environ['EMAIL_ADDR']
                EMAIL_PWS = os.environ['EMAIL_PWS']
                self.sendReport(EMAIL_ADDR,EMAIL_PWS,self.email,'**ERROR/WARNING for '+self.module_name+'**','smtp.gmail.com')
            except KeyError as e:
                print "You must set the environment variable %s for next time to receive the report." % str(e)
        
        #clean the directory created     
        self.clean_directory()
        os.rmdir(self.directory)
                
    def run(self,xnat,projectName,subject,experiment,scan):
        Scan = xnat.select('/project/'+projectName+'/subject/'+subject+'/experiment/'+experiment+'/scan/'+scan)
        if Scan.resource('DICOM').exists():
            if not Scan.resource('NIFTI').exists():
                if len(Scan.resource('DICOM').files().get()) > 0:
                    print '      -downloading all DICOMs...'
                    num=1
                    for dicom_fname in Scan.resource('DICOM').files().get()[:]:
                        dicom_file = Scan.resource('DICOM').file(dicom_fname)
                        local_fname = os.path.join(self.directory, str(num)+ '.dcm') 
                        dicom_file.get(local_fname)
                        num = num + 1
                    
                    # check that the dicom are complete (all the slices present)
                    f = open(os.path.join(self.directory,'callCheckDICOM.m'), "w")
                    try:
                        lines=[ '% Matlab Script to check DICOM function\n',
                                'in_dir=\''+str(self.directory)+'\';\n',
                                'tr_dirs = dir([in_dir  \'/*.dcm\']);\n',
                                'num_training = length(tr_dirs);\n',
                                '%if more than one DICOMs in the folder\n',
                                'if (num_training>1)\n',
                                '\t%matrix of the orientation of each DICOMs\n',
                                '\tP=zeros(num_training,3);\n',
                                '\tfor i = 1:num_training\n',
                                '\t\t%read the header of the DICOM\n',
                                '\t\tDicom_header = dicominfo([in_dir \'/\' tr_dirs(i).name]);\n',
                                '\t\tP(i,:)=Dicom_header.ImagePositionPatient;\n',
                                '\tend\n',
                                '\t%Get the axes with the biggest variance = axes used by the scanner\n',
                                '\t[maxNumCol, maxIndexCol] = max(var(P));\n',
                                '\t%sort P \n',
                                '\t[Y,I]=sort(P(:,maxIndexCol));\n',
                                '\tP2=P(I,:);\n',
                                '\td =sqrt((P2(1:end-1,:)-P2(2:end,:)).*(P2(1:end-1,:)-P2(2:end,:)));\n',
                                '\t%difference between the max and the min\n',
                                '\tD=(max(d)- min(d));\n',
                                '\t%if this difference is bigger than 0.001, it means that one spacing\n',
                                '\t%between two slices is bigger than the spacing between the closest\n',
                                '\t%slices ---> some slices are missing\n',
                                '\tif (D(maxIndexCol)>0.001)\n',
                                '\t\tdisp(\'ERROR: Slices missing\')\n',
                                '\tend\n',
                                'end\n',
                              ]
                        f.writelines(lines) # Write a sequence of strings to a file
                    finally:
                        f.close()
                    #run it and check the output:
                    print '      -checking all DICOMs...'
                    call='matlab < '+os.path.join(self.directory,'callCheckDICOM.m')
                    try:
                        output = sb.check_output(call.split())
                        if 'ERROR' in output:
                            send_an_email=1
                            self.report('        ERROR: missing or duplicates slices in DICOM for Subject/Experiment : '+subject+'/'+experiment+'/'+scan)
                    except:
                        print "        ERROR: checking DICOMs failed."
                        
                    #remove the .m file:
                    os.remove(self.directory+'/callCheckDICOM.m')
                    
                    # convert dcm to nii
                    print '      -convert dcm to nii...'
                    dcm = os.path.join(self.directory,'1.dcm')
                    call = self.dcm2niipath+'/dcm2nii -a n -e n -d n -g y -f n -n y -p n -v y -x n -r n %(dcm)s' % {'dcm':dcm}
                    
                    try:
                        output = sb.check_output(call.split())
                    except sb.CalledProcessError:
                        print "      -DCM --> NII regular conversion failure\n"
                        print '      -dcmdjpeg on the dicom and call again dcm2nii.'
                        dirList=os.listdir(self.directory)
                        for dicoms in dirList:
                            number=dicoms.split('.')[0]
                            os.system('dcmdjpeg '+self.directory+'/'+dicoms+' '+self.directory+'/final_'+number+'.dcm')
                            os.remove(self.directory+'/'+dicoms)
                        dcm = os.path.join(self.directory ,'final_1.dcm')
                        call = self.dcm2niipath+'/dcm2nii -a n -e n -d n -g y -f n -n y -p n -v y -x n -r n %(dcm)s' % {'dcm':dcm}
                        try:
                            output = sb.check_output(call.split())
                        except sb.CalledProcessError:
                            print "      -DCM --> NII ( preprocess dicom with dcmdjpeg ) conversion failure\n"
                            send_an_email=1
                            self.report('ERROR: Fail to convert for Subject/Experiment : '+subject+'/'+experiment+'/'+scan) 
                            pass
                        
                    uploading=0 
                    number_of_nifti=0
                    #Create the resource:
                    Scan.resource('NIFTI').create()
                    #upload
                    for fname in os.listdir(self.directory):  
                        ext = os.path.splitext(fname)
                        if ext[1]=='.gz':
                            number_of_nifti+=1
                            uploading=1
                            # upload nii to XNAT
                            Scan.resource('NIFTI').file(fname).put(self.directory+'/'+fname)
                            print '                   upload '+fname+' to XNAT...'
                    
                    #more than one NIFTI uploaded
                    if number_of_nifti>1:
                        self.report('WARNING: more than one NIFTI upload for Subject/Experiment : '+subject+'/'+experiment+'/'+scan)
                        
                    #nothing upload
                    if uploading==0:
                        print '      -WARNING : Nothing upload.'
                        
                    # clean tmp folder 
                    self.clean_directory()
                    
                    
