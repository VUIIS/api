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
