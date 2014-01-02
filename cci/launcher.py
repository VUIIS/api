#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" launcher.py

"""
__copyright__ = 'Copyright 2013 Vanderbilt University. All Rights Reserved'

import os,sys
from pyxnat import Interface
from processors import ScanProcessor,SessionProcessor
import processors
import modules
import XnatUtils
import task
import cluster
from task import Task
from datetime import datetime, timedelta

DEFAULT_QUEUE_LIMIT = 300
DEFAULT_ROOT_JOB_DIR = '/tmp'
FULL_UPDATE_LOCK_FILE  = 'FULL_UPDATE_RUNNING.txt'
QUICK_UPDATE_LOCK_FILE  = 'QUICK_UPDATE_RUNNING.txt'
MODULES_LOCK_FILE='MODULES_RUNNING.txt'
UPDATE_FIELD = 'src'
UPDATE_FORMAT = "%Y-%m-%d %H:%M:%S"
UPDATE_PREFIX = 'updated--'

#TODO: add sort options

class Launcher(object):
    def __init__(self,project_process_dict,project_modules_dict,queue_limit=DEFAULT_QUEUE_LIMIT, root_job_dir=DEFAULT_ROOT_JOB_DIR, xnat_user=None, xnat_pass=None, xnat_host=None, upload_dir=None, job_email=None,job_email_options='bae'):
        self.queue_limit = queue_limit
        self.root_job_dir = root_job_dir
        self.project_process_dict = project_process_dict
        self.project_modules_dict = project_modules_dict
        self.job_email=job_email
        self.job_email_options=job_email_options

        try:
            if xnat_user == None:
                self.xnat_user = os.environ['XNAT_USER']
            else:
                self.xnat_user = xnat_user
                
            if xnat_pass == None:
                self.xnat_pass = os.environ['XNAT_PASS']
            else:
                self.xnat_pass = xnat_pass
                
            if xnat_host == None:
                self.xnat_host = os.environ['XNAT_HOST']
            else:
                self.xnat_host = xnat_host
        
            if upload_dir == None:
                self.upload_dir = os.environ['UPLOAD_SPIDER_DIR']
            else:
                self.upload_dir = upload_dir

        except KeyError as e:
            print("You must set the environment variable %s" % str(e))
            sys.exit(1)  
        
        #if project_process_dict == None:
            # TODO: get the default list of processors and get list of project 
            # this user has access to process here we could have the masispider 
            # user get all the projects it can access, so then users could just 
            # add masispider as a member of their project and it would process 
            # their data,good idea???

        # TODO: check the project process list
        # TODO: check that projects exist
                
    def update_open_tasks(self, settings_filename):
        task_queue = []
        
        print('\n-------------- Quick Update --------------')
        
        success = self.lock_quick_update(settings_filename)   
        if not success:
            print('ERROR:failed to get lock on quick update')
            exit(1)                              

        try:
            print('Connecting to XNAT at '+self.xnat_host)
            xnat = Interface(self.xnat_host, self.xnat_user, self.xnat_pass)
            
            print('Getting task list...')
            task_list = self.get_open_tasks(xnat)
            
            print(str(len(task_list))+' open jobs found')

            print('Updating tasks...')
            for cur_task in task_list:
                print('     Updating task:'+cur_task.assessor_label)
                task_status = cur_task.update_status()
                if task_status == task.NEED_TO_RUN:
                    task_queue.append(cur_task)
                    
            print(str(len(task_queue))+' jobs ready to be launched')
        
            #===== Sort the task queue as desired - random? breadth-first? depth-first? 
            #task_queue.sort()
                        
            # Launch jobs
            self.launch_jobs(task_queue)
            
        finally:       
            self.unlock_quick_update(settings_filename)                                                      
            xnat.disconnect()
            print('Connection to XNAT closed')
            
    def update_modules(self,settings_filename,mod_time=None):
        try:
            print('\n-------------- Run Modules --------------')
            print('Connecting to XNAT at '+self.xnat_host)
            xnat = Interface(self.xnat_host, self.xnat_user, self.xnat_pass)
         
            success = self.lock_setup_inputs(settings_filename)
            if not success:
                print('ERROR:failed to get lock on full update')
                exit(1)
         
            # List of projects:
            project_list = list(self.project_modules_dict.keys())
            
            # List of Modules:
            for project in project_list:
                print'\n=========== project: '+project+'==========='
                #prerun
                self.module_prerun(project)
                
                #run
                self.module_run(xnat,project,mod_time)
                
                #after run
                self.module_afterrun(xnat,project)
                        
        finally:       
            self.unlock_setup_inputs(settings_filename)                                 
            xnat.disconnect()
            print('Connection to XNAT closed')
                        
    def module_prerun(self,projectID):    
        # for all of the module
        for mod in self.project_modules_dict[projectID]:
            mod.prerun()
            
    def module_run(self,xnat,projectID, mod_time=None, check_mod=False):
        #get the different list:
        exp_mod_list, scan_mod_list = modules.modules_by_type(self.project_modules_dict[projectID])  
        
        # Querying through XNAT
        for subject in XnatUtils.list_subjects(xnat,projectID):            
            if mod_time != None:
                last_mod = datetime.strptime(subject['last_modified'][0:10],"%Y-%m-%d")
                if last_mod < mod_time:
                    print(' +Subject:'+subject['label']+', skipping subject, not modified')
                    continue

            if check_mod:
                last_mod = datetime.strptime(subject['last_modified'][0:19], '%Y-%m-%d %H:%M:%S')
                last_up = self.get_subj_lastupdate(subject)

                if last_up != None and last_mod < last_up:
                    print(' +Subject:'+subject['label']+', skipping subject, not modified,last_mod='+str(last_mod)+',last_up='+str(last_up))
                    continue
                            
            set_subj_lastupdate(subject)
            
            for experiment in XnatUtils.list_experiments(xnat, projectID, subject['ID']):
                #experiment Modules:
                print ' +Subject: '+subject['label']+' / Session: '+experiment['label']
                for exp_mod in exp_mod_list:
                    print'   * Module: '+exp_mod.getname()
                    exp_mod.run(xnat,projectID,subject['label'],experiment['label'])
                    
                #Scan Modules:
                if scan_mod_list:
                    for scan in XnatUtils.list_scans(xnat,projectID,subject['ID'],experiment['ID']):
                        print'   + Scan: '+scan['scan_id']
                        for scan_mod in scan_mod_list:
                            print'     * Module: '+scan_mod.getname()
                            scan_mod.run(xnat,projectID,subject['label'],experiment['label'],scan['scan_id'])
            
    def module_afterrun(self,xnat,projectID):    
        # for all of the module
        for mod in self.project_modules_dict[projectID]:
            mod.afterrun(xnat,projectID)
            
    def get_open_tasks(self, xnat):
        task_list = []
        project_list = list(self.project_process_dict.keys())
        
        # iterate projects
        for projectid in project_list:
            print('===== PROJECT:'+projectid+' =====')          

            # Get lists of processors for this project
            exp_proc_list, scan_proc_list = processors.processors_by_type(self.project_process_dict[projectid])
            
            # iterate experiments
            for exp_dict in XnatUtils.list_experiments(xnat, projectid):
                if 0: 
                    print('    SESS:'+exp_dict['label'])  
                task_list.extend(self.get_open_tasks_session(xnat, exp_dict, exp_proc_list, scan_proc_list))
                                  
        return task_list
    
    def get_open_tasks_session(self, xnat, sess_info, sess_proc_list, scan_proc_list):
        task_list = []
        projid = sess_info['project']
        subjid = sess_info['subject_ID']
        sessid = sess_info['ID']
        
        assr_list = XnatUtils.list_assessors(xnat, projid, subjid, sessid)
        for assr_info in assr_list:  
            task_proc = None
                        
            if assr_info['procstatus'] not in task.OPEN_STATUS_LIST and assr_info['qcstatus'] not in task.OPEN_QC_LIST:
                continue
              
            # Look for a match in sess processors
            for sess_proc in sess_proc_list:
                if sess_proc.xsitype == assr_info['xsiType'] and sess_proc.name == assr_info['proctype']:
                    task_proc = sess_proc
                    break
                        
            # Look for a match in scan processors
            if task_proc == None:
                for scan_proc in scan_proc_list:
                    if scan_proc.xsitype == assr_info['xsiType'] and scan_proc.name == assr_info['proctype']:
                        task_proc = scan_proc
                        break
                        
            if task_proc == None:
                print('WARN:no matching processor found:'+assr_info['assessor_label'])
                continue
          
            # Get a new task with the matched processor
            assr = XnatUtils.get_full_object(xnat, assr_info)
            cur_task = Task(task_proc,assr,self.upload_dir)
            task_list.append(cur_task)    
            
        return task_list
                            
    def get_desired_tasks_session(self, xnat, sess_info, sess_proc_list, scan_proc_list):
        task_list = []
        projid = sess_info['project']
        subjid = sess_info['subject_ID']
        sessid = sess_info['ID']
        
        # iterate session level processors
        for sess_proc in sess_proc_list:       
            if sess_proc.should_run(sess_info):
                sess_task = sess_proc.get_task(xnat, sess_info, self.upload_dir)
                task_list.append(sess_task)
                        
        # iterate scans
        for scan_info in XnatUtils.list_scans(xnat, projid, subjid, sessid):
            for scan_proc in scan_proc_list:
                if scan_proc.should_run(scan_info):
                    scan_task = scan_proc.get_task(xnat, scan_info, self.upload_dir)
                    task_list.append(scan_task)
        
        return task_list
        
    def update_session(self, xnat, sess_info, sess_proc_list, scan_proc_list, do_launch=True):
        task_list = self.get_session_tasks(xnat, sess_info, sess_proc_list, scan_proc_list)
        for cur_task in task_list:
            print('     Updating task:'+cur_task.assessor_label)
            task_status = cur_task.update_status()
            if task_status == task.NEED_TO_RUN and do_launch == True and cluster.count_jobs() < self.queue_limit:
                success = cur_task.launch(self.root_job_dir)
                if(success != True):
                    # TODO: change status???
                    print('ERROR:failed to launch job')
        
    def get_desired_tasks(self, xnat, mod_time=None, check_mod=False):
        task_list = []
        project_list = list(self.project_process_dict.keys())
  
        # iterate projects
        for projectid in project_list:  
            print('===== PROJECT:'+projectid+' =====')          
            # Get lists of processors for this project
            exp_proc_list, scan_proc_list = processors.processors_by_type(self.project_process_dict[projectid])   
            
            for subject in XnatUtils.list_subjects(xnat, projectid):    
                if check_mod:
                    last_mod = datetime.strptime(subject['last_modified'][0:19], '%Y-%m-%d %H:%M:%S')
                    last_up = self.get_subj_lastupdate(subject)
                                        
                    if last_up != None and last_mod < last_up:
                        print(' +Subject:'+subject['label']+', skipping subject, not modified,last_mod='+str(last_mod)+',last_up='+str(last_up))
                        continue
                                   
                self.set_subj_lastupdate(XnatUtils.get_full_object(xnat, subject))
                
                # iterate experiments
                for exp_dict in XnatUtils.list_experiments(xnat, projectid, subject['ID']):
                    print('    SESS:'+exp_dict['label'])   
                    task_list.extend(self.get_desired_tasks_session(xnat, exp_dict, exp_proc_list, scan_proc_list))

        return task_list
                                                
    def update(self, settings_filename, mod_time=None, check_mod=False):        
        print('\n-------------- Full Update --------------')
        
        success = self.lock_full_update(settings_filename)
        if not success:
            print('ERROR:failed to get lock on full update')
            exit(1)   
        
        try:
            print('Connecting to XNAT at '+self.xnat_host)
            xnat = Interface(self.xnat_host, self.xnat_user, self.xnat_pass)
            
            print('Getting task list...')
            task_list = self.get_desired_tasks(xnat, mod_time, check_mod)
            
            import datetime
            print('INFO:finished building list of tasks, now updating, Time='+str(datetime.datetime.now()))

            print('Updating tasks...')
            for cur_task in task_list:
                print('    Updating task:'+cur_task.assessor_label)
                task_status = cur_task.update_status()
                            
        finally:  
                self.unlock_full_update(settings_filename)                                 
                xnat.disconnect()
                print('Connection to XNAT closed')
                
    def launch_jobs(self, task_list):
        # Check cluster
        cur_job_count = cluster.count_jobs()
        if cur_job_count == -1:
            print('ERROR:cannot get count of jobs from cluster')
            return
        print(str(cur_job_count)+' jobs currently in queue')
        
        # Launch until we reach cluster limit or no jobs left to launch
        while cur_job_count < self.queue_limit and len(task_list)>0:
            cur_task = task_list.pop()
            
            # Confirm task is still ready to run
            if cur_task.get_status() != task.NEED_TO_RUN:
                continue
            
            print('Launching job:'+cur_task.assessor_label+', currently '+str(cur_job_count)+' jobs in cluster queue')
            success = cur_task.launch(self.root_job_dir,self.job_email,self.job_email_options)
            if(success != True):
                print('ERROR:failed to launch job')

            cur_job_count = cluster.count_jobs()
            if cur_job_count == -1:
                print('ERROR:cannot get count of jobs from cluster')
                return
                
    def lock_full_update(self,settings_filename):
        lock_file = self.upload_dir+'/'+settings_filename+'_'+FULL_UPDATE_LOCK_FILE
        
        if os.path.exists(lock_file):
            return False
        else:
            open(lock_file, 'w').close()
            return True
                
    def lock_quick_update(self,settings_filename):
        lock_file = self.upload_dir+'/'+settings_filename+'_'+QUICK_UPDATE_LOCK_FILE
        
        if os.path.exists(lock_file):
            return False
        else:
            open(lock_file, 'w').close()
            return True
        
    def lock_setup_inputs(self,settings_filename):
        lock_file = self.upload_dir+'/'+settings_filename+'_'+MODULES_LOCK_FILE
        
        if os.path.exists(lock_file):
            return False
        else:
            open(lock_file, 'w').close()
            return True
            
    def unlock_full_update(self,settings_filename):
        lock_file = self.upload_dir+'/'+settings_filename+'_'+FULL_UPDATE_LOCK_FILE
        
        if os.path.exists(lock_file):
           os.remove(lock_file)
                
    def unlock_quick_update(self,settings_filename):
        lock_file = self.upload_dir+'/'+settings_filename+'_'+QUICK_UPDATE_LOCK_FILE
        
        if os.path.exists(lock_file):
            os.remove(lock_file)
    
    def unlock_setup_inputs(self,settings_filename):
        lock_file = self.upload_dir+'/'+settings_filename+'_'+MODULES_LOCK_FILE
        
        if os.path.exists(lock_file):
            os.remove(lock_file)
            
    def get_subj_lastupdate(self, subj):
        update_time = subj[UPDATE_FIELD][len(UPDATE_PREFIX):]
        if update_time == '':
            return None
        else:
            return datetime.strptime(update_time, UPDATE_FORMAT)
                        
    def set_subj_lastupdate(self, subject):
        # We set update to one minute into the future since setting update field will change last modified time
        now = (datetime.now() + timedelta(minutes=1)).strftime(UPDATE_FORMAT)
        subject.attrs.set(UPDATE_FIELD, UPDATE_PREFIX+now)
