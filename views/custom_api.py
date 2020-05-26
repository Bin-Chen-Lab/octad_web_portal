import json, subprocess
from os import walk, makedirs, removedirs
import shutil
from os.path import join, splitext, exists, relpath, dirname
import collections
from datetime import datetime
from flask import Blueprint, request, render_template, url_for, g
from app import app
from models.dashboard import get_diseases, Samples, Job, STATUS, get_sites, get_metastatics, get_grades, get_stages, get_tissue_types, get_gender, get_EGFR, get_IDH1, get_IDH2, get_TP53, get_mutation_list, get_gain_list, get_loss_list
from zipfile import ZipFile, ZIP_DEFLATED
from custom_email import send_email
from models.dashboard import FEATURES
from sqlalchemy import not_
from models.base import db
import pandas as pd
import numpy as np
rscript_path = app.config['RSCRIPT_PATH']
rdir_path = app.config['RREPO_PATH']
r_output = join(app.config['RREPO_OUTPUT'], '') # ensures path has a trailing slash
base_url = app.config['BASE_URL']

apiRoute = Blueprint('api', __name__)

@apiRoute.route('/sample/api1', methods=["GET"])
# @csrf.exempt
def sampleApi1():
    """
    json of job information
    :return: json object
    """
    tissue_type = ['adjacent']
    samples = Samples.query.filter(not_(Samples.tissue_type.in_(tissue_type))).all()

    sampleList = []
    for sample in samples:
        d = [sample.id, sample.id, sample.sample_id, sample.tissue_type, sample.age_in_year, sample.site,
             sample.gender, sample.metastatic_site, sample.cancer, sample.EGFR, sample.IDH1, sample.IDH2,
             sample.TP53, sample.tumor_grade, sample.tumor_stage, sample.mutation_list, sample.gain_list, sample.loss_list]
        sampleList.append(d)

    return json.dumps({"data": sampleList})


# @apiRoute.route('/sample/control/api', methods=["POST"])
# # @csrf.exempt
# def controlSampleApi():
# 	"""
# 	json of job information
# 	:return: json object
# 	"""
# 	site = ''
# 	sample_list = []
# 	if request.method == 'POST':
# 		data = request.get_json(force=True)
# 		job_id = data['job_id']
# 		job = Job.query.filter(Job.id == job_id).first()
# 		file_name = data['file_name']
# 		if not file_name:
# 			control_ids = [control for control in job.jobs[0].ctrl_sample_id.split(',') if job and job.jobs[0].ctrl_sample_id]
# 			if not control_ids:
# 				control_path = r_output + job_id + '/control_ids.txt'
# 				with open(control_path, "r") as f:
# 					for control in f.readlines():
# 						control_ids.append(control.replace('\n', ''))
# 				f.close()
# 			samples = Samples.query.filter(Samples.sample_id.in_(control_ids)).all()
# 			site = job.jobs[0].ctrl_site
# 		else:
# 			file_path = join(app.config['RREPO_OUTPUT'], str(job_id), file_name)
# 			f = open(file_path, 'r')
# 			lines = f.readlines()
# 			site = lines[0].replace('\n', '')
# 			control_id = [line.replace('\n', '') for line in lines[1:]]
# 			samples = Samples.query.filter(Samples.sample_id.in_(control_id)).all()
# 			job.jobs[0].update(commit=True, ctrl_site=site)
# 		for sample in samples:
# 			d = collections.OrderedDict()
# 			d['id'] = sample.id
# 			d['sample_id'] = sample.sample_id
# 			d['tissue_type'] = sample.tissue_type
# 			d['age_in_year'] = sample.age_in_year
# 			d['site'] = sample.site
# 			d['gender'] = sample.gender
# 			d['metastatic_site'] = sample.metastatic_site
# 			d['cancer'] = sample.cancer
# 			d['egfr'] = 1 if sample.EGFR else 0
# 			d['idh1'] = 1 if sample.IDH1 else 0
# 			d['idh2'] = 1 if sample.IDH2 else 0
# 			d['tp53'] = 1 if sample.TP53 else 0
# 			d['tumor_grade'] = sample.tumor_grade
# 			d['tumor_stage'] = sample.tumor_stage
# 			sample_list.append(d)
# 	data = {"site": site, "samples": sample_list}
# 	return json.dumps(data)


