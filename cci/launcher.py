#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" launcher.py

"""
__copyright__ = 'Copyright 2013 Vanderbilt University. All Rights Reserved'

def launch_jobs(max_job_count,project_process_list,jobdir):
    # TODO: create per exp processor and per scan processor lists from project_process_list
    
    try:
        intf = Interface(xnat_host, xnat_user, xnat_pwd)
        task_queue = []
        
        # First, update all tasks and build list of jobs to be run
        
        # iterate projects
        for projectid in project_list:
        
            # iterate subjects
            for subject in xnat.list_subjects(intf, projectid):
            
                # iterate experiments
                for experiment in xnat.list_experiments(intf, projectid, subject['ID']):
                
                    # iterate experiment level processors
                    for exp_proc in exp_proc_list:
                        if exp_proc.may_run(experiment):
                            task = exp_proc.get_task(intf, projectid, subjectid, experimentid)
                            task.update_status()
                            if task.get_status() == task.READY_TO_RUN:
                                task_queue.append(task)
                        
                    # iterate scans
                    for scan in xnat.list_scans(intf, projectid, subject['ID'], experiment['ID']):
        
                        # iterate scan level processors
                        for scan_proc in scan_proc_list:
                            if scan_proc.may_run(scan):
                                task = scan_proc.get_task(scan)
                                task.update_status()
                                if task.get_status() == task.READY_TO_RUN:
                                    task_queue.append(task)
                                
        # Sort the task queue as desired - random? breadth-first? depth-first? 
        #task_queue.sort()
        
        # Launch jobs
        cur_job_count = cluster.count_jobs()
        if cur_job_count == -1:
            # Error getting job count
            return
            
        while cur_job_count <= max_job_count:
            task = task_queue.pop()
            # Confirm task is still ready to run
            if task.get_status() == task.READY_T0_RUN:
                task.set_status(task.RUNNING)
                task.launch() # write PBS, submit PBS
                cur_job_count+=1

    finally:
        # close XNAT connection
        intf.disconnect()
