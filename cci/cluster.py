#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" cluster.py

Cluster functionality
"""
__copyright__ = 'Copyright 2013 Vanderbilt University. All Rights Reserved'

import subprocess
from subprocess import CalledProcessError
import os
from datetime import datetime

MAX_TRACE_DAYS=30

def count_jobs():
    cmd = "qstat | grep $USER | wc -l"
    
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
        return int(output)
    except (CalledProcessError,ValueError):
        return -1
    
def job_status(jobid):
    cmd = "qstat -f "+str(jobid)+" | grep job_state | awk {'print $3'}"
    # TODO: handle invalid jobid, error message will look like this:
    # "qstat: Unknown Job Id Error jobid"
    
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
        output = output.strip()
        return output
    except CalledProcessError:
        return ''      
  
def is_traceable_date(jobdate):
    try:
        trace_date = datetime.strptime(jobdate,"%Y-&m-%d")
        today = datetime.today()
        diff_days = (datetime.today() - d).days
        return diff_days <= MAX_TRACE_DAYS
    except ValueError:
        return False
    
def tracejob_info(jobid, jobdate):
    d = datetime.strptime(d1, "%Y-%m-%d")
    diff_days = (datetime.today() - d).days
    jobinfo['mem_used'] = ''
    jobinfo['walltime_used'] = ''
    
    cmd='rsh vmpsched "tracejob -n '+str(diff_days)+' '+jobid+'"'    
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
        
        if 'Exit_status' in output:
            #get the walltime used
            tmpstr = output[0].split('resources_used.walltime=')
            if len(tmpstr) > 1:
                jobinfo['walltime_used'] = tmpstr[1].split('\n')
       
            #get the mem used
            tmpstr = output[0].split('resources_used.mem=')
            if len(tmpstr) > 1:
                jobinfo['mem_used'] = tmpstr[1].split('kb')[0]+'kb'
                
    except CalledProcessError:
        pass
    
    return jobinfo
  
class PBS:  
    #constructor
    def __init__(self,filename,outfile,cmds,walltime_str,mem_mb=2048,email=''):
        self.filename=filename
        self.outfile=outfile
        self.cmds=cmds
        self.walltime_str=walltime_str
        self.mem_mb=mem_mb
        self.email=email

    def write(self):
        pbs_dir = os.path.dirname(self.filename)
        if not os.path.exists(pbs_dir):
            os.makedirs(pbs_dir)
        
        f = open(self.filename,'w')
        f.write('#!/bin/bash\n')
        if self.email != '':
            f.write('#PBS -M ' + self.email+'\n')
            f.write('#PBS -m ae \n')
        f.write('#PBS -l nodes=1:ppn=1\n')
        f.write('#PBS -l walltime='+str(self.walltime_str)+'\n')
        f.write('#PBS -l mem=' + str(self.mem_mb) + 'mb\n')
        f.write('#PBS -o ' + self.outfile+'\n')
        f.write('#PBS -j oe '+ '\n')
        f.write('\n')        
        f.write('uname -a') # outputs node info (name, date&time, type, OS, etc)
        f.write('\n')
        
        # Write the shell commands
        for line in self.cmds:
            f.write(line+'\n')

    def submit(self):
        try:
            cmd = 'qsub ' + self.filename
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
            jobid = output.split('.')[0]
        except CalledProcessError:
            jobid = '0'
        
        return jobid
    