@apiRoute.route('/sample/control/api1', methods=["POST"])
# @csrf.exempt
def controlSampleApi1():
    """
    json of job information
    :return: json object
    """
    site = ''
    sample_list = []
    if request.method == 'POST':
        data = request.get_json(force=True)
        job_id = data['job_id']
        job = Job.query.filter(Job.id == job_id).first()
        file_name = data['file_name']
        if not file_name:
            control_ids = [control for control in job.jobs[0].ctrl_sample_id.split(',') if job and job.jobs[0].ctrl_sample_id]
            if not control_ids:
                control_path = r_output + job_id + '/control_ids.txt'
                with open(control_path, "r") as f:
                    for control in f.readlines():
                        control_ids.append(control.replace('\n', ''))
                f.close()
            samples = Samples.query.filter(Samples.sample_id.in_(control_ids)).all()
            site = job.jobs[0].ctrl_site
        else:
            file_path = join(app.config['RREPO_OUTPUT'], str(job_id), file_name)
            f = open(file_path, 'r')
            lines = f.readlines()
            site = lines[0].replace('\n', '')
            control_id = [line.replace('\n', '') for line in lines[1:]]

            # tissue_type = ['adjacent']
            # samples = Samples.query.filter(not_(Samples.tissue_type.in_(tissue_type))).all()

            samples = Samples.query.filter(Samples.sample_id.in_(control_id)).all()
            job.jobs[0].update(commit=True, ctrl_site=site)

        for sample in samples:
            d = [sample.id, sample.id, sample.sample_id, sample.tissue_type, sample.age_in_year, sample.site,
                 sample.gender, sample.metastatic_site, sample.cancer, sample.EGFR, sample.IDH1, sample.IDH2,
                 sample.TP53, sample.tumor_grade, sample.tumor_stage]
            sample_list.append(d)
    data = {"site": site, "samples": sample_list}
    return json.dumps(data)

@apiRoute.route('/diseases1', methods=["POST"])
# @csrf.exempt
#Append sample ids against selected disease
def diseases1():
    data = request.get_json(force=True)

    job_id = data['job_id']
    case_id_path = r_output + job_id + '/case_ids.txt'
    control_size = data['control_size']
    control_tissue_type = data['control_tissue_type']

    args = [ str(job_id), str(case_id_path), str(control_size), str(control_tissue_type)]
    cmd = [rscript_path, join(rdir_path,'select_controls.R')]

    print "Inside Disease1 :"
    print cmd
    print args

    site = ''
    sample_list = []

    try:
        x = subprocess.call(cmd+args, universal_newlines=True)

        print cmd

        #job = Job.query.filter(Job.id == job_id).first()
        file_path = join(app.config['RREPO_OUTPUT'], str(job_id), "control_ids.txt")
        f = open(file_path, 'r')
        lines = f.readlines()
        site = lines[0].replace('\n', '')
        control_id = [line.replace('\n', '') for line in lines[1:]]

        correlation_graph_path = '/static/data/' + job_id + '/'

        samples = Samples.query.filter(Samples.sample_id.in_(control_id)).all()
        for sample in samples:
            d = [sample.id, sample.id, sample.sample_id, sample.tissue_type, sample.age_in_year, sample.site,
                 sample.gender, sample.metastatic_site, sample.cancer, sample.EGFR, sample.IDH1, sample.IDH2,
                 sample.TP53, sample.tumor_grade, sample.tumor_stage]
            sample_list.append(d)

            data = { "site": site, "samples": sample_list, 'correlation_graph': correlation_graph_path + 'correlation graph.pdf' }
        return json.dumps(data)

    except Exception as e:
        print e
        return json.loads(False)

#job.update(commit=True, status=2, case_sample_id=case_str)
        #file_name = x.replace('[1] "', '')
        #file_name = file_name.replace('"', '')
        #file_name = file_name.replace('\n', '')






    #except: Exception as e:
    #     print e
    #     return json.dumps(dict(job_id=job_id, file_name="fail"))
    # print 'The maximum of the numbers is:', file_name
    # return json.dumps(dict(job_id=job_id, file_name=file_name))
    # return json.dumps(dict(job_id=job_id))
    # diseases = get_diseases()
    # return json.dumps(diseases)



@apiRoute.route('/diseases', methods=["GET"])
# @csrf.exempt
def diseases():
    diseases = get_diseases()
    return json.dumps(diseases)


