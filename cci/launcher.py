#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" launcher.py

"""
__copyright__ = 'Copyright 2013 Vanderbilt University. All Rights Reserved'

import os
from pyxnat import Interface
from processors import ScanProcessor,SessionProcessor
import processors
import XnatUtils
import task
import cluster

DEFAULT_QUEUE_LIMIT = 50
DEFAULT_ROOT_JOB_DIR = '/gpfs21/scratch/'+os.getlogin()+'/tmp'

class Launcher(object):
    def __init__(self):
        self.queue_limit = DEFAULT_QUEUE_LIMIT
        self.root_job_dir = DEFAULT_ROOT_JOB_DIR

    def update_and_launch_jobs(self,project_process_dict):
        exp_count = 0
        scan_count = 0
        exp_task_count = 0
        scan_task_count = 0
        project_list = list(project_process_dict.keys())
        task_queue = []
    
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
    
            # ===== First, update all tasks and build list of jobs to be run
            
            # iterate projects
            for projectid in project_list:
                print('=====PROJECT:'+projectid+'=====')
                
                # Get lists of processors for this project
                exp_proc_list, scan_proc_list = processors.processors_by_type(project_process_dict[projectid])
                
                # iterate subjects
                for subj_dict in XnatUtils.list_subjects(xnat, projectid):
                    print('SUBJECT:'+subj_dict['label'])
                
                    # iterate experiments
                    for exp_dict in XnatUtils.list_experiments(xnat, projectid, subj_dict['ID']):
                        exp_count += 1
                        print('    SESSION:'+exp_dict['label'])
    
                        # iterate experiment level processors
                        for exp_proc in exp_proc_list:                    
                            if exp_proc.should_run(exp_dict):
                                exp_task_count += 1
                                exp_task = exp_proc.get_task(xnat, exp_dict)
                                task_status = exp_task.update_status()
                                print('        PROC:'+exp_proc.name+':'+exp_task.assessor_label+' : '+task_status)
                                if task_status == task.READY_TO_RUN:
                                    task_queue.append(exp_task)
                            
                        # iterate scans
                        for scan_dict in XnatUtils.list_scans(xnat, projectid, subj_dict['ID'], exp_dict['ID']):
                            scan_count += 1
                            print('        SCAN:'+scan_dict['ID']+':'+scan_dict['type'])
    
                            # iterate scan level processors
                            for scan_proc in scan_proc_list:
                                if scan_proc.should_run(scan_dict):
                                    scan_task_count += 1
                                    scan_task = scan_proc.get_task(xnat,scan_dict)
                                    task_status = scan_task.update_status()
                                    print('            PROC:'+scan_proc.name+' : '+task_status)
                                    if task_status == task.READY_TO_RUN:
                                        task_queue.append(scan_task)
                                        
            print str(exp_count)+' experiments'
            print str(exp_task_count)+' experiment tasks'
            print str(scan_count)+' scans'
            print str(scan_task_count)+' scan tasks'
              
            #===== Sort the task queue as desired - random? breadth-first? depth-first? 
            print(str(len(task_queue))+' jobs ready to be launched.')
            #task_queue.sort()
            
            #===== Launch jobs
            cur_job_count = cluster.count_jobs()
            if cur_job_count == -1:
                print 'ERROR:cannot get count of jobs from cluster'
                return
            print(str(cur_job_count)+' jobs currently in queue')
                
            while cur_job_count <= self.queue_limit and len(task_queue)>0:
                print 'Launching job: currently '+str(cur_job_count)+' jobs in cluster queue'
                cur_task = task_queue.pop()
                # Confirm task is still ready to run
                if cur_task.get_status() == task.READY_TO_RUN:
                    success = cur_task.launch(self.root_job_dir)
                    if(success == True):
                        cur_job_count+=1
            
        finally:                                        
            xnat.disconnect()
            print 'Connection to XNAT closed' 

def update_only(project_process_dict):
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
        
        # iterate projects
        for projectid in project_list:
            print('=====PROJECT:'+projectid+'=====')
            
            # Get lists of processors for this project
            exp_proc_list, scan_proc_list = processors_by_type(project_process_dict[projectid])
                
            # iterate subjects
            for subj_dict in XnatUtils.list_subjects(xnat, projectid):
                print('SUBJECT:'+subj_dict['label'])
            
                # iterate experiments
                for exp_dict in XnatUtils.list_experiments(xnat, projectid, subj_dict['ID']):
                    print('    SESSION:'+exp_dict['label'])

                    # iterate experiment level processors
                    for exp_proc in exp_proc_list:                    
                        if exp_proc.should_run(exp_dict):
                            exp_task = exp_proc.get_task(xnat, exp_dict)
                            task_status = exp_task.update_status()
                            print('        PROC:'+exp_proc.name+':'+exp_task.assessor_label+' : '+task_status)
                        
                    # iterate scans
                    for scan_dict in XnatUtils.list_scans(xnat, projectid, subj_dict['ID'], exp_dict['ID']):
                        print('        SCAN:'+scan_dict['ID']+':'+scan_dict['type'])

                        # iterate scan level processors
                        for scan_proc in scan_proc_list:
                            if scan_proc.should_run(scan_dict):
                                scan_task = scan_proc.get_task(xnat,scan_dict)
                                task_status = scan_task.update_status()
                                print('            PROC:'+scan_proc.name+' : '+task_status)
                                    
    finally:                                        
        xnat.disconnect()
        print 'Connection to XNAT closed'
        

