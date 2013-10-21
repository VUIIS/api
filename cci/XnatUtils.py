from pyxnat import Interface

def list_subjects(intf, projectid=None):
    if projectid:
        post_uri = '/REST/projects/'+projectid+'/subjects'
    else:
        post_uri = '/REST/subjects'

    post_uri += '?columns=ID,project,label,URI'
    subject_list = intf._get_json(post_uri)
    return subject_list
    
def list_experiments(intf, projectid=None, subjectid=None):
    if projectid and subjectid:
        post_uri = '/REST/projects/'+projectid+'/subjects/'+subjectid+'/experiments'
    elif projectid == None and subjectid == None:
        post_uri = '/REST/experiments'
    elif projectid and subjectid == None:
        post_uri = '/REST/projects/'+projectid+'/experiments'
    else:
        return None
    
    post_uri += '?columns=ID,URI,subject_label,subject_ID,modality,project,date,xsiType,label'
    experiment_list = intf._get_json(post_uri)
    return experiment_list

def list_scans(intf, projectid, subjectid, experimentid):
    post_uri = '/REST/projects/'+projectid+'/subjects/'+subjectid+'/experiments'
    post_uri += '?columns=ID,URI,label,subject_label,subject_id,project'
    post_uri += ',xnat:mrsessiondata/scans/scan/id'
    post_uri += ',xnat:mrsessiondata/scans/scan/type'
    post_uri += ',xnat:mrsessiondata/scans/scan/quality'
    post_uri += ',xnat:mrsessiondata/scans/scan/note'
    post_uri += ',xnat:mrsessiondata/scans/scan/frames'
    post_uri += ',xnat:mrsessiondata/scans/scan/series_description'
    scan_list = intf._get_json(post_uri)
    new_list = [] 
        
    for s in scan_list:
        if s['ID'] == experimentid:
            snew = {}
            snew['scan_id'] = s['xnat:mrsessiondata/scans/scan/id']
            snew['scan_label'] = s['xnat:mrsessiondata/scans/scan/id']
            snew['scan_quality'] = s['xnat:mrsessiondata/scans/scan/quality']
            snew['scan_note'] = s['xnat:mrsessiondata/scans/scan/note']
            snew['scan_frames'] = s['xnat:mrsessiondata/scans/scan/frames']
            snew['scan_description'] = s['xnat:mrsessiondata/scans/scan/series_description']
            snew['scan_type'] = s['xnat:mrsessiondata/scans/scan/type']
            snew['project_id'] = s['project']
            snew['project_label'] = s['project']
            snew['subject_id'] = s['xnat:mrsessiondata/subject_id']
            snew['subject_label'] = s['subject_label']
            snew['session_id'] = s['ID']
            snew['session_label'] = s['label']
            snew['session_uri'] = s['URI']
            new_list.append(snew)

    return new_list

def list_scan_resources(intf, projectid, subjectid, experimentid, scanid):
    post_uri = '/REST/projects/'+projectid+'/subjects/'+subjectid+'/experiments/'+experimentid+'/scans/'+scanid+'/resources'
    resource_list = intf._get_json(post_uri)
    return resource_list

def list_assessors(intf, projectid, subjectid, experimentid):
    new_list = [] 
    
    # First get FreeSurfer
    post_uri = '/REST/projects/'+projectid+'/subjects/'+subjectid+'/experiments/'+experimentid+'/assessors'
    post_uri += '?columns=ID,label,URI,xsiType,project,xnat:mrsessiondata/subject_id,xnat:mrsessiondata/id,xnat:mrsessiondata/label,URI,fs:fsData/procstatus,fs:fsData/validation/status&xsiType=fs:fsData' 
    assessor_list = intf._get_json(post_uri)
        
    for a in assessor_list:
        anew = {}
        anew['assessor_id'] = a['ID']
        anew['assessor_label'] = a['label']
        anew['assessor_uri'] = a['URI']
        anew['project_id'] = a['project']
        anew['project_label'] = a['project']
        anew['subject_id'] = a['xnat:mrsessiondata/subject_id']
        anew['session_id'] = a['xnat:mrsessiondata/id']
        anew['session_label'] = a['xnat:mrsessiondata/label']
        anew['procstatus'] = a['fs:fsdata/procstatus']
        anew['qcstatus'] = a['fs:fsdata/validation/status']
        anew['proctype'] = 'FreeSurfer'
        anew['xsiType'] = a['xsiType']
        new_list.append(anew)
        
    # Then add genProcData
    post_uri = '/REST/projects/'+projectid+'/subjects/'+subjectid+'/experiments/'+experimentid+'/assessors'
    post_uri += '?columns=ID,label,URI,xsiType,project,xnat:mrsessiondata/subject_id,xnat:mrsessiondata/id,xnat:mrsessiondata/label,proc:genprocdata/procstatus,proc:genprocdata/proctype,proc:genprocdata/validation/status&xsiType=proc:genprocdata' 
    assessor_list = intf._get_json(post_uri)
        
    for a in assessor_list:
        anew = {}
        anew['assessor_id'] = a['ID']
        anew['assessor_label'] = a['label']
        anew['assessor_uri'] = a['URI']
        anew['project_id'] = a['project']
        anew['project_label'] = a['project']
        anew['subject_id'] = a['xnat:mrsessiondata/subject_id']
        anew['session_id'] = a['xnat:mrsessiondata/id']
        anew['session_label'] = a['xnat:mrsessiondata/label']
        anew['procstatus'] = a['proc:genprocdata/procstatus']
        anew['proctype'] = a['proc:genprocdata/proctype']
        anew['qcstatus'] = a['proc:genprocdata/validation/status']
        anew['xsiType'] = a['xsiType']
        new_list.append(anew)

    return new_list

def list_assessor_out_resources(intf, projectid, subjectid, experimentid, assessorid):
    post_uri = '/REST/projects/'+projectid+'/subjects/'+subjectid+'/experiments/'+experimentid+'/assessors/'+assessorid+'/out/resources'
    resource_list = intf._get_json(post_uri)
    return resource_list

def get_full_object(intf,obj_dict):    
    if 'scan_id' in obj_dict:
        proj = obj_dict['project_id']
        subj = obj_dict['subject_id']
        sess = obj_dict['session_id']
        scan = obj_dict['scan_id']
        return intf.select('/project/'+proj+'/subject/'+subj+'/experiment/'+sess+'/scan/'+scan)
    elif 'xsiType' in obj_dict and (obj_dict['xsiType'] == 'fs:fsData' or obj_dict['xsiType'] == 'proc:genProcData'):
        proj = obj_dict['project_id']
        subj = obj_dict['subject_id']
        sess = obj_dict['session_id']
        assr = obj_dict['assessor_id']
        return intf.select('/project/'+proj+'/subject/'+subj+'/experiment/'+sess+'/assessor/'+assr)    
    elif 'experiments' in obj_dict['URI']:
        proj = obj_dict['project']
        subj = obj_dict['subject_ID']
        sess = obj_dict['ID']
        return intf.select('/project/'+proj+'/subject/'+subj+'/experiment/'+sess)
    elif 'subjects' in obj_dict['URI']:
        proj = obj_dict['project']
        subj = obj_dict['ID']
        return intf.select('/project/'+proj+'/subject/'+subj)    
    else:
        return None
 