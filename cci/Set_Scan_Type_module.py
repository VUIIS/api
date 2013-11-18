from modules import DEFAULT_MASIMATLAB_PATH,ScanModule
import os
import fileinput

DEFAULT_TPM_PATH='NONE'
DEFAULT_MODULE_NAME='Set_Scan_Type'
DEFAULT_TEXT_REPORT='ERROR/WARNING for setting scan type:\n'
DEFAULT_SCANTYPE_FILE_PATH=''
DEFAULT_EMAIL='nan'

class Set_Scan_Type_Module(ScanModule):
    def __init__(self,module_name=DEFAULT_MODULE_NAME,directory=DEFAULT_TPM_PATH,email=DEFAULT_EMAIL,Text_report=DEFAULT_TEXT_REPORT,masimatlabpath=DEFAULT_MASIMATLAB_PATH,scantype_file=DEFAULT_SCANTYPE_FILE_PATH):
        super(Set_Scan_Type_Module, self).__init__(module_name,directory,email,Text_report=DEFAULT_TEXT_REPORT)
        self.masimatlabpath=masimatlabpath
        self.scantype_file=scantype_file
        self.old_scan_type_list=list()
        self.new_scan_type_list=list()
    
    def prerun(self):
        #read text file
        if os.path.exists(self.scantype_file):
            for line in fileinput.input(self.scantype_file):
                stringline=line.split(';')
                scans_type=stringline[0].split('=')
                if len(scans_type)>1:
                    self.old_scan_type_list.append(scans_type[0])
                    self.new_scan_type_list.append(scans_type[1])
                    
    def afterrun(self,xnat,project):
        if self.email!='nan' and self.send_an_email:
            try:
                EMAIL_ADDR = os.environ['EMAIL_ADDR']
                EMAIL_PWS = os.environ['EMAIL_PWS']
                self.sendReport(EMAIL_ADDR,EMAIL_PWS,self.email,'**ERROR/WARNING for '+self.module_name+'**','smtp.gmail.com')
            except KeyError as e:
                print "You must set the environment variable %s for next time to receive the report." % str(e)
                                    
    def run(self,xnat,projectName,subject,experiment,scan):
        Scan=xnat.select('/projects/'+projectName+'/subjects/'+subject+'/experiments/'+experiment+'/scans/'+scan)
        if Scan.attrs.get('xnat:imageScanData/type') in self.old_scan_type_list:
            #INDEX
            INDEX_ScanType=self.old_scan_type_list.index(Scan.attrs.get('xnat:imageScanData/type'))
            #set the new scan type
            Scan.attrs.set('xnat:imageScanData/type',self.new_scan_type_list[INDEX_ScanType])
            
            
