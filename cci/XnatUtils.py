from pyxnat import Interface

def list_subjects(intf, projectid):
    post_uri_subject = '/REST/projects/'+projectid+'/subjects'
    subj_list = intf._get_json(post_uri_subject)
    return subject_list
    
def list_experiments(intf, projectid, subjectid):
    post_uri_experiment = '/REST/projects/'+projectid+'/subjects/'+subjectid+'/experiments'
    experiment_list = intf._get_json(post_uri_experiment)
    return experiment_list
             
def list_scans(intf, projectid, subjectid, experimentid):
    post_uri_scan = '/REST/projects/'+projectid+'/subjects/'+subjectid+'/experiments/'+experimentid+'/scans'
    scan_list = intf._get_json(post_uri_experiment)
    return scan_list

class SimpleXnatData(object):
    id
    
class SimpleProject(SimpleXnatData):
    def __init__(self,id):
        self.id=id

    def get_full_data(self,intf):
        return intf.select('/project/'+self.id)

class SimpleSubject(SimpleXnatData):
    projectid
    
    def __init__(self,projectid,id):
        self.id=id
        self.projectid=projectid
      
    def get_full_data(self,intf):
        return intf.select('/project/'+projectid+'/subject/'+self.id)
    
class SimpleSession(SimpleXnatData):
    subjectid
    projectid
    
    def __init__(self,projectid,subjectid,id):
        self.id=id
        self.projectid=projectid
        self.subjectid=subjectid

    def get_full_data(self,intf):
        return intf.select('/project/'+projectid+'/subject/'+subjectid+'/experiment/'+self.id)
    
class SimpleScan(SimpleXnatData):
    sessionid
    subjectid
    projectid
    
    def __init__(self,projectid,subjectid,sessionid,id):
        self.id=id
        self.projectid=projectid
        self.subjectid=subjectid
        self.sessionid=sessionid

    def get_full_data(self,intf):
        return intf.select('/project/'+projectid+'/subject/'+subjectid+'/experiment/'+sessionid+'/scan/'+self.id)
 
class SimpleAssessor(SimpleXnatData):
    subjectid
    projectid
    sessionid
    
    def __init__(self,projectid,subjectid,sessionid,id):
        self.id=id
        self.projectid=projectid
        self.subjectid=subjectid
        self.sessionid=sessionid

    def get_full_data(self,intf):
        return intf.select('/project/'+projectid+'/subject/'+subjectid+'/experiment/'+sessionid+'/assessor/'+self.id)
    