@apiRoute.route('/job/api/<user_id>', methods=["GET"])
# @csrf.exempt
def userJobApi(user_id):
    """
    json of job information
    :return: json object
    """
    jobStatus() #check incompleted jobs
        
    jobs = Job.query.filter(Job.user_id == user_id, Job.is_save == True).order_by(Job.creationTime.desc()).all()
    jobs_list = []
    for job in jobs:
        d = [job.id, job.name, job.jobs[0].disease_name, STATUS[job.status], str(job.creationTime)]
        jobs_list.append(d)

    return json.dumps(jobs_list)



@apiRoute.route('/job/status', methods=["GET"])
# @csrf.exempt
def jobStatus():
    """
    json of job information
    :return: json object
    """



    jobs = Job.query.filter(Job.status <= 5).all()
    # jobs = Job.query.filter(Job.status == 6).all()
    for job in jobs:
        job_id = job.id

        if job.status < 5 and (job.is_save != 0):
            # Removed unwanted Jobs and Jobs directory from Database
            created_date = job.creationTime.date()
            current_date = datetime.utcnow().date()
            compareCreatedDate = datetime(created_date.year, created_date.month, created_date.day)
            compareCurrentDate = datetime(current_date.year, current_date.month, current_date.day)
            getFinalDate = compareCurrentDate - compareCreatedDate
            if getFinalDate.days >= 15:
                #delete_JobDirectorydelete_JobDirectory(job_id) #function to delete the Job directory
                if job.jobs: job.jobs[0].delete(commit=True)
                job.delete(commit=True)
#               #replaced by delete job
#		elif job.status <= 5 and (job.is_save == 0 or not job.is_save) and job.creationTime.date() < datetime.utcnow().date():
#			# Removed unwanted Jobs and Jobs from Database
#			#delete_JobDirectory(job_id) #function to delete the Job directory
#			if job.jobs: job.jobs[0].delete(commit=True)
#			job.delete(commit=True)
        elif check_JobComplete(job_id):
            job.update(commit=True, status=6)
            file_folder = join(app.config['RREPO_OUTPUT'], str(job.id))
            file_name = job.name.replace(' ', '_') + '.zip'
            file_path = join(file_folder, file_name)
            if not exists(file_path):
                fantasy_zip = ZipFile(file_path, 'w')
                for folder, subfolders, files in walk(file_folder):
                    for file in files:
                        if file.endswith('.pdf') or file.endswith('.csv') or file.endswith('case_ids.txt') or file.endswith('control_ids.txt'):
                            fantasy_zip.write(join(folder, file),
                                              relpath(join(folder, file), file_folder),
                                              compress_type=ZIP_DEFLATED)
                fantasy_zip.close()
                job_url = base_url + url_for('dashboard.job_output', job_id=job.id)
                subject = "OCTAD: %s Status" % job.name
                text = ""
                html = render_template('emails/job_status.html', job=job, job_url=job_url)
                send_email(job.userDetails.username, subject, text, html)

    return json.dumps("script completed")


def check_pdf(job_id):
    stat_path = app.config['APPLICATION_ROOT'] + '/static/data/' + str(job_id) + '/'
    flag = False
    for root, dirs, files in walk(stat_path):
        for file in files:
            if file.startswith("drug_enriched"):
                flag = True
    return flag

def check_JobComplete(job_id):
    """searches data folders for file with particular name to indicate the R code has completed
    
    parameters, job_id file.   
    modified P Bills, IT Services May 2020 to look only for essential sRGES file instead of 
    other analysis, since the signature-file-only process does not create these.  
    """
    stat_path = app.config['APPLICATION_ROOT'] + '/static/data/' + str(job_id) + '/'
    file_name_to_check = "sRGES.csv" # "drug_sensitivity_insilico_results"
    
    print "checking for {} in {}".format(file_name_to_check, stat_path)
    
    for root, dirs, files in walk(stat_path):
        # for file in files:
        # 	if file.startswith(file_name_to_check):				
        # 		return True
        if file_name_to_check in files:
            "{} file found, job complete".format(file_name_to_check)
            return True
            
    print("job completion file not found {}".format(file_name_to_check))
    return False
    
