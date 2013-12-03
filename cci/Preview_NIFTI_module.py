from modules import DEFAULT_MASIMATLAB_PATH,ScanModule
import XnatUtils
import os

DEFAULT_TPM_PATH='/tmp/Preview_NIFTI_tmp/'
DEFAULT_MODULE_NAME='Preview_NIFTI'
DEFAULT_TEXT_REPORT='ERROR/WARNING for preview NIFTI :\n'
DEFAULT_EMAIL='nan'

class Preview_NIFTI_Module(ScanModule):
    def __init__(self,module_name=DEFAULT_MODULE_NAME,directory=DEFAULT_TPM_PATH,email=DEFAULT_EMAIL,Text_report=DEFAULT_TEXT_REPORT,masimatlabpath=DEFAULT_MASIMATLAB_PATH):
        super(Preview_NIFTI_Module, self).__init__(module_name,directory,email,Text_report=DEFAULT_TEXT_REPORT)
        self.masimatlabpath=masimatlabpath
    
    def prerun(self):
        #make directory
        self.make_dir()    
        
    def afterrun(self,xnat,project):
        pass
                
    def run(self,xnat,projectName,subject,experiment,scan):
        Scan = xnat.select('/project/'+projectName+'/subject/'+subject+'/experiment/'+experiment+'/scan/'+scan)
        if Scan.resource('SNAPSHOTS').exists():
            print "      -Has snapshot."
        else:
            if Scan.resource('NIFTI').exists():
                if len(Scan.resource('NIFTI').files().get()) > 0:
                    print "      -downloading NIFTI..."
                    
                    dl,NIFTI_filename=XnatUtils.download_biggest_resources(Scan.resource('NIFTI'),self.directory)
                    
                    if not dl:
                        print '      -ERROR: NIFTI file size is zero.'
                    else:
                        smGif = os.path.join(self.directory,os.path.splitext(os.path.basename(NIFTI_filename))[0] + "_sm.gif")
                        lgGif = os.path.join(self.directory,os.path.splitext(os.path.basename(NIFTI_filename))[0] + "_lg.gif")
                        
                        #Matlab code to generate preview
                        f = open(self.directory+'/callpreview.m', "w")
                        try:
                            lines=[ 'addpath(genpath(\'' + self.masimatlabpath + '/trunk/xnatspiders/matlab/nii2gif/\'));\n',
                                    'addpath(genpath(\'' + self.masimatlabpath + '/trunk/xnatspiders/matlab/ext/\'));\n',
                                    'src = \'' + NIFTI_filename + '\'\n',
                                    'sm = \'' + smGif + '\'\n',
                                    'lg = \'' + lgGif + '\'\n',
                                    'makeNiiGifPreview(src,sm,lg)\n',
                                  ]
                            f.writelines(lines) # Write a sequence of strings to a file
                        finally:
                            f.close()
    
                        #call the matlab script (create a invisible window where it will put the display : solve oak problem)
                        print '      -Matlab script : '+self.directory+'/callpreview.m running ...'
                        
                        os.system('xvfb-run  -e '+self.directory+'/callpreview.err -f '+self.directory+'/callpreview.auth -a --server-args="-screen 0 1600x1280x24 -ac -extension GLX" matlab -nodesktop -nosplash < '+self.directory+'/callpreview.m > '+self.directory+'/matlabOutput.txt')
                        print '===================================================================\n'
                        
                        if os.path.isfile(smGif) : 
                            print '      -GIF Made'
                            Scan.resource('SNAPSHOTS').create()
                            Scan.resource('SNAPSHOTS').file('snap_t.gif').put(smGif,'GIF','THUMBNAIL');
                            Scan.resource('SNAPSHOTS').file('snap.gif').put(lgGif,'GIF','ORIGINAL');
                        else : 
                            print '      -GIF FAILED'
                            self.report('ERROR: GIF failed for NIFTI in '+projectName+'/'+subject+'/'+experiment+'/'+scan)
                
                        print '      -Cleaning up.'
                        self.clean_directory()
                        print '      -Done'
                    
                else:
                    print "    *ERROR : The size of the resource is 0."      
            else:
                print '    *No nifti.'
