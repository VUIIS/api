#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" cluster.py

Cluster functionality
"""
__copyright__ = 'Copyright 2013 Vanderbilt University. All Rights Reserved'

import subprocess
from subprocess import CalledProcessError
import os

def count_jobs():
    cmd = "qstat | grep $USER | wc | awk {'print $1'}"
    
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
