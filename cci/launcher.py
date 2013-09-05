#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" launcher.py

"""
__copyright__ = 'Copyright 2013 Vanderbilt University. All Rights Reserved'

import os,sys
from pyxnat import Interface
from processors import ScanProcessor,SessionProcessor
import processors
import XnatUtils
import task
import cluster
from task import Task

DEFAULT_QUEUE_LIMIT = 1000
DEFAULT_ROOT_JOB_DIR = '/tmp'

#TODO: add sort options

class Launcher(object):
    def __init__(self,project_process_dict,queue_limit=DEFAULT_QUEUE_LIMIT, root_job_dir=DEFAULT_ROOT_JOB_DIR, xnat_user=None, xnat_pass=None, xnat_host=None, upload_dir=None):
        self.queue_limit = queue_limit
        self.root_job_dir = root_job_dir
        self.project_process_dict = project_process_dict
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
            print "You must set the environment variable %s" % str(e)
            sys.exit(1)  
        
        #if project_process_dict == None:
            # TODO: get the default list of processors and get list of project 
            # this user has access to process here we could have the masispider 
            # user get all the projects it can access, so then users could just 
            # add masispider as a member of their project and it would process 
            # their data,good idea???

        # TODO: check the project process list
                
    def update_open_tasks(self):
        task_queue = []
                
        try:
            print 'Connecting to XNAT at '+self.xnat_host
            xnat = Interface(self.xnat_host, self.xnat_user, self.xnat_pass)
            
            print 'Getting task list...'
            task_list = self.get_open_tasks(xnat)
            
            print(str(len(task_list))+' open jobs found')

            print 'Updating tasks...'
            for cur_task in task_list:
                print '     Updating task:'+cur_task.assessor_label
                task_status = cur_task.update_status()
                if task_status == task.NEED_TO_RUN:
                    task_queue.append(cur_task)
                    
            print(str(len(task_queue))+' jobs ready to be launched')
        
            #===== Sort the task queue as desired - random? breadth-first? depth-first? 
            #task_queue.sort()
                        
            # Launch jobs
            self.launch_jobs(task_queue)
            
        finally:                                        
            xnat.disconnect()
            print 'Connection to XNAT closed' 
            
    def get_open_tasks(self, xnat):
        task_list = []
        project_list = list(self.project_process_dict.keys())
        
        # iterate projects
        for projectid in project_list:
            print '===== PROJECT:'+projectid+' ====='          

            # Get lists of processors for this project
            exp_proc_list, scan_proc_list = processors.processors_by_type(self.project_process_dict[projectid])
            
            # iterate experiments
            for exp_dict in XnatUtils.list_experiments(xnat, projectid):
                print '    SESS:'+exp_dict['label']     
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
            
            if assr_info['procstatus'] not in task.OPEN_STATUS_LIST:
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
                print 'WARN:no matching processor found:'+assr_info['assessor_label']
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
            print '     Updating task:'+cur_task.assessor_label
            task_status = cur_task.update_status()
            if task_status == task.NEED_TO_RUN and do_launch == True and cluster.count_jobs() < self.queue_limit:
                success = cur_task.launch(self.root_job_dir)
                if(success != True):
                    # TODO: change status???
                    print 'ERROR:failed to launch job'
        
    def get_desired_tasks(self, xnat):
        task_list = []
        project_list = list(self.project_process_dict.keys())
  
        # iterate projects
        for projectid in project_list:  
            print '===== PROJECT:'+projectid+' ====='          
            # Get lists of processors for this project
            exp_proc_list, scan_proc_list = processors.processors_by_type(self.project_process_dict[projectid])        
 
            # iterate experiments
            for exp_dict in XnatUtils.list_experiments(xnat, projectid):
                print '    SESS:'+exp_dict['label']     
                task_list.extend(self.get_desired_tasks_session(xnat, exp_dict, exp_proc_list, scan_proc_list))

        return task_list
                                                
    def update(self):
        task_queue = []
                
        try:
            print 'Connecting to XNAT at '+self.xnat_host
            xnat = Interface(self.xnat_host, self.xnat_user, self.xnat_pass)
            
            print 'Getting task list...'
            task_list = self.get_desired_tasks(xnat)
            
            print 'Updating tasks...'
            for cur_task in task_list:
                print '    Updating task:'+cur_task.assessor_label
                task_status = cur_task.update_status()
                if task_status == task.NEED_TO_RUN:
                    task_queue.append(cur_task)
              
            #===== Sort the task queue as desired - random? breadth-first? depth-first? 
            print(str(len(task_queue))+' jobs ready to be launched')
            #task_queue.sort()
            
            # Launch jobs
            self.launch_jobs(task_queue)
            
        finally:                                        
            xnat.disconnect()
            print 'Connection to XNAT closed' 
    
    def update_status_only(self):            
        try:
            print 'Connecting to XNAT at '+self.xnat_host
            xnat = Interface(self.xnat_host, self.xnat_user, self.xnat_pass)
            
            print 'Getting task list'
            task_list = self.get_tasks(xnat)
            
            for cur_task in task_list:
                print '     Updating task:'+task.assessor_label
                cur_task.update_status()
                                        
        finally:                                        
            xnat.disconnect()
            print 'Connection to XNAT closed'
        
    def relaunch_failed(self):
        task_queue = []
            
        try:
            print 'Connecting to XNAT at '+self.xnat_host
            xnat = Interface(self.xnat_host, self.xnat_user, self.xnat_pass)    
                    
            print 'Getting task list...'
            task_list = self.get_tasks(xnat)
            
            # Change failed tasks to need run and add to queue
            for cur_task in task_list:
                print '     Updating task:'+task.assessor_label
                task_status = cur_task.update_status()
                if cur_task.get_status() == task.JOB_FAILED:
                    cur_task.set_status(task.NEED_TO_RUN)
                    task_queue.append(cur_task)
                        
            # Launch jobs
            print(str(len(task_queue))+' jobs to relaunch')
            self.launch_jobs(task_queue)
            print 'Finished launching jobs'
        finally:                                        
            xnat.disconnect()
            print 'XNAT connection closed'
            
    def launch_jobs(self, task_list):
        # Check cluster
        cur_job_count = cluster.count_jobs()
        if cur_job_count == -1:
            print 'ERROR:cannot get count of jobs from cluster'
            return
        print(str(cur_job_count)+' jobs currently in queue')
        
        # Launch until we reach cluster limit or no jobs left to launch
        while cur_job_count <= self.queue_limit and len(task_list)>0:
            cur_task = task_list.pop()
            
            # Confirm task is still ready to run
            if cur_task.get_status() != task.NEED_TO_RUN:
                continue
            
            print 'Launching job:'+cur_task.assessor_label+', currently '+str(cur_job_count)+' jobs in cluster queue'
            success = cur_task.launch(self.root_job_dir)
            if(success == True):
                cur_job_count+=1
            else:
                print 'ERROR:failed to launch job'
