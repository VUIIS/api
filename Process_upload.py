#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Created on Mar 13, 2013

@author: Benjamin Yvernault, Electrical Engineering, Vanderbilt University
'''

import os
import sys
import Spiders
from datetime import datetime
from pyxnat import Interface
from task import READY_TO_COMPLETE, COMPLETE, UPLOADING

def parse_args():
    from optparse import OptionParser
    usage = "usage: %prog [options] \nWhat is the script doing : Upload Data on Xnat from a Directory as an Assessor. "
    parser = OptionParser(usage=usage)
    parser.add_option("-e", "--emailaddress", dest="emailaddress",default='',
                  help="Email address to prevent if an assessor already exists.", metavar="EMAIL ADDRESS")
    return parser.parse_args()

def get_assessor_name_from_folder():
    #Get the assessor label from the folders in Upload Directory that are ready to be upload
    
    #Upload Directory 
    try:
        UploadDir = os.environ['UPLOAD_SPIDER_DIR']
    except KeyError as e:
        print "You must set the environment variable %s" % str(e)
        sys.exit(1) 
    
    #list of assessor label
    assessor_label_list=list()
    
    print ' -Get Processes names from the upload folder...'
    #check all files/folder in the directory
    UploadDirList=os.listdir(UploadDir)
    for assessor_label in UploadDirList:
        assessor_path=UploadDir+'/'+assessor_label
        #if it's a folder and not OUTLOG and the flag file READY_TO_UPLAOD exists
        if os.path.isdir(assessor_path) and assessor_label!='OUTLOG' and assessor_label!='TRASH' and assessor_label!='PBS' and os.path.exists(assessor_path+'/READY_TO_UPLOAD.txt'):
            if not os.path.exists(assessor_path+'/ALREADY_SEND_EMAIL.txt'):
                #it's a folder for an assessor:
                assessor_label_list.append(assessor_label)
            
    return assessor_label_list

def get_outlog_from_folder():
    #Get the outlog files which need to be upload
    
    #Upload Directory 
    try:
        UploadDir = os.environ['UPLOAD_SPIDER_DIR']
    except KeyError as e:
        print "You must set the environment variable %s" % str(e)
        sys.exit(1) 
    
    #list of assessor label
    outlog_list=list()
    
    print ' -Get the OUTLOG for the processes...'
    #check all files/folder in the directory
    OutlogDirList=os.listdir(UploadDir+'/OUTLOG')
    for outlog_name in OutlogDirList:
        outlog_file=UploadDir+'/OUTLOG/'+outlog_name
        #if it's a folder and not OUTLOG and the flag file READY_TO_UPLAOD exists
        if os.path.isfile(outlog_file):
            assessor_label=outlog_name[:-7]
            if os.path.isdir(UploadDir+'/'+assessor_label):
                os.mkdir(UploadDir+'/'+assessor_label+'/OUTLOG')
                os.system('mv '+outlog_file+' '+UploadDir+'/'+assessor_label+'/OUTLOG/')
            else:
                #it's a folder for an assessor:
                outlog_list.append(outlog_name)
            
    return outlog_list

def get_pbs_from_folder():
    #Get the pbs files which need to be upload
    
    #Upload Directory 
    try:
        UploadDir = os.environ['UPLOAD_SPIDER_DIR']
    except KeyError as e:
        print "You must set the environment variable %s" % str(e)
        sys.exit(1) 
    
    #list of assessor label
    pbs_list=list()
    
    print ' -Get the PBS for the processes...'
    #check all files/folder in the directory
    PBSDirList=os.listdir(UploadDir+'/PBS')
    for pbs_name in PBSDirList:
        pbs_file=UploadDir+'/PBS/'+pbs_name
        #if it's a folder and not OUTLOG and the flag file READY_TO_UPLAOD exists
        if os.path.isfile(pbs_file):
            #it's a folder for an assessor:
            pbs_list.append(pbs_name)
            
    return pbs_list

def set_check_assessor_status(assessor_label_list,emailaddress):
    #Set Uploading for the assessor who need to be upload (except if already complete)
    
    #for xnat connection
    try:
        # Environs
        VUIISxnat_user = os.environ['XNAT_USER']
        VUIISxnat_pwd = os.environ['XNAT_PASS']
        VUIISxnat_host = os.environ['XNAT_HOST']
        VUEMAIL_ADDR = os.environ['EMAIL_ADDR']
        VUEMAIL_PWS = os.environ['EMAIL_PWS']
    except KeyError as e:
        print "You must set the environment variable %s" % str(e)
        sys.exit(1) 
        
    #new assessor list which need to be upload :
    new_assessor_list=list()
    
    #Email variables :
    send_an_email=0;
    TEXT='\nThe following assessor already exists and the Spider try to upload files on existing files :\n'
    
    #connect to the experiment
    try:
        print ' -Connecting to XNAT to set status at '+VUIISxnat_host
        xnat = Interface(VUIISxnat_host, VUIISxnat_user, VUIISxnat_pwd)
        #Get the Project Name, the subject label, the experiment label and the assessor label from the file name :
        number_of_process=len(assessor_label_list)
        for index,assessor_label in enumerate(assessor_label_list):
            sys.stdout.flush()
            sys.stdout.write("  * Changing status: "+str(index+1)+"/"+str(number_of_process)+'\r')
            assessor_path=UploadDir+'/'+assessor_label
            labels=assessor_label.split('-x-')
            ProjectName=labels[0]
            Subject=labels[1]
            Experiment=labels[2]
            #The Process name is the last labels : if it's at scan level, labels[3]=scan, Process_name=labels[4]
            if len(labels)>4:
                Process_name=labels[4]
            else:
                Process_name=labels[3]
            
            #Select the right experiment :
            experiment = xnat.select('/project/'+ProjectName+'/subjects/'+Subject+'/experiments/'+Experiment)
            if experiment.exists():
                #ASSESSOR
                assessor=experiment.assessor(assessor_label)
                #existence :
                if assessor.datatype() == 'fs:fsData':
                    #set the status to Upload :
                    assessor.attrs.set('fs:fsData/procstatus', UPLOADING)
                    #add to the list:
                    new_assessor_list.append(assessor_label)
                elif assessor.exists():
                    #check status :
                    if assessor.attrs.get('proc:genProcData/procstatus') == COMPLETE or assessor.attrs.get('proc:genProcData/procstatus') == READY_TO_COMPLETE:
                        if not os.path.exists(assessor_path+'/ALREADY_SEND_EMAIL.txt'):
                            open(assessor_path+'/ALREADY_SEND_EMAIL.txt', 'w').close()
                        print 'Data already exist.\n'
                        TEXT+='\t- Project : '+ProjectName+' / Subject : '+Subject+' / Experiment : '+Experiment+' / Assessor label : '+ assessor_label+'\n'
                        send_an_email=1
                    else:
                        #set the status to Upload :
                        assessor.attrs.set('proc:genProcData/procstatus', UPLOADING)
                        #add to the list:
                        new_assessor_list.append(assessor_label)
                else:
                    #create the assessor and set the status 
                    assessor.create(assessors='proc:genProcData')
                    #Set attributes
                    assessor.attrs.set('proc:genProcData/procstatus', UPLOADING) #Set to uploading files
                    assessor.attrs.set('proc:genProcData/proctype', Process_name)
                    now=datetime.now()
                    today=str(now.year)+'-'+str(now.month)+'-'+str(now.day)
                    assessor.attrs.set('proc:genProcData/date',today)
                    #add to the list:
                    new_assessor_list.append(assessor_label)
            else:
                print 'ERROR: The folder '+assessor_label+' has a wrong ProjectName or Subject label or Experiment label.'
        
    finally:
        xnat.disconnect()
        
    #Sent an email
    if send_an_email and emailaddress!='':
        TEXT=TEXT+'\nYou should :\n\t-remove the assessor if you want to upload the data \n\t-set the status of the assessor to "uploading" \n\t-remove the data from the upload folder if you do not want to upload this data.\n'
        SUBJECT='SPider_Process_Upload -> Data already on Xnat'
        Spiders.sendMail(VUEMAIL_ADDR,VUEMAIL_PWS,emailaddress,SUBJECT,TEXT,'smtp.gmail.com') 
                
    return new_assessor_list

def Uploading_Assessor(xnat,assessor_path,ProjectName,Subject,Experiment,assessor_label):
    #SNAPSHOTS :
    #Check if the SNAPSHOTS folder exists, if not create one from PDF if pdf exists :
    if not os.path.exists(assessor_path+'/SNAPSHOTS/') and os.path.exists(assessor_path+'/PDF/'):
        print '    +creating original of SNAPSHOTS'
        os.system('mkdir '+assessor_path+'/SNAPSHOTS/')
        #Make the snapshots for the assessors with ghostscript
        snapshot_original = assessor_path+'/SNAPSHOTS/snapshot_original.png'
        os.system('gs -q -o '+snapshot_original+' -sDEVICE=pngalpha -dLastPage=1 '+assessor_path+'/PDF/*.pdf')
    
    #Create the preview snapshot from the original if Snapshots exist :
    if os.path.exists(assessor_path+'/SNAPSHOTS/'):
        Assessor_Resource_List=os.listdir(assessor_path+'/SNAPSHOTS/')
        for snapshot in Assessor_Resource_List:
            if len(snapshot.split('original'))>1:
                print '    +creating preview of SNAPSHOTS'
                #Name of the preview snapshot
                snapshot_preview = assessor_path+'/SNAPSHOTS/preview.'+snapshot.split('.')[1]
                #Make the snapshot_thumbnail
                os.system('convert '+assessor_path+'/SNAPSHOTS/'+snapshot+' -resize x200 '+snapshot_preview)                  
    
    #Select the experiment
    experiment = xnat.select('/project/'+ProjectName+'/subjects/'+Subject+'/experiments/'+Experiment)
        
    #Select the assessor
    assessor=experiment.assessor(assessor_label)
    
    #UPLOAD files :                
    Assessor_Resource_List=os.listdir(assessor_path)    
    #for each folder=resource in the assessor directory 
    for Resource in Assessor_Resource_List:
        Resource_path=assessor_path+'/'+Resource
        
        #Need to be in a folder to create the resource :
        if os.path.isdir(Resource_path):
            print '    +uploading '+Resource
            #check if the resource exist, if yes remove it
            if assessor.out_resource(Resource).exists():
                assessor.out_resource(Resource).delete()
            
            #create the resource
            r = assessor.out_resource(Resource)
                
            #if it's the SNAPSHOTS folder, need to set the thumbnail and original:
            if Resource=='SNAPSHOTS':
                #for each files in this folderl, Upload files in the resource :
                Resource_files_list=os.listdir(Resource_path)
                #for each folder=resource in the assessor directory 
                for filename in Resource_files_list:
                    #if it's a folder, zip it and upload it
                    if os.path.isdir(filename):
                        filenameZip=filename+'.zip'
                        os.system('zip '+filenameZip+' '+Resource_path+'/'+filename+'/*')
                        #upload
                        r.put_zip(Resource_path+'/'+filenameZip,extract=True)
                    #if it's the preview snapshot
                    elif os.path.splitext(filename)[0]=='preview':
                        r.file(filename).put(Resource_path+'/'+filename,(filename.split('.')[1]).upper(),'THUMBNAIL')
                    #if it's the original snapshot
                    elif len(filename.split('original'))>1:
                        r.file(filename).put(Resource_path+'/'+filename,(filename.split('.')[1]).upper(),'ORIGINAL')
                    else:
                        #upload the file
                        r.file(filename).put(Resource_path+'/'+filename)
            #for all the other resources :
            else:
                #for each files in this folderl, Upload files in the resource :
                Resource_files_list=os.listdir(Resource_path)
                #for each folder=resource in the assessor directory 
                for filename in Resource_files_list:
                    #if it's a folder, zip it and upload it
                    if os.path.isdir(filename):
                        filenameZip=filename+'.zip'
                        os.system('zip '+filenameZip+' '+Resource_path+'/'+filename+'/*')
                        #upload
                        r.put_zip(Resource_path+'/'+filenameZip,extract=True)
                    else:
                        #upload the file
                        r.file(filename).put(Resource_path+'/'+filename)
                        
    #upload finish
    assessor.attrs.set('proc:genProcData/procstatus', READY_TO_COMPLETE)
    os.system('rm -r '+assessor_path)

def Uploading_OUTLOG(outlog_list,xnat):
    number_outlog=len(outlog_list)
    for index,outlogfile in enumerate(outlog_list):
        print' *Uploading OUTLOG '+str(index+1)+'/'+str(number_outlog)+' -- File name: '+outlogfile
        #Get the Project Name, the subject label, the experiment label and the assessor label from the file name :
        labels=outlogfile.split('-x-')
        ProjectName=labels[0]
        Subject=labels[1]
        Experiment=labels[2]
        assessor_label=outlogfile.split('.')[0]
        
        #connect to the experiment
        experiment = xnat.select('/project/'+ProjectName+'/subjects/'+Subject+'/experiments/'+Experiment)
        if experiment.exists():
            #ASSESSOR
            assessor=experiment.assessor(assessor_label)
            #if the assessors doesn't exist send an email
            if assessor.exists():
                r=assessor.out_resource('OUTLOG')
                #if the resource exist, don't upload it
                procstatus = assessor.attrs.get('proc:genProcData/procstatus')
                if r.exists() and (procstatus == COMPLETE or procstatus == READY_TO_COMPLETE):
                    print 'WARNING : the OUTLOG resource already exists for the assessor '+assessor_label
                    print 'Copying the outlog file in the assessor folder if exists or in trash if not.'
                    #check if there is a folder with the same name : if yes, put the outlog there. If not upload it.
                    if  os.path.isdir(UploadDir+'/'+assessor_label):
                        if not os.path.exists(UploadDir+'/'+assessor_label+'/OUTLOG'):
                            os.mkdir(UploadDir+'/'+assessor_label+'/OUTLOG')
                        os.system('mv '+UploadDir+'/OUTLOG/'+outlogfile+' '+UploadDir+'/'+assessor_label+'/OUTLOG/')
                    else:
                        os.rename(UploadDir+'/OUTLOG/'+outlogfile,UploadDir+'/TRASH/'+outlogfile)
                else:
                    #remove the previous resource if exists 
                    if r.exists():
                        assessor.out_resource('OUTLOG').delete()
                        
                    #upload the file
                    r=assessor.out_resource('OUTLOG')
                    r.file(outlogfile).put(UploadDir+'/OUTLOG/'+outlogfile)
                    os.remove(UploadDir+'/OUTLOG/'+outlogfile)
            else:
                print 'ERROR: The assessor does not exist:'+assessor_label
                os.rename(UploadDir+'/OUTLOG/'+outlogfile,UploadDir+'/TRASH/'+outlogfile)
                
        else:
            print 'ERROR: The Output PBS file '+outlogfile+' has a wrong ProjectName or Subject label or Experiment label in his name.'
            os.rename(UploadDir+'/OUTLOG/'+outlogfile,UploadDir+'/TRASH/'+outlogfile)
            
    #remove the files that are not upload (being copy somewhere before
    Spiders.remove_files_directories_in_folder(UploadDir+'/OUTLOG/')

def Uploading_PBS(pbs_list,xnat):
    number_pbs=len(pbs_list)
    for index,pbsfile in enumerate(pbs_list):
        print' *Uploading PBS '+str(index+1)+'/'+str(number_pbs)+' -- File name: '+pbsfile
        #Get the Project Name, the subject label, the experiment label and the assessor label from the file name :
        labels=pbsfile.split('-x-')
        ProjectName=labels[0]
        Subject=labels[1]
        Experiment=labels[2]
        assessor_label=pbsfile.split('.')[0]
        
        #connect to the experiment
        experiment = xnat.select('/project/'+ProjectName+'/subjects/'+Subject+'/experiments/'+Experiment)
        if experiment.exists():
            #ASSESSOR
            assessor=experiment.assessor(assessor_label)
            #if the assessors doesn't exist send an email
            if assessor.exists():
                #remove the previous resource if exists
                r=assessor.out_resource('PBS')
                if r.exists():
                    assessor.out_resource('PBS').delete()
               
                #upload the file
                r=assessor.out_resource('PBS')
                r.file(pbsfile).put(UploadDir+'/PBS/'+pbsfile)
                os.remove(UploadDir+'/PBS/'+pbsfile)
            
            else:
                print 'ERROR: The assessor does not exist'
                os.rename(UploadDir+'/PBS/'+pbsfile,UploadDir+'/TRASH/'+pbsfile)
                
        else:
            print 'ERROR: The PBS file '+pbsfile+' has a wrong ProjectName or Subject label or Experiment label in his name.'
            os.rename(UploadDir+'/PBS/'+pbsfile,UploadDir+'/TRASH/'+pbsfile)
        
    #remove the files that are not upload (being copy somewhere before
    Spiders.remove_files_directories_in_folder(UploadDir+'/PBS/')
    
def Upload_FreeSurfer(xnat,assessor_path,ProjectName,Subject,Experiment,assessor_label):
    #SNAPSHOTS :
    #Check if the snapshot exists, if not create one from PDF if pdf exists :
    snapshot_original = assessor_path+'/SNAPSHOTS/snapshot_original.png'
    if not os.path.exists(snapshot_original) and os.path.exists(assessor_path+'/PDF/'):
        print '    +creating original of SNAPSHOTS'
        #Make the snapshots for the assessors with ghostscript
        os.system('gs -q -o '+snapshot_original+' -sDEVICE=pngalpha -dLastPage=1 '+assessor_path+'/PDF/*.pdf')
    
    #Create the preview snapshot from the original if Snapshots exist :
    if os.path.exists(assessor_path+'/SNAPSHOTS/'):
        Assessor_Resource_List=os.listdir(assessor_path+'/SNAPSHOTS/')
        for snapshot in Assessor_Resource_List:
            if len(snapshot.split('original'))>1:
                print '    +creating preview of SNAPSHOTS'
                #Name of the preview snapshot
                snapshot_preview = assessor_path+'/SNAPSHOTS/preview.'+snapshot.split('.')[1]
                #Make the snapshot_thumbnail
                os.system('convert '+assessor_path+'/SNAPSHOTS/'+snapshot+' -resize x200 '+snapshot_preview)                  
    
    #Select the experiment
    experiment = xnat.select('/project/'+ProjectName+'/subjects/'+Subject+'/experiments/'+Experiment)
        
    #Select the assessor
    assessor=experiment.assessor(assessor_label)
    
    # Upload the XML
    print '    +uploading XML'
    xml_files_list = os.listdir(assessor_path+'/'+'XML')
    if len(xml_files_list) != 1:
    	print 'ERROR:cannot upload FreeSufer, unable to find XML file:'+assessor_path
    	return
    xml_path = assessor_path+'/XML/'+xml_files_list[0]
    assessor.create(xml=xml_path, allowDataDeletion=False)
    
    #UPLOAD files :                
    Assessor_Resource_List=os.listdir(assessor_path)    
    #for each folder=resource in the assessor directory 
    for Resource in Assessor_Resource_List:
        Resource_path=assessor_path+'/'+Resource
        
        #Need to be in a folder to create the resource :
        if os.path.isdir(Resource_path):
            print '    +uploading '+Resource
            #check if the resource exist, if yes remove it
            if assessor.out_resource(Resource).exists():
                assessor.out_resource(Resource).delete()
            
            #create the resource
            r = assessor.out_resource(Resource)
                
            #if it's the SNAPSHOTS folder, need to set the thumbnail and original:
            if Resource=='SNAPSHOTS':
                #for each files in this folderl, Upload files in the resource :
                Resource_files_list=os.listdir(Resource_path)
                #for each folder=resource in the assessor directory 
                for filename in Resource_files_list:
                    #if it's a folder, zip it and upload it
                    if filename.lower().endswith('.zip'):
                    	r.put_zip(Resource_path+'/'+filename, extract=True)
                    elif os.path.isdir(filename):
                        filenameZip=filename+'.zip'
                        os.system('zip '+filenameZip+' '+Resource_path+'/'+filename+'/*')
                        #upload
                        r.put_zip(Resource_path+'/'+filenameZip,extract=True)
                    #if it's the preview snapshot
                    elif os.path.splitext(filename)[0]=='preview':
                        r.file(filename).put(Resource_path+'/'+filename,(filename.split('.')[1]).upper(),'THUMBNAIL')
                    #if it's the original snapshot
                    elif len(filename.split('original'))>1:
                        r.file(filename).put(Resource_path+'/'+filename,(filename.split('.')[1]).upper(),'ORIGINAL')
                    else:
                        #upload the file
                        r.file(filename).put(Resource_path+'/'+filename)
            #for all the other resources :
            else:
                #for each files in this folderl, Upload files in the resource :
                Resource_files_list=os.listdir(Resource_path)
                #for each folder=resource in the assessor directory 
                for filename in Resource_files_list:
                    #if it's a folder, zip it and upload it
                    if os.path.isdir(filename):
                        filenameZip=filename+'.zip'
                        os.system('zip '+filenameZip+' '+Resource_path+'/'+filename+'/*')
                        #upload
                        r.put_zip(Resource_path+'/'+filenameZip,extract=True)
                    elif filename.lower().endswith('.zip'):
                    	r.put_zip(Resource_path+'/'+filename, extract=True)
                    else:
                        #upload the file
                        r.file(filename).put(Resource_path+'/'+filename)
      
    #upload finish
    assessor.attrs.set('fs:fsdata/procstatus',READY_TO_COMPLETE)
    os.system('rm -r '+assessor_path)
    
#########################################################################################################################################################
###############################################################  MAIN FUNCTION ##########################################################################
#########################################################################################################################################################

if __name__ == '__main__':
    
    ################### Script for Upload FILES on Assessor on Xnat ######################
    (options,args) = parse_args()
    emailaddress = options.emailaddress
    
    print 'Time at the beginning of the Process_Upload: ', str(datetime.now()),'\n'

    #Upload Directory for Spider_Process_Upload.py
    try:
        # Environs
        VUIISxnat_user = os.environ['XNAT_USER']
        VUIISxnat_pwd = os.environ['XNAT_PASS']
        VUIISxnat_host = os.environ['XNAT_HOST']
        VUEMAIL_ADDR = os.environ['EMAIL_ADDR']
        VUEMAIL_PWS = os.environ['EMAIL_PWS']
        UploadDir = os.environ['UPLOAD_SPIDER_DIR']
    except KeyError as e:
        print "You must set the environment variable %s" % str(e)
        sys.exit(1) 
    
    #make the two special directory
    if not os.path.exists(UploadDir+'/OUTLOG'):
        os.mkdir(UploadDir+'/OUTLOG')
    if not os.path.exists(UploadDir+'/TRASH'):
        os.mkdir(UploadDir+'/TRASH')
    if not os.path.exists(UploadDir+'/PBS'):
        os.mkdir(UploadDir+'/PBS')    
    
    #check if this spider is still running for the former called by checking the flagfile Spider_Process_Upload_running.txt
    if not os.path.exists(UploadDir+'/Process_Upload_running.txt') and not os.path.exists(UploadDir+'/Spider_Process_Upload_running.txt'):
        #create the flag file showing that the spider is running 
        f=open(UploadDir+'/Process_Upload_running.txt', 'w')
        today=datetime.now()
        datestr="Date: "+str(today.year)+str(today.month)+str(today.day)+'_'+str(today.hour)+':'+str(today.minute)+':'+str(today.second)
        f.write(datesrt)
        f.close()
        
        try:
            #Start Uploading
            print '-------- Upload Directory: '+UploadDir+' --------'
            ###VARIABLES###
            #Check if the folder is not empty
            UploadDirList=os.listdir(UploadDir)
            if len(UploadDirList)==0:
                print 'WARNING: No data need to be upload.\n'
            else:
                #Get the assessor label from the directory :
                assessor_label_in_dir_list=get_assessor_name_from_folder()
                #Get the list of OUTLOG which need to be upload:
                outlog_list=get_outlog_from_folder()
                #Get the list of OUTLOG which need to be upload:
                pbs_list=get_pbs_from_folder()
                #Check the status of the assessor and set the assessor to upload if needed :
                assessor_label_upload_list=set_check_assessor_status(assessor_label_in_dir_list,emailaddress)
                
                #Start the process to upload
                try:
                    print 'INFO: Connecting to XNAT to start uploading processes at '+VUIISxnat_host
                    xnat = Interface(VUIISxnat_host, VUIISxnat_user, VUIISxnat_pwd)
                    
                    ################# 1) Upload the assessor data ###############
                    #For each assessor label that need to be upload :
                    number_of_processes=len(assessor_label_upload_list)
                    for index,assessor_label in enumerate(assessor_label_upload_list):
                        assessor_path=UploadDir+'/'+assessor_label
                        if os.path.isdir(assessor_path):
                            sys.stdout.flush()
                            sys.stdout.write("    *Process: "+str(index+1)+"/"+str(number_of_processes)+' -- label: '+assessor_label+'\n')
                            #Get the Project Name, the subject label, the experiment label and the assessor label from the folder name :
                            labels=assessor_label.split('-x-')
                            ProjectName=labels[0]
                            Subject=labels[1]
                            Experiment=labels[2]
                            #The Process name is the last labels : if scan so labels[3]=scan, Process_name=labels[4]
                            if len(labels)>4:
                                Process_name=labels[4]
                            else:
                                Process_name=labels[3]
                            
                            ############## Upload Assessor ###############
                            if Process_name=='FS':
                                #freesurfer upload :
                                Upload_FreeSurfer(xnat,assessor_path,ProjectName,Subject,Experiment,assessor_label)
                            else:
                                #Default upload:
                                Uploading_Assessor(xnat,assessor_path,ProjectName,Subject,Experiment,assessor_label)
                                
                                
                    ################# 2) Upload the Outlog files ###############
                    #For each file, upload it to the OUTLOG resource on the assessor
                    Uploading_OUTLOG(outlog_list,xnat)
                    
                    ################# 2) Upload the PBS files ###############
                    #For each file, upload it to the PBS resource
                    Uploading_PBS(pbs_list,xnat)
                    
                    
                #if fail, close the connection to xnat
                finally:                                        
                    xnat.disconnect()
                    print 'INFO: Connection to Xnat closed'  
        
        #Stop the process before the end or end of the script, remove the flagfile for the spider running 
        finally:
            #remove flagfile
            os.remove(UploadDir+'/Process_Upload_running.txt')
            print '===================================================================\n'
    else:
        print 'WARNING: Upload already running.'
        