# need to call for jobs without logged in users id (function above runs for all jobs)
def createJobZip(job):
    """ create zip file for a single job
    Does not check for job completedness and overwrites (recreates ) the zip file
    input: job object
    output : T/F if completed successfully 
    This was created for use with signature-file only upload jobs
    P. Bills MSU IT Services. May 2020
    """
    stat_folder = join(app.config['RREPO_OUTPUT'], str(job.id))

    if not exists(stat_folder):
        print("did not create zip file, folder for job not found".format(stat_folder))
        return(False)

    if not job.name:
        print("job {} does not have a name, can't create zip file".format(job.id))
        return(False)

    file_name = job.name.replace(' ', '_') + '.zip'
    file_path = join(stat_folder, file_name)
    try:
        print "creating zip file {} ...".format(file_path)
        fantasy_zip = ZipFile(file_path, mode='w')
        for folder, subfolders, files in walk(stat_folder):
            for file in files:
                if file.endswith('.pdf') or file.endswith('.csv') or file.endswith('case_ids.txt') or file.endswith('control_ids.txt'):
                    fantasy_zip.write(join(folder, file),relpath(join(folder, file), stat_folder))
                        # compress_type=ZIP_DEFLATED)
    except Exception as e:
        print('error when making zip file {}'.format(e))
        return(False)

    finally:
        fantasy_zip.close()
    
    return True



# START : Function to delete the Job from the Respective folder
def delete_JobDirectory(job_id):
    stat_path = app.config['APPLICATION_ROOT'] + '/static/data/' + str(job_id) + '/'
    flag = False
    if exists(stat_path):
        shutil.rmtree(stat_path)
        flag = True
    return flag
# END : Function to delete the Job from the Respective folder

@apiRoute.route('/job/del/<user_id>/<job_id>', methods=["GET"])
# @csrf.exempt
def delete_job(user_id, job_id):
    print job_id
    #return job_id
    job = Job.query.filter(Job.id == job_id, Job.user_id == user_id).first()
    flag = False
    #print type(job)
    if job != None:
        # if job.jobs != None: job.jobs[0].delete(commit=True)
        # job.delete(commit=True)
        print 1
        # delete_JobDirectory(job_id)
        flag = True
    return render_template('dashboard/job.html', user = user_id)


@apiRoute.route('/job/rerun', methods=["GET"])
# @csrf.exempt
def jobRerun():
    """
    json of job information
    :return: json object
    """

    jobs = Job.query.filter(Job.status == 5).all()
    for job in jobs:
        cmd = [rscript_path, join(rdir_path,'drug_predict.R'), str(job.id), 'T', str(50), str(1), 'F', 'T']
        x = subprocess.Popen(cmd)


@apiRoute.route('/job/signature', methods=['POST'])
# @csrf.exempt
def signatureData():
    """
    On the basis of job_id signature related files given in list
    :param job_id:
    :return: list of file names
    """
    outdata = {}
    data = request.get_json(force=True)
    job_id = data.get('job_id', None)
    job = Job.query.filter(Job.id == job_id).first() if job_id else None
    if job:
        file_path = '/static/data/' + job_id + '/'
        pdf_path = app.config['APPLICATION_ROOT'] + file_path
        pdfs = []
        for dirPath, dirNames, fileNames in walk(pdf_path):
            pdfs.extend([join(file_path, fileName) for fileName in fileNames if fileName.startswith('dz_enriched_')
                         and splitext(fileName)[1].lower() in ['.pdf']])
        outdata = {'signature': file_path + 'signature.pdf',
                'enricher': pdfs}
    return json.dumps(outdata)


@apiRoute.route('/get_casefeature_by_disease', methods=["POST"])
# @csrf.exempt
def get_casefeature_by_disease():
    data = request.get_json(force=True)

    disease = data.get('disease', None)

    tissue_type = data.get('tissue_type', None)
    site = data.get('site', None)
    gender = data.get('gender', None)
    metastatic = data.get('metastatic', None)
    egfr = data.get('egfr', None)
    idh1 = data.get('idh1', None)
    idh2 = data.get('idh2', None)
    tp53 = data.get('tp53', None)
    age = data.get('tp53', None)
    tumor_grade = data.get('tumor_grade', None)
    tumor_stage = data.get('tumor_stage', None)
    empMutation  = "";
    empGain  = "";
    empLoss  = "";
    mutation_list = data.get('mutation_list', empMutation)
    gain_list = data.get('gain_list', empGain)
    loss_list = data.get('loss_list', empLoss)
    sites_list = get_sites(disease, tissue_type, gender, metastatic, egfr, idh1, idh2, tp53, age, tumor_grade, tumor_stage)
    metastatics_list = get_metastatics(disease, tissue_type, site, gender, egfr, idh1, idh2, tp53, age, tumor_grade, tumor_stage)
    grades_list = get_grades(disease, tissue_type, site, gender, metastatic, egfr, idh1, idh2, tp53, age, tumor_stage)
    stages_list = get_stages(disease, tissue_type, site, gender, metastatic, egfr, idh1, idh2, tp53, age, tumor_grade)
    tissue_types_list = get_tissue_types(disease, site, gender, metastatic, egfr, idh1, idh2, tp53, age, tumor_grade, tumor_stage)
    gender_list = get_gender(disease, tissue_type, site, metastatic, egfr, idh1, idh2, tp53, age, tumor_grade, tumor_stage)
    egfr_list = get_EGFR(disease, tissue_type, site, gender, metastatic, idh1, idh2, tp53, age, tumor_grade, tumor_stage)
    idh1_list = get_IDH1(disease, tissue_type, site, gender, metastatic, egfr, idh2, tp53, age, tumor_grade, tumor_stage)
    idh2_list = get_IDH2(disease, tissue_type, site, gender, metastatic, egfr, idh1, tp53, age, tumor_grade, tumor_stage)
    tp53_list = get_TP53(disease, tissue_type, site, gender, metastatic, egfr, idh1, idh2, age, tumor_grade, tumor_stage)
    mutation_list_data = get_mutation_list(disease, tissue_type, site, gender, metastatic, egfr, idh1, idh2, age, tumor_grade,tumor_stage,mutation_list)
    gain_list_data = get_gain_list(disease, tissue_type, site, gender, metastatic, egfr, idh1, idh2, age, tumor_grade,tumor_stage,gain_list)
    loss_list_data = get_loss_list(disease, tissue_type, site, gender, metastatic, egfr, idh1, idh2, age, tumor_grade,tumor_stage,loss_list)
    outdata = dict(sites=sites_list, metastatics=metastatics_list, grades=grades_list, stages=stages_list, tissue_types=tissue_types_list, gender=gender_list,
        egfr=egfr_list, idh1=idh1_list, idh2=idh2_list, tp53=tp53_list, mutation_list=mutation_list_data, gain_list=gain_list_data, loss_list=loss_list_data)

    return json.dumps(outdata)


@apiRoute.route('/case_plot', methods=["POST"])
# @csrf.exempt
def case_plot():
    data = request.get_json(force=True)
    case_str = data.get('cases', None)
    if case_str:
        case_ids = [i for i in case_str.split(',')]
    else:
        case_ids = []

    csv_file = app.config['APPLICATION_ROOT'] + '/static/data_files/tsne_3d.csv'

    df = pd.read_csv(csv_file)
    others = {
        "x": list(df.X.values),
        "y": list(df.Y.values),
        "mode": 'markers',
        "type": 'scatter',
        "name": 'Other',
        "text": list(df.name.values)
    }
    if case_ids:
        odf = df.loc[df['Unnamed: 0'].isin(case_ids)]
        x = list(odf.X.values)
        y = list(odf.Y.values)
        texts = list(odf.name.values)
    else:
        x = []
        y = []
        texts = []
    cases = {
        "x": x,
        "y": y,
        "mode": 'markers',
        "type": 'scatter',
        "name": 'Case',
        "text": texts
    }
    layout = {"title": 'Case Visualization', "showlegend": True}
    graph_data = [others, cases]
    return json.dumps(dict(graph_data=graph_data, layout=layout))


@apiRoute.route('/control_plot', methods=["POST"])
# @csrf.exempt
def control_plot():
    data = request.get_json(force=True)
    case_str = data.get('cases', None)
    control_str = data.get('controls', None)
    if case_str:
        case_ids = [i for i in case_str.split(',')]
    else:
        case_ids = []
    if control_str:
        control_ids = [j for j in control_str.split(',')]
    else:
        control_ids = []
    csv_file = app.config['APPLICATION_ROOT'] + '/static/data_files/tsne_3d.csv'
    df = pd.read_csv(csv_file)
    others = {
        "x": list(df.X.values),
        "y": list(df.Y.values),
        "mode": 'markers',
        "type": 'scatter',
        "name": 'Other',
        "text": list(df.name.values)
    }
    if case_ids:
        odf = df.loc[df['Unnamed: 0'].isin(case_ids)]
        cx = list(odf.X.values)
        cy = list(odf.Y.values)
        ctexts = list(odf.name.values)
    else:
        cx = []
        cy = []
        ctexts = []
    if control_ids:
        odf = df.loc[df['Unnamed: 0'].isin(control_ids)]
        ctx = list(odf.X.values)
        cty = list(odf.Y.values)
        cttexts = list(odf.name.values)
    else:
        ctx = []
        cty = []
        cttexts = []
    cases = {
        "x": cx,
        "y": cy,
        "mode": 'markers',
        "type": 'scatter',
        "name": 'Case',
        "text": ctexts
    }
    controls = {
        "x": ctx,
        "y": cty,
        "mode": 'markers',
        "type": 'scatter',
        "name": 'Control',
        "text": cttexts
    }
    layout = {"title": 'Case Control Visualization', "showlegend": True}
    graph_data = [others, cases, controls]
    return json.dumps(dict(graph_data=graph_data, layout=layout))


