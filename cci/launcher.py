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

def update_and_launch_jobs(max_job_count,project_process_dict,jobdir):
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
        intf = Interface(xnat_host, xnat_user, xnat_pass)

        # ===== First, update all tasks and build list of jobs to be run
        
        # iterate projects
        for projectid in project_list:
            print('=====PROJECT:'+projectid+'=====')
            
            # Clear processor lists
            scan_proc_list = []
            exp_proc_list = []
            
            # Build list of processors for this project
            for proc in project_process_dict[projectid]:
                if issubclass(proc.__class__,ScanProcessor):
                    scan_proc_list.append(proc)
                elif issubclass(proc.__class__,SessionProcessor):
                    exp_proc_list.append(proc)
                else:
                    print('ERROR:unknown processor type:'+proc)
            
            # iterate subjects
            for subj_dict in XnatUtils.list_subjects(intf, projectid):
                print('     SUBJECT:'+subj_dict['label'])
            
                # iterate experiments
                for exp_dict in XnatUtils.list_experiments(intf, projectid, subj_dict['ID']):
                    print('         SESSION:'+exp_dict['label'])

                    # iterate experiment level processors
                    for exp_proc in exp_proc_list:                    
                        if exp_proc.should_run(exp_dict):
                            exp_task = exp_proc.get_task(intf, exp_dict)
                            task_status = exp_task.update_status()
                            print('               '+exp_proc.name+':'+exp_task.assessor_label+' : '+task_status)
                            if task_status == task.READY_TO_RUN:
                                task_queue.append(exp_task)
                        
                    # iterate scans
                    for scan_dict in XnatUtils.list_scans(intf, projectid, subj_dict['ID'], exp_dict['ID']):
                        print('               SCAN:'+scan_dict['ID']+':'+scan_dict['type'])

                        # iterate scan level processors
                        for scan_proc in scan_proc_list:
                            if scan_proc.should_run(scan_dict):
                                scan_task = scan_proc.get_task(intf,scan_dict)
                                task_status = scan_task.update_status()
                                print('                    '+scan_proc.name+' : '+task_status)
                                if task_status == task.READY_TO_RUN:
                                    task_queue.append(scan_task)
                                
        #===== Sort the task queue as desired - random? breadth-first? depth-first? 
        print(str(len(task_queue))+' jobs ready to be launched.')
        #task_queue.sort()
        
        #===== Launch jobs
        cur_job_count = cluster.count_jobs()
        if cur_job_count == -1:
            print 'ERROR:cannot get count of jobs from cluster'
            return
        print(str(cur_job_count)+' jobs currently in queue')
            
        while cur_job_count <= max_job_count and len(task_queue)>0:
            print 'Launching job: currently '+str(cur_job_count)+' jobs in cluster queue'
            cur_task = task_queue.pop()
            # Confirm task is still ready to run
            if cur_task.get_status() == task.READY_TO_RUN:
                success = cur_task.launch(jobdir)
                if(success == True):
                    cur_job_count+=1
        
    finally:                                        
        intf.disconnect()
        print 'Connection to XNAT closed'
