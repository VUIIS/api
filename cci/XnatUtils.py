from pyxnat import Interface

def list_subjects(intf, projectid):
    post_uri = '/REST/projects/'+projectid+'/subjects'
    post_uri += '?columns=ID,project,label,URI'
    subject_list = intf._get_json(post_uri)
    return subject_list
    
def list_experiments(intf, projectid, subjectid):
    post_uri = '/REST/projects/'+projectid+'/subjects/'+subjectid+'/experiments'
    post_uri += '?columns=ID,URI,subject_label,subject_ID,modality,project,date,xsiType,label'
    experiment_list = intf._get_json(post_uri)
    return experiment_list
             
def list_scans(intf, projectid, subjectid, experimentid):
    post_uri = '/REST/projects/'+projectid+'/subjects/'+subjectid+'/experiments/'+experimentid+'/scans'
    post_uri += '?columns=ID,URI,project,type,quality,series_description,xsiType,note,frames,xnat:imageSessionData/project,xnat:imageSessionData/subject_id,xnat:imagesessiondata/id'
    scan_list = intf._get_json(post_uri)
    return scan_list

def list_scan_resources(intf, projectid, subjectid, experimentid, scanid):
    post_uri = '/REST/projects/'+projectid+'/subjects/'+subjectid+'/experiments/'+experimentid+'/scans/'+scanid+'/resources'
    resource_list = intf._get_json(post_uri)
    return resource_list

def list_assessors(intf, projectid, subjectid, experimentid):
    post_uri = '/REST/projects/'+projectid+'/subjects/'+subjectid+'/experiments/'+experimentid+'/assessors'
    assessor_list = intf._get_json(post_uri)
    return assessor_list

def list_assessor_out_resources(intf, projectid, subjectid, experimentid, assessorid):
    post_uri = '/REST/projects/'+projectid+'/subjects/'+subjectid+'/experiments/'+experimentid+'/assessors/'+assessorid+'/out/resources'
    resource_list = intf._get_json(post_uri)
    return resource_list

def get_full_object(intf,obj_dict):
    uri = obj_dict['URI']
    
    if 'scans' in uri:
        proj = obj_dict['xnat:imagesessiondata/project']
        subj = obj_dict['xnat:imagesessiondata/subject_id']
        sess = obj_dict['xnat:imagesessiondata/id']
        scan = obj_dict['ID']
        return intf.select('/project/'+proj+'/subject/'+subj+'/experiment/'+sess+'/scan/'+scan)
    elif 'experiments' in uri:
        proj = obj_dict['project']
        subj = obj_dict['subject_ID']
        sess = obj_dict['ID']
        return intf.select('/project/'+proj+'/subject/'+subj+'/experiment/'+sess)
    elif 'subjects' in uri:
        proj = obj_dict['project']
        subj = obj_dict['ID']
        return intf.select('/project/'+proj+'/subject/'+subj)
    else:
        return None
