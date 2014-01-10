from modules import DEFAULT_MASIMATLAB_PATH,ScanModule
import os
import subprocess as sub
import fileinput
import XnatUtils

DEFAULT_TPM_PATH='/tmp/dcm2nii_phillips_temp/'
DEFAULT_MODULE_NAME='dcm2nii_phillips'
DEFAULT_TEXT_REPORT='ERROR/WARNING for dcm2nii phillips :\n'
DEFAULT_EMAIL='nan'
DEFAULT_AVOID_SCANTYPE=['SURVEY','',' ','vuSuperPACSExportExam']

class dcm2nii_phillips_Module(ScanModule):
    def __init__(self,module_name=DEFAULT_MODULE_NAME,directory=DEFAULT_TPM_PATH,email=DEFAULT_EMAIL,Text_report=DEFAULT_TEXT_REPORT,masimatlabpath=DEFAULT_MASIMATLAB_PATH,avoid_scans_type=DEFAULT_AVOID_SCANTYPE):
        super(dcm2nii_phillips_Module, self).__init__(module_name,directory,email,Text_report=DEFAULT_TEXT_REPORT)
        self.masimatlabpath=masimatlabpath
        self.avoid_scans_type=avoid_scans_type
    
    def prerun(self,settings_filename=''):
        #make directory
        self.make_dir(settings_filename)
    
    def afterrun(self,xnat,project):
        if self.email!='nan' and self.send_an_email:
            try:
                EMAIL_ADDR = os.environ['EMAIL_ADDR']
                EMAIL_PWS = os.environ['EMAIL_PWS']
                self.sendReport(EMAIL_ADDR,EMAIL_PWS,self.email,'**ERROR/WARNING for '+self.module_name+'**','smtp.gmail.com')
            except KeyError as e:
                print "You must set the environment variable %s for next time to receive the report." % str(e)
        
        #clean the directory created
        try:   
            os.rmdir(self.directory)
        except:
            print'WARNING: '+self.directory+' not empty. Could not delete it.'

    def run(self,xnat,projectName,subject,experiment,scan):
        SCAN = xnat.select('/project/'+projectName+'/subject/'+subject+'/experiment/'+experiment+'/scan/'+scan)
    	if SCAN.attrs.get('xnat:imageScanData/type') in self.avoid_scans_type:
    	    print '      -Avoid this type'
    	else:
            if SCAN.resource('DICOM').exists():
                if not SCAN.resource('NIFTI').exists():
                    if len(SCAN.resource('DICOM').files().get()) > 0:
                        print '      -downloading DICOM...'
                        dl,DICOM_filename=XnatUtils.download_biggest_resources(SCAN.resource('DICOM'),self.directory,projectName+'-x-'+subject+'-x-'+experiment+'-x-'+SCAN.attrs.get('xnat:imageScanData/ID')+'.dcm')
                        
                        if not dl:
                            print '      -ERROR: NIFTI file size is zero.'
                        else:
                            #Convertion DICOM to PARREC philips (getstudy):
                            print "      -Convert dcm2parrec..."
                            PAR_file=DICOM_filename[:-3]+'PAR'
                            
                            try:
                                args=['perl',os.path.join(self.masimatlabpath,'trunk/xnatspiders/matlab/getStudyDcm2PARREC/getstudy_support_files/convert_dicom_to_xmlrec.pl'),'-a','-f',DICOM_filename,'-e',self.directory,'-m',self.masimatlabpath,'-p',os.path.splitext(os.path.basename(DICOM_filename))[0]]
                                p = sub.Popen(args,stdout=sub.PIPE,stderr=sub.PIPE)
                                output, errors = p.communicate()
                                
                                #old call
                                #os.system('perl '+self.masimatlab+'/trunk/xnatspiders/matlab/getStudyDcm2PARREC/getstudy_support_files/convert_dicom_to_xmlrec.pl -a -f '+DICOM_filename+' -e '+self.directory+ ' -m '+self.masimatlabpath+' -p '+os.path.splitext(os.path.basename(DICOM_filename))[0])
                            except OSError as e:
                                print '      -ERROR: dcm2parrec for '+DICOM_filename[:-4] +' failed ...'
                                print '       '+e
                                self.report('ERROR: dcm2parrec for '+DICOM_filename[:-4] +' failed : '+e)
                                pass
                            
                            if os.path.exists(PAR_file):
                                #Convertion PARREC to NIFTI philips (r2agui):
                                self.parrec2nifti(SCAN,PAR_file)
                                
                                ##### ZIPPING DATA AND UPLOAD #####
                                #Gzip REC and NIFTI
                                NII_file=DICOM_filename[:-3]+'nii'
                                os.system('gzip '+DICOM_filename[:-3]+'REC')
                                for fname in os.listdir(self.directory):
                                    ext = os.path.splitext(fname)
                                    if ext[1]=='.nii' or ext[1]=='.NII':
                                        os.rename(self.directory+'/'+fname,NII_file)
                                os.system('gzip '+NII_file)
                                
                                #Upload
                                print "      -Uploading resources..."
                                REC_file=DICOM_filename[:-3]+'REC.gz'
                                
                                #delete older files:
                                if SCAN.resource('PAR').exists:
                                    SCAN.resource('PAR').delete()
                                SCAN.resource('PAR').file(os.path.basename(PAR_file)).put(PAR_file)
                                if SCAN.resource('REC').exists:
                                    SCAN.resource('REC').delete()
                                SCAN.resource('REC').file(os.path.basename(REC_file)).put(REC_file)
                                if SCAN.resource('NIFTI').exists:
                                    SCAN.resource('NIFTI').delete()
                                SCAN.resource('NIFTI').file(os.path.basename(NII_file+'.gz')).put(NII_file+'.gz')
                                
                                #for DTI upload BVAL and BVEC:
                                if 'dti' in SCAN.attrs.get('xnat:imageScanData/type').lower() or 'dif' in SCAN.attrs.get('xnat:imageScanData/type').lower():
                                    BVAL_file=DICOM_filename[:-4]+'-x-bval.txt'
                                    BVEC_file=DICOM_filename[:-4]+'-x-bvec.txt'
                                    if SCAN.resource('BVAL').exists:
                                        SCAN.resource('BVAL').delete()
                                    SCAN.resource('BVAL').file(os.path.basename(BVAL_file)).put(BVAL_file)
                                    if SCAN.resource('BVEC').exists:
                                        SCAN.resource('BVEC').delete()
                                    SCAN.resource('BVEC').file(os.path.basename(BVEC_file)).put(BVEC_file)
                            
                        # clean tmp folder 
                        self.clean_directory()
                    
                    else:
                        print "      -WARNING : No DICOM resources."
                else:
                    print '      -Already a NIFTI'
            else:
                print '      -No Dicom'          
                    
    def parrec2nifti(self,Scan,filePAR):
        print "      -Convert parrec2nii..."
        #Data path
        data=os.path.split(filePAR)
        
        send_an_email=0
        
        #write the matlab script
        parrec2nifti_matlab_script=os.path.join(self.directory,'callconvert_r2a.m')
        f = open(parrec2nifti_matlab_script, "w")
        try:
            lines=[ '% Matlab Script to call convert_r2a function\n',
                    '% Path to convert_r2a.m \n',
                    'addpath(genpath(\''+self.masimatlabpath+'/trunk/xnatspiders/matlab/r2agui_vu_override/\'));\n',
                    'filePAR ={\'/'+str(data[1])+'\'};\n',
                    'directory_record=\''+str(self.directory)+'\';\n\n',
                    '% Write the option\n',
                    'options.subaan=1;\n',
                    'options.subsourceaan=0;\n',
                    'options.usealtfolder=0;\n',
                    'options.altfolder=\'\';\n',
                    'options.prefix=\'\';\n',
                    'options.pathpar=\''+data[0]+'\';\n',
                    'options.angulation=1;\n',
                    'options.rescale=1;\n',
                    'options.usefullprefix=0;\n',
                    'options.outputformat=1;\n',
                    'options.dim=4;\n',
                    'options.dti_revertb0=0;\n\n',
                    '% Call convert_r2a\n',
                    '[outfiles,file_error_size]=convert_r2a(filePAR,options);\n\n',
                    '% write the error on volumes in a text file\n',
                    'if (length(file_error_size)>0)\n',
                    '\tfName = strcat(directory_record,\'/report_r2agui.txt\');\n',
                    '\tfid = fopen(fName,\'w\');\n',           
                    '\tif fid ~= -1\n',
                    '\t\tfor i=1:length(file_error_size)\n',
                    '\t\t\tfprintf(fid,\'%s\\n\',file_error_size{i});\n',
                    '\t\tend\n',
                    '\telse\n',
                    '\t\tprintf(\'ERROR : File name for txt report invalid.\');\n',
                    '\tend\n',
                    'end\n'
                  ]
            f.writelines(lines) # Write a sequence of strings to a file
        finally:
            f.close()
        
        #call the matlab script
        #os.system('matlab -nodesktop -nosplash < '+parrec2nifti_matlab_script)
        args=['matlab','-nodesktop','-nosplash','<',parrec2nifti_matlab_script]
        p = sub.Popen(args,stdout=sub.PIPE,stderr=sub.PIPE)
        output, errors = p.communicate()
        
        #if the report from r2agui 
        if os.path.exists(self.directory+'/report_r2agui.txt'):
            for line in fileinput.input(self.directory+'/report_r2agui.txt'):
                self.report('ERROR: volumes does not match for'+line)
                Scan.attrs.set('quality','unusable')
        
