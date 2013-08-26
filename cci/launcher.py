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

DEFAULT_QUEUE_LIMIT = 50
DEFAULT_ROOT_JOB_DIR = '/tmp'

class Launcher(object):
    def __init__(self,queue_limit=DEFAULT_QUEUE_LIMIT, root_job_dir=DEFAULT_ROOT_JOB_DIR):
        self.queue_limit = queue_limit
        self.root_job_dir = root_job_dir
        # TODO: check for all env vars and stuff here
        
    def get_tasks(self, xnat, project_process_dict, upload_dir):
        task_list = []
        project_list = list(project_process_dict.keys())
  
        # iterate projects
        for projectid in project_list:  
            print '===== PROJECT:'+projectid+' ====='          
            # Get lists of processors for this project
            exp_proc_list, scan_proc_list = processors.processors_by_type(project_process_dict[projectid])
            
            # iterate subjects
            for subj_dict in XnatUtils.list_subjects(xnat, projectid):
                print '     SUBJ:'+subj_dict['label']          
 
                # iterate experiments
                for exp_dict in XnatUtils.list_experiments(xnat, projectid, subj_dict['ID']):
                    print '          SESS:'+exp_dict['label']          

                    # iterate experiment level processors
                    for exp_proc in exp_proc_list:                    
                        if exp_proc.should_run(exp_dict):
                            exp_task = exp_proc.get_task(xnat, exp_dict, upload_dir)
                            task_list.append(exp_task)
                        
                    # iterate scans
                    for scan_dict in XnatUtils.list_scans(xnat, projectid, subj_dict['ID'], exp_dict['ID']):
    
                        # iterate scan level processors
                        for scan_proc in scan_proc_list:
                            if scan_proc.should_run(scan_dict):
                                scan_task = scan_proc.get_task(xnat,scan_dict, upload_dir)
                                task_list.append(scan_task)
        
        return task_list
                                                
    def update(self,project_process_dict):
        project_list = list(project_process_dict.keys())
        task_queue = []
    
        try:
            # Environs
            xnat_user = os.environ['XNAT_USER']
            xnat_pass = os.environ['XNAT_PASS']
            xnat_host = os.environ['XNAT_HOST']
            upload_dir = os.environ['UPLOAD_SPIDER_DIR']
        except KeyError as e:
            print "You must set the environment variable %s" % str(e)
            sys.exit(1)  
            
        try:
            print 'Connecting to XNAT'
            xnat = Interface(xnat_host, xnat_user, xnat_pass)
            
            print 'Getting task list...'
            task_list = self.get_tasks(xnat,project_process_dict, upload_dir)
            
            print 'Updating tasks...'
            for cur_task in task_list:
                print '     Updating task:'+cur_task.assessor_label
                task_status = cur_task.update_status()
                if task_status == task.READY_TO_RUN:
                    task_queue.append(cur_task)
              
            #===== Sort the task queue as desired - random? breadth-first? depth-first? 
            print(str(len(task_queue))+' jobs ready to be launched')
            #task_queue.sort()
            
            #===== Launch jobs
            cur_job_count = cluster.count_jobs()
            if cur_job_count == -1:
                print 'ERROR:cannot get count of jobs from cluster'
                return
            print(str(cur_job_count)+' jobs currently in queue')
                
            while cur_job_count <= self.queue_limit and len(task_queue)>0:
                cur_task = task_queue.pop()
                
                # Confirm task is still ready to run
                if cur_task.get_status() != task.READY_TO_RUN:
                    continue
                
                print 'Launching job:'+cur_task.assessor_label+', currently '+str(cur_job_count)+' jobs in cluster queue'
                success = cur_task.launch(self.root_job_dir)
                if(success == True):
                    cur_job_count+=1
                else:
                    print 'ERROR:failed to launch job'
            
        finally:                                        
            xnat.disconnect()
            print 'Connection to XNAT closed' 
    
    def update_only(self,project_process_dict):
        project_list = list(project_process_dict.keys())
    
        try:
            # Environs
            xnat_user = os.environ['XNAT_USER']
            xnat_pass = os.environ['XNAT_PASS']
            xnat_host = os.environ['XNAT_HOST']
        except KeyError as e:
            print "You must set the environment variable %s" % str(e)
            sys.exit(1)  
            
        try:
            print 'Connecting to XNAT'
            xnat = Interface(xnat_host, xnat_user, xnat_pass)
            
            print 'Getting task list'
            task_list = self.get_tasks(xnat,project_process_dict)
            
            for cur_task in task_list:
                print '     Updating task:'+task.assessor_label
                task_status = cur_task.update_status()
                                        
        finally:                                        
            xnat.disconnect()
            print 'Connection to XNAT closed'
        
    def relaunch_failed(self,project_process_dict):
        project_list = list(project_process_dict.keys())
        task_queue = []
    
        try:
            # Environs
            xnat_user = os.environ['XNAT_USER']
            xnat_pass = os.environ['XNAT_PASS']
            xnat_host = os.environ['XNAT_HOST']
            upload_dir = os.environ['UPLOAD_SPIDER_DIR']

        except KeyError as e:
            print "You must set the environment variable %s" % str(e)
            sys.exit(1)  
            
        try:
            print 'Connecting to XNAT'
            xnat = Interface(xnat_host, xnat_user, xnat_pass)    
                    
            print 'Getting task list...'
            task_list = self.get_tasks(xnat,project_process_dict)
            
            for cur_task in task_list:
                print '     Updating task:'+task.assessor_label
                task_status = cur_task.update_status()
                if cur_task.get_status() == task.JOB_FAILED:
                    task_queue.append(cur_task)
                        
            # Launch jobs
            print(str(len(task_queue))+' jobs to relaunch')
            cur_job_count = cluster.count_jobs()
            if cur_job_count == -1:
                print 'ERROR:cannot get count of jobs from cluster'
                return
            else:
                print(str(cur_job_count)+' jobs already in queue')
                
            while cur_job_count <= self.queue_limit and len(task_queue)>0:
                cur_task = task_queue.pop()
                
                # Confirm task is still failed
                if cur_task.get_status() != task.JOB_FAILED:
                    continue
                
                print 'Launching job:'+cur_task.assessor_label+', currently '+str(cur_job_count)+' jobs in cluster queue'
                success = cur_task.launch(self.root_job_dir)
                if(success == True):
                    cur_job_count+=1
                else:
                    print 'ERROR:failed to launch job'
            
            print 'Finished launching jobs'
            
        finally:                                        
            xnat.disconnect()
            print 'XNAT connection closed'

