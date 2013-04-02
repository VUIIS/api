#!/usr/bin/env python
# -*- coding: utf-8 -*-

# cluster should know nothing about xnat or task or processor

""" cluster.py

Cluster functionality
"""
__copyright__ = 'Copyright 2013 Vanderbilt University. All Rights Reserved'
        
def count_jobs():
    cmd = "qstat | grep $USER | wc | awk {'print $1'}"
    
    try:
        output = check_output(cmd, stderr=STDOUT, shell=True)
        return int(output)
    except CalledProcessError:
        return -1
    
def job_status(jobid):
    cmd = "checkjob "+jobid+" | grep State | awk {'print $2'}"
    # TODO: handle invalid jobid, error message will look like this:
    # ERROR:  cannot locate job '42010'

class PBS:  
    #constructor
    def __init__(self,jobdir,outfile,email='',cmds='',walltime_str,mem_mb=1024):
        self.jobdir=jobdir
        self.outfile=outfile
        self.email=email
        self.cmds=cmds
        self.walltime_str=walltime_str
        self.mem_mb=mem_mb
 
    def write(self,filename):
        f = open(filename,'w')
        f.write('#!/bin/bash\n')
        f.write('#PBS -M ' + self.email+'\n')
        f.write('#PBS -m a \n')
        f.write('#PBS -l nodes=1:ppn=1\n')
        f.write('#PBS -l walltime='+walltime_str+'\n')
        f.write('#PBS -l mem=' + str(self.mem_mb) + 'mb\n')
        f.write('#PBS -o ' + self.outfile)
        f.write('#PBS -j oe '+ '\n')
        f.write('\n')        
        f.write('uname -a') # outputs node info (name, date&time, type, OS, etc)
        f.write('\n')
        
        # Write the shell commands
        for line in self.cmds:
            f.write(line+'\n')
    
    def setWalltime(self,walltime_str):
        self.walltime_str=walltime_str
    
    def getMemReqMb(self):
        return self.memreq_mb
    
    def setMemReqMb(self,mb):
        self.memreq_mb=mb
         
    def setCommands(self,cmds):
        self.cmds=cmds
        
    def setOutFile(self,outfile):
        self.outfile=outfile
    
    def submit(self,filename):
        try:
            cmd = 'qsub ' + filename
            output = subprocess.check_output(cmd)
            jobid = output.split('.')[0]
        except sb.CalledProcessError:
            jobid = ''
        
        return jobid