@apiRoute.route('/output/drug_hit/<job_id>', methods=['GET'])
# @csrf.exempt
def drug_hit(job_id):
    """
    On the basis of job_id drug_hits data in json format
    :param job_id:
    :return: list of csv data
    """
    job = Job.query.filter(Job.id == job_id).first() if job_id else None
    drug_hits_csv_data = []
    if job:
        file_path = '/static/data/' + job_id + '/'
        pdf_path = app.config['APPLICATION_ROOT'] + file_path
        drug_hits_csv_file = "".join([pdf_path, 'sRGES_drug.csv'])
        if exists(drug_hits_csv_file):
            df = pd.read_csv(drug_hits_csv_file, index_col=False, dtype={"sRGES": str})
            csv_df = df[["pert_iname", "clinical_phase", "moa", "target", "sRGES"]]
            csv_df1 = csv_df.replace(np.nan, '', regex=True)
            drug_hits_csv_data = csv_df1.values.tolist()
    return json.dumps({"data": drug_hits_csv_data})


@apiRoute.route('/output/dz_predict/<job_id>', methods=['GET'])
# @csrf.exempt
def disease_predict(job_id):
    """
    On the basis of job_id drug_hits data in json format
    :param job_id:
    :return: list of csv data
    """
    job = Job.query.filter(Job.id == job_id).first() if job_id else None
    disease_predict_csv_data = []
    if job:
        file_path = '/static/data/' + job_id + '/'
        pdf_path = app.config['APPLICATION_ROOT'] + file_path
        disease_predict_csv_file = "".join([pdf_path, 'dz_signature.csv'])
        if exists(disease_predict_csv_file):
            df = pd.read_csv(disease_predict_csv_file, index_col=False)
            csv_df = df[["identifier", "gene", "log2FoldChange", "padj"]]
            csv_df1 = csv_df.replace(np.nan, '', regex=True)
            disease_predict_csv_data = csv_df1.values.tolist()

    return json.dumps({"data": disease_predict_csv_data})

# START : Displaying the Singature, Up and Down Singature Genes CSV on Signature Page

