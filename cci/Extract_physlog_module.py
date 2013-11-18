from modules import SessionModule
import XnatUtils
import os
import subprocess

DEFAULT_TPM_PATH='/tmp/Extract_physlog_tmp/'
DEFAULT_MODULE_NAME='Extract_physlog'
DEFAULT_TEXT_REPORT='ERROR/WARNING for extracting the physlog:\n'
DEFAULT_EMAIL='nan'

class Extract_physlog_Module(SessionModule):
    def __init__(self,module_name=DEFAULT_MODULE_NAME,directory=DEFAULT_TPM_PATH,email=DEFAULT_EMAIL,Text_report=DEFAULT_TEXT_REPORT):
        super(Extract_physlog_Module, self).__init__(module_name,directory,email,Text_report=DEFAULT_TEXT_REPORT)
    
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
                    
    def run(self,xnat,projectName,subject,experiment):
        EXPERIMENT=xnat.select('/projects/'+projectName+'/subjects/'+subject+'/experiments/'+experiment)
        if EXPERIMENT.resource('unpacked').exists():
            print '      -Already run'
        else:
	    print '      -Extracting the physlog'
            for scan in XnatUtils.list_scans(xnat, projectName, subject, experiment):
                Scan=xnat.select('/projects/'+projectName+'/subjects/'+subject+'/experiments/'+experiment+'/scans/'+scan['ID'])
                if Scan.resource('secondary').exists():
                    #Download
                    XnatUtils.download_all_resources(Scan.resource('secondary'),self.directory)
                    
                    #for files in the directory:
                    error=1
                    for filename in os.listdir(self.directory):
                        if os.path.getsize(os.path.join(self.directory,filename))==0:
                            self.report('ERROR: file with a size equal to zero for '+projectName+'/'+subject+'/'+experiment+'/'+scan['ID'])
                        else:
                            #rename the file with .zip extension:
                            os.rename(os.path.join(self.directory,filename),os.path.join(self.directory,os.path.splitext(filename)[0]+'.zip'))
                            
                            #make directory:
                            unzipDir=os.path.join(self.directory,'unzipdir')
                            if not os.path.exists(unzipDir):
                                os.mkdir(unzipDir)
                                
                            #unzip the files
                            file_full_path = os.path.join(self.directory,os.path.splitext(filename)[0]+'.zip')
                            p = subprocess.Popen(['/usr/bin/unzip',file_full_path,'-d',unzipDir], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            out, error = p.communicate()         
                            if not len(error)>400:
                                error=0
                                #rename all the files with the same name that the zip files.
                                for fname in os.listdir(unzipDir):
                                    #check the extension
                                    ext = os.path.splitext(fname)
                                    if ext[1]=='.log' or ext[1]=='.LOG' or ext[1]=='.xml' or ext[1]=='.XML':
                                        #double extension
                                        ext2 = ext[0].split('.')
                                        if ext2[len(ext2)-1]=='sql' or ext2[len(ext2)-1]=='SQL' or ext2[len(ext2)-1]=='scanphyslog' or ext2[len(ext2)-1]=='SCANPHYSLOG':
                                            #recup the subject/experiment/scan number (COULD BE A PROBLEM HERE IF THE PROJECT NAME HAS SEVERAL WORDS SEPARATED BY '_')
                                            #                                         (BUT USUALLY THE PROJECT NAME IS THE PI NAME WITHOUT '_')
                                            fname2 = filename+'.'+ext2[len(ext2)-1]+ext[1]
                                            os.rename(unzipDir+'/'+fname,self.directory+'/'+fname2)
                                
                                #Upload:
                                for fname in os.listdir(self.directory):
                                    if '.sql' in os.path.splitext(os.path.splitext(fname)[0]):
                                        if not Scan.resource('SQL_XML').exists():
                                            Scan.resource('SQL_XML').create()
                                            
                                        Scan.resource('SQL_XML').file(fname).put(os.path.join(self.directory,fname))
                                        
                                    elif '.scanphyslog' in os.path.splitext(os.path.splitext(fname)[0]):
                                        if not Scan.resource('PHYSLOG').exists():
                                            Scan.resource('PHYSLOG').create()
                                            
                                        Scan.resource('PHYSLOG').file(fname).put(os.path.join(self.directory,fname))
                                        
                            #clean
                            self.clean_directory()
                                    
                    if error:
                        self.record('ERROR: (not a proper zip) extract secondary files failed for '+projectName+'/'+subject+'/'+experiment+'/'+scan['ID'])
                        
            
            #create the flag resource on the experiment           
            EXPERIMENT.resource('unpacked').create()
                        
                        
                        
