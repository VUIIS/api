from modules import SessionModule
import os
import XnatUtils

DEFAULT_TPM_PATH='/tmp/Unique_Series_Description_tmp/'
DEFAULT_MODULE_NAME='Unique_Series_Description'
DEFAULT_TEXT_REPORT='ERROR/WARNING for unique series description:\n'
DEFAULT_EMAIL='nan'

class Unique_Series_Description_Module(SessionModule):
    def __init__(self,module_name=DEFAULT_MODULE_NAME,directory=DEFAULT_TPM_PATH,email=DEFAULT_EMAIL,Text_report=DEFAULT_TEXT_REPORT):
        super(Unique_Series_Description_Module, self).__init__(module_name,directory,email,Text_report=DEFAULT_TEXT_REPORT)
        
    def prerun(self,settings_filename=''):
        pass
    
    def afterrun(self,xnat,project):
        if self.email!='nan' and self.send_an_email:
            try:
                EMAIL_ADDR = os.environ['EMAIL_ADDR']
                EMAIL_PWS = os.environ['EMAIL_PWS']
                self.sendReport(EMAIL_ADDR,EMAIL_PWS,self.email,'**ERROR/WARNING for '+self.module_name+'**','smtp.gmail.com')
            except KeyError as e:
                print "You must set the environment variable %s for next time to receive the report." % str(e)
    
    def run(self,xnat,project,subject,experiment):
        Experiment=xnat.select('/projects/'+project+'/subjects/'+subject+'/experiments/'+experiment)
        if Experiment.resource('series_checked').exists():
            print '      -Already run'
        else:
            Series_description=dict()
            
            for scan in XnatUtils.list_scans(xnat, project, subject ,experiment):
                if scan['quality']!='unusable':
                    Scan=xnat.select('/projects/'+project+'/subjects/'+subject +'/experiments/'+experiment +'/scans/'+scan['ID'] )
                    SD=Scan.attrs.get('series_description')
                    if SD !='':
                        if SD in Series_description:
                            Series_description[SD] += 1
                            Scan.attrs.set('series_description',SD+str(Series_description[SD]))
                            
                            #if it's the second time add the number to the first one
                            if Series_description[SD] == 2:
                                ScanNumber1=xnat.select('/projects/'+project+'/subjects/'+subject +'/experiments/'+experiment +'/scans/'+Series_description['X'+SD+'X'])
                                ScanNumber1.attrs.set('series_description',SD+'1')
                                
                        else:
                            Series_description[SD] = 1
                            # you don't know yet if you have to add the 1 (could be only one description) so add XdescriptionX = scanID of the first one
                            Series_description['X'+SD+'X'] = scan['ID']
                            
            #Create the flag resources on experiment level :
            Experiment.resource('series_checked').create()
            
        
                
                
                
                
                
                        