@apiRoute.route('/sample/csv_api/<job_id>/<name>', methods=["GET"])
# @csrf.exempt
def sampleCsvApi(job_id,name):
    """
    On the basis of job_id drug_hits data in json format
    :param job_id:
    :return: list of csv data
    """
    print name

    job = Job.query.filter(Job.id == job_id).first() if job_id else None
    disease_predict_csv_data = []


    if name == 'dz_sign':
        if job:
            file_path = '/static/data/' + job_id + '/'
            pdf_path = app.config['APPLICATION_ROOT'] + file_path
            disease_predict_csv_file = "".join([pdf_path, 'dz_signature.csv'])
            if exists(disease_predict_csv_file):
                df = pd.read_csv(disease_predict_csv_file, index_col=False)
                csv_df = df[["identifier", "gene", "log2FoldChange", "padj"]]
                csv_df1 = csv_df.replace(np.nan, '', regex=True)
                disease_predict_csv_data = csv_df1.values.tolist()

            return json.dumps({"data": disease_predict_csv_data})

    if name == 'dz_up':
        if job:
            file_path = '/static/data/' + job_id + '/enrichment_analysis/GeneEnrichment/'
            pdf_path = app.config['APPLICATION_ROOT'] + file_path
            disease_predict_csv_file = "".join([pdf_path, 'dz_up_sig_genes_enriched.csv'])
            if exists(disease_predict_csv_file):
                df = pd.read_csv(disease_predict_csv_file, index_col=False)
                csv_df = df[["database", "category", "Odds_Ratio", "qval", "Combined Score", "genes"]]
                smallest_value = csv_df.nsmallest(10, ['qval'])
                csv_df1 = smallest_value.replace(np.nan, '', regex=True)
                disease_predict_csv_data = csv_df1.values.tolist()

            return json.dumps({"data": disease_predict_csv_data})


    if name == 'dz_down':
        if job:
            file_path = '/static/data/' + job_id + '/enrichment_analysis/GeneEnrichment/'
            pdf_path = app.config['APPLICATION_ROOT'] + file_path
            disease_predict_csv_file = "".join([pdf_path, 'dz_down_sig_genes_enriched.csv'])
            if exists(disease_predict_csv_file):
                df = pd.read_csv(disease_predict_csv_file, index_col=False)
                csv_df = df[["database", "category", "Odds_Ratio", "qval", "Combined Score", "genes"]]
                smallest_value = csv_df.nsmallest(10, ['qval'])
                csv_df1 = smallest_value.replace(np.nan, '', regex=True)
                disease_predict_csv_data = csv_df1.values.tolist()

            return json.dumps({"data": disease_predict_csv_data})

    if name == 'approved_drugs':
        if job:
            file_path = '/static/data/' + job_id + '/'
            pdf_path = app.config['APPLICATION_ROOT'] + file_path
            disease_predict_csv_file = "".join([pdf_path, 'sRGES_FDAapproveddrugs.csv'])
            if exists(disease_predict_csv_file):
                df = pd.read_csv(disease_predict_csv_file, index_col=False)
                csv_df = df[["pert_iname", "clinical_phase", "moa", "target", "sRGES"]]
                csv_df1 = csv_df.replace(np.nan, '', regex=True)
                disease_predict_csv_data = csv_df1.values.tolist()

#			print disease_predict_csv_data

            return json.dumps({"data": disease_predict_csv_data})


    if name == 'mutation':
        if job:
            file_path = app.config['APPLICATION_ROOT'] + '/static/'

            mutation_csv_file = "".join([file_path, 'mutation.csv'])
            if exists(mutation_csv_file):
                df = pd.read_csv(mutation_csv_file, index_col=False)
                csv_df = df[["Mutation"]]
                csv_df1 = csv_df.replace(np.nan, '', regex=True)
                mutation_csv_data = csv_df1.values.tolist()

            return json.dumps({"data": mutation_csv_data})

    if name == 'loss':
        if job:
            file_path = app.config['APPLICATION_ROOT'] + '/static/'

            loss_csv_file = "".join([file_path, 'mutation.csv'])
            if exists(loss_csv_file):
                df = pd.read_csv(loss_csv_file, index_col=False)
                csv_df = df[["Mutation"]]
                csv_df1 = csv_df.replace(np.nan, '', regex=True)
                loss_csv_data = csv_df1.values.tolist()

            return json.dumps({"data": loss_csv_data})

    if name == 'gain':
        if job:
            file_path = app.config['APPLICATION_ROOT'] + '/static/'

            gain_csv_file = "".join([file_path, 'mutation.csv'])
            if exists(gain_csv_file):
                df = pd.read_csv(gain_csv_file, index_col=False)
                csv_df = df[["Mutation"]]
                csv_df1 = csv_df.replace(np.nan, '', regex=True)
                gain_csv_data = csv_df1.values.tolist()

            return json.dumps({"data": gain_csv_data})


# END : Displaying the Singature, Up and Down Singature Genes CSV on Signature Page

@apiRoute.route('/sample/mutation_api/', methods=["POST"])
# @csrf.exempt
def sampleMutationApi():

    data = request.get_json(force=True)

    name = data['name']

    if name == 'mutation':

        mutation_csv_data = "Sucess";

        return json.dumps({"mutation": mutation_csv_data})

@apiRoute.route('/sample/gain_api/', methods=["POST"])
# @csrf.exempt
def sampleGainApi():

    data = request.get_json(force=True)

    name = data['name']

    if name == 'gain':

        gain_csv_data = "Sucess";

        return json.dumps({"gain": gain_csv_data})

@apiRoute.route('/sample/loss_api/', methods=["POST"])
# @csrf.exempt
def sampleLossApi():

    data = request.get_json(force=True)

    name = data['name']

    if name == 'loss':

        loss_csv_data = "Sucess";

        return json.dumps({"mutation": loss_csv_data})