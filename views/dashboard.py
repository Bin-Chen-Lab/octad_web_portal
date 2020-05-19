import subprocess, requests
import shutil
from datetime import datetime
from os import walk, makedirs, chmod
from os.path import join, splitext, exists, dirname
from app import app, before_request, db
from flask import Blueprint, render_template, request, g, flash, session, url_for, redirect, make_response
from flask_login import login_user
from models.dashboard import FEATURES, get_sites, get_metastatics, get_grades, get_stages, Job, JobDetails, STATUS
from models.profile import User, generate_password, check_password
import json, re
from flask_login import login_required
rscript_path = app.config['RSCRIPT_PATH']
rdir_path = app.config['RREPO_PATH']
# modified P Bills, MSU IT Services, May 2020. 
r_output = join(app.config['RREPO_OUTPUT'],'')  # ensures there is a trailing slash

dashboardRoute = Blueprint('dashboard', __name__)
dashboardRoute.before_request(before_request)

@dashboardRoute.route('/dataset', methods=["GET"])
# @login_required
def dataset():
    """
    Static page displayed
    """
    return render_template('dashboard/dataset.html')


@dashboardRoute.route('/code', methods=["GET"])
# @login_required
def code():
    """
    Static page displayed
    """
    return render_template('dashboard/code.html')


@dashboardRoute.route('/tutorials', methods=["GET"])
# @login_required
def tutorials():
    """
    Static page displayed
    """
    return render_template('dashboard/tutorials.html')


@dashboardRoute.route('/faq', methods=["GET"])
# @login_required
def faq():
    """
    Static page displayed
    """
    return render_template('dashboard/faq.html')


@dashboardRoute.route('/news', methods=["GET"])
# @login_required
def news():
    """
    Static page displayed
    """
    return render_template('dashboard/news.html')

@dashboardRoute.route('/about', methods=["get"])
# @login_required
def about():
    """
    Static page displayed
    """
    return render_template('dashboard/about.html')

@dashboardRoute.route('/', methods=["GET"])
# @login_required
def dashboard():
    job_type = request.args.get('rerun', False)
    job_id = request.args.get('job_id', '')
    if job_id and job_type == 'true':
        job = Job.query.filter(Job.id == job_id).first()
    else:
        job = None
    sites = get_sites()
    print "tedstt"
    metastatics = get_metastatics()
    grades = get_grades()
    stages = get_stages()
    print stages
    print "end"
    return render_template('dashboard/dashboard.html', features=FEATURES, sites=sites,
                           metastatics=metastatics, grades=grades, stages=stages, job=job)

@dashboardRoute.route('/job/del1/<user_id>/<job_id>', methods=["GET"])
# @csrf.exempt
def delete_job(user_id, job_id):
        print job_id
        #return job_id
        job = Job.query.filter(Job.id == job_id, Job.user_id == user_id).first()
        flag = False
        #print type(job)
        if job != None:
            if job.jobs != None: job.jobs[0].delete(commit=True)
            job.delete(commit=True)
            delete_JobDirectory(job_id)

        flag = True
        return render_template('dashboard/job.html')

# START : Function to delete the Job from the Respective folder
def delete_JobDirectory(job_id):
        stat_path = app.config['APPLICATION_ROOT'] + '/static/data/' + str(job_id) + '/'
        flag = False
        if exists(stat_path):
                shutil.rmtree(stat_path)
                flag = True
        return flag
# END : Function to delete the Job from the Respective folder

@dashboardRoute.route('/dashboard1', methods=["GET"])
# @login_required
def dashboard1():
    """
    Extra function which displays dashboard without plotly

    :return:
    """
    job_type = request.args.get('rerun', False)
    job_id = request.args.get('job_id', '')
    if job_id and job_type == 'true':
        job = Job.query.filter(Job.id == job_id).first()
    else:
        job = None
    sites = get_sites()
    metastatics = get_metastatics()
    grades = get_grades()
    stages = get_stages()
    return render_template('dashboard/dashboard1.html', features=FEATURES, sites=sites, metastatics=metastatics,
                           grades=grades, stages=stages, job=job)


@dashboardRoute.route('/output/<job_id>', methods=["GET"])
# @login_required
def job_output(job_id):
    """
    IF job status is complete then only job is displayed else page is not accessible
    :param job_id:
    :return:
    """
    job = Job.query.get(job_id)

    # added P Bills 5/2020
    # to allow for login-less job retrieval, allow retrieval by key parameter (output/1040?key=abcdefg ) 
    # job can be views on two conditions : 
    #   a job key was sent and it's correct   OR 
    #   user is logged in and owns the job (regardless of key that's sent)
    # get job key parameter (if set, or empty string)
    
    job_key = request.args.get('key', default = '', type = str)

    if job:        
        if not ( job_key and job.check_key(job_key) or (g.user and job.user_id == g.user.id)):
            # got here if it's the wrong key  and/or wrong user
            print "not authorized for job {}".format(job_id)
            return redirect(url_for('dashboard.dashboard'))
    else:
        print "Job with id {} not found".format(job_id)
        return redirect(url_for('dashboard.job_history'))

    # job = Job.query.filter(Job.id == job_id, Job.user_id == g.user.id).first()
    if not job or job.status < 5: # 6
        return redirect(url_for('dashboard.job_history'))
    file_name = job.name.replace(' ', '_') + '.zip'
    file_path = '/static/data/' + job_id + '/'
    signature_file = ''
    dz_enricher = []
    drug_file = ''
    drug_enricher = {}
    pdf_path = app.config['APPLICATION_ROOT'] + file_path
    for dirPath, dirNames, fileNames in walk(pdf_path):
        for fileName in fileNames:
            if fileName.lower().startswith('signature'):
                signature_file = join(file_path, fileName)
            elif fileName.lower().startswith('lincs_') or fileName.lower().startswith('cmap_'):
                drug_file = join(file_path, fileName)
            elif fileName.lower().startswith('dz_enriched_') and splitext(fileName)[1].lower() in ['.pdf']:
                dz_enricher.append(join(file_path, fileName))
            elif fileName.lower().startswith('drug_enriched') and splitext(fileName)[1].lower() in ['.pdf']:
                if 'sea_targets' in fileName:
                    drug_enricher.update(Targets=join(file_path, fileName))
                elif 'chembl_targets' in fileName:
                    drug_enricher.update(Pathway=join(file_path, fileName))
                elif 'meshes' in fileName:
                    drug_enricher.update({'Mesh Term': join(file_path, fileName)})
    # if job.status < 6:
    #     return redirect(url_for('dashboard.job_history'))
    job_url = url_for_job_output(job)
    return render_template('dashboard/output.html', job=job, file_name=file_name,
                           signature_file=signature_file, dz_enricher=dz_enricher,
                           drug_file=drug_file, drug_enricher=drug_enricher, job_url = job_url)

def compute_control_samples():
    print "Here is the Control"

@dashboardRoute.route('/job/save', methods=["POST"])
# @login_required
def save_job():
    job_id = request.form.get('job_id', None)
    if job_id < 0 or job_id == '':
        job_id = Job.get_new_id()
    job = Job.query.filter(Job.id == job_id).first()
    if job:
        job_name = request.form.get('jobName', None)
        description = request.form.get('description', None)
        #disease_name = request.form.get('case_disease_name', None)
        disease_name = request.form.get('our_disease_list', None)
        case_sample_id = request.form.get('case_samples', None)
        case_tissue_type = request.form.getlist('case_type', None)
        case_tissue_type = ','.join(case_tissue_type) if case_tissue_type else ''
        case_site = request.form.get('case_site', None)
        case_gender = request.form.get('case_gender', None)
        case_metastatic_site = request.form.get('case_metastatic', None)
        case_EGFR = request.form.get('case_EGFR', None)
        case_IDH1 = request.form.get('case_IDH1', None)
        case_IDH2 = request.form.get('case_IDH2', None)
        case_TP53 = request.form.get('case_TP53', None)
        ctrl_sample_id = request.form.get('control_samples', None)
        case_age_in_year = request.form.get('case_age', None)
        case_tumor_grade = request.form.get('case_tumor_grade', None)
        case_tumor_stage = request.form.getlist('case_tumor_stage', None)
        case_tumor_stage = ','.join(case_tumor_stage) if case_tumor_stage else ''
        ctrl_tissue_type = request.form.getlist('control_type', None)
        ctrl_tissue_type = ','.join(ctrl_tissue_type) if ctrl_tissue_type else ''
        ctrl_site = request.form.get('control_site', None)
        ctrl_gender = request.form.get('control_gender', None)
        ctrl_metastatic_site = request.form.get('control_metastatic', None)
        ctrl_EGFR = request.form.get('control_EGFR', None)
        ctrl_IDH1 = request.form.get('control_IDH1', None)
        ctrl_IDH2 = request.form.get('control_IDH2', None)
        ctrl_TP53 = request.form.get('control_TP53', None)
        ctrl_age_in_year = request.form.get('control_age', None)
        ctrl_tumor_grade = request.form.get('control_tumor_grade', None)
        ctrl_tumor_stage = request.form.getlist('control_tumor_stage', None)
        ctrl_tumor_stage = ','.join(ctrl_tumor_stage) if ctrl_tumor_stage else ''
        de_method = request.form.get('de_method', None)
        dz_fc_threshold = request.form.get('dz_fc_threshold', None)
        dz_p_threshold = request.form.get('dz_p_threshold', None)
        database = request.form.get('database', None)
        choose_fda_drugs = request.form.get('choose_fda_drugs', 'T')
        if database == 'lincs_db':
            max_gene_size = request.form.get('lincs_max_genes', 50)
        else:
            max_gene_size = request.form.get('cmap_max_genes', 150)
        landmark = request.form.get('landmark', 1)
        weight_cell_line = request.form.get('weight_cell_line', 'F')
        debug = request.form.get('debug', 'T')
        finishInfo = request.form.get('finishInfo', None)
        next_url = request.form.get('next_url', None)
        jobDetails = job.jobs[0]
        if job.status < 3 and case_sample_id and ctrl_sample_id:
            status = 3
        elif job.status < 1 and case_sample_id and not ctrl_sample_id:
            status = 1
        else:
            status = job.status
        if not g.user:
            username = request.form['email']
            password = request.form['password']
            registered_user = User.query.filter_by(username=username).first()
            if registered_user is None:
                hashedPasswd = generate_password(password)
                registered_user = User(username, hashedPasswd, 0, True)
                registered_user.save()
            elif not check_password(registered_user.password, password):
                result = {"message": "Invalid credentials", "category": "error"}
                return json.dumps(result)
            if login_user(registered_user, remember=True):
                session['user_id'] = registered_user.id
                registered_user.update(commit=False, loginTime=datetime.utcnow())
                g.user = registered_user
                job.update(commit=False, user_id=registered_user.id, name=job_name, description=description, status=status, is_save=True)
                db.session.commit()
            else:
                result = {"message": "User is unable to logged in so can't create job", "category": "error"}
                return json.dumps(result)
        else:
            job.update(commit=False, name=job_name, description=description, status=status, is_save=True)
            db.session.commit()
        result = {"message": "Job saved successfully", "category": "success", "finishInfo": finishInfo}
        # Storing Job details
        jobDetails.update(commit=True, disease_name=disease_name, case_tissue_type=case_tissue_type,
                          case_site=case_site, case_gender=case_gender, case_metastatic_site=case_metastatic_site,
                          case_EGFR=case_EGFR if case_EGFR else None, case_IDH1=case_IDH1 if case_IDH1 else None,
                          case_IDH2=case_IDH2 if case_IDH2 else None, case_TP53=case_TP53 if case_TP53 else None,
                          case_age_in_year=case_age_in_year, case_tumor_grade=case_tumor_grade,
                          case_tumor_stage=case_tumor_stage, ctrl_tissue_type=ctrl_tissue_type,
                          ctrl_site=ctrl_site, ctrl_gender=ctrl_gender, ctrl_metastatic_site=ctrl_metastatic_site,
                          ctrl_EGFR=ctrl_EGFR if ctrl_EGFR else None, ctrl_IDH1=ctrl_IDH1 if ctrl_IDH1 else None,
                          ctrl_IDH2=ctrl_IDH2 if ctrl_IDH2 else None, ctrl_TP53=ctrl_TP53 if ctrl_TP53 else None,
                          ctrl_age_in_year=ctrl_age_in_year, ctrl_tumor_grade=ctrl_tumor_grade,
                          ctrl_tumor_stage=ctrl_tumor_stage, de_method=de_method, dz_fc_threshold=dz_fc_threshold,
                          dz_p_threshold=dz_p_threshold, database=database, choose_fda_drugs=choose_fda_drugs,
                          max_gene_size=max_gene_size, landmark=landmark, weight_cell_line=weight_cell_line,
                          debug=debug, case_sample_id=case_sample_id, ctrl_sample_id=ctrl_sample_id)
        if finishInfo == 'true':
            # Added following because it is not working fine with ui field
            choose_fda_drugs = 'T'
            max_gene_size = 50
            landmark = 1
            weight_cell_line = 'F'
            debug = 'T'
            case_path = join(r_output, str(job_id), 'case_ids.txt')
            control_path = join(r_output, str(job_id), 'control_ids.txt')

            if job.status < 4 and not de_method:
                result = {"message": "Invalid DE method. Please select on signature page", "category": "error"}
                return json.dumps(result)
            elif job.status == 4:
                print "ELSE : Status 4"
                cmd = [rscript_path, join(rdir_path,'compute_sRGES_enrichment_rankLines.R'), str(job_id), case_path, control_path, de_method,
                       dz_fc_threshold, dz_p_threshold, debug, choose_fda_drugs, str(max_gene_size), str(landmark),
                       weight_cell_line]
            elif job.status == 3:
                print "ELSE : Status 3"
                cmd = [rscript_path, join(rdir_path + 'compute_sRGES_enrichment_rankLines.R'), str(job_id), case_path, control_path, de_method,
                       dz_fc_threshold, dz_p_threshold, debug, choose_fda_drugs, str(max_gene_size), str(landmark), weight_cell_line]

            else:
                result = {"message": "Please try again. Unable to create job", "category": "error"}
                return json.dumps(result)
            print cmd
            try:
                x = subprocess.Popen(cmd)
                job.update(commit=False, status=5)
                db.session.commit()
            except Exception as e:
                pass
        result.update(next_url=next_url, job_id=job_id)
        return json.dumps(result)
    else:
        result = {"message": "Invalid data please generate job again", "category": "error"}
        return json.dumps(result)


@dashboardRoute.route('/job_history', methods=["GET"])
@login_required
def job_history():
    # Do some stuff
    return render_template('dashboard/job.html')


@dashboardRoute.route('/job/case/<disease>', methods=["POST"])
# @login_required
def job_case(disease):
    """
    Running R script for job
    :return: json object
    """
    data = request.get_json(force=True)
    print data
    job_id = data.get('job_id', None)
    if not job_id:
        job_id = str(Job.get_new_id())
    case_str = data.get('case_samples', None)
    if case_str:
        case_path = join(r_output, str(job_id), 'case_ids.txt')
        case_ids = case_str.split(',')
        if not exists(dirname(case_path)):
            try:
                makedirs(dirname(case_path))
            except OSError as exc:  # Guard against race condition
                print str(exc)
                print "file not generated for case_ids"
        with open(case_path, "w") as f:
            for case in case_ids:
                f.write(case + '\n')
            f.close()
    diseaselist = disease.split("|")
    d_list = [d for d in diseaselist]
    # print "Heeeeee"
    # cmd = [rscript_path, rdir_path + 'select_cases.R', job_id]
    # #cmd = [rscript_path, rdir_path + 'case.R', job_id]
    # print cmd
    # cmd.extend(d_list)
    # print cmd
    # # check_output will run the command and store to result
    # try:
    #     x = subprocess.check_output(cmd, universal_newlines=True)
    #     job = Job.query.filter(Job.id == job_id).first()
    #     job.update(commit=True, status=2, case_sample_id=case_str)
    #     file_name = x.replace('[1] "', '')
    #     file_name = file_name.replace('"', '')
    #     file_name = file_name.replace('\n', '')
    # except Exception as e:
    #     print e
    #     return json.dumps(dict(job_id=job_id, file_name="fail"))
    # print 'The maximum of the numbers is:', file_name
    # return json.dumps(dict(job_id=job_id, file_name=file_name))
    return json.dumps(dict(job_id=job_id))


@dashboardRoute.route('/job/control', methods=["POST"])
# @login_required
def job_control():
    """
    creating jobs control data on next button click
    :return: json object
    """
    data = request.get_json(force=True)
    print data
    job_id = data.get('job_id', None)
    control_str = data.get('control_samples', None)
    if control_str:
        control_path = join(r_output, str(job_id), 'control_ids.txt')
        control_ids = control_str.split(',')
        if not exists(dirname(control_path)):
            try:
                makedirs(dirname(control_path))
            except OSError as exc:  # Guard against race condition
                print str(exc)
                print "file not generated for control_ids"
        with open(control_path, "w") as f:
            for control in control_ids:
                f.write(control + '\n')
            f.close()
    try:
        job = Job.query.filter(Job.id == job_id).first()
        job.update(commit=True, status=3, ctrl_sample_id=control_str)
        return json.dumps(True)
    except Exception as e:
        return json.loads(False)


@dashboardRoute.route('/job/compute', methods=["POST"])
# @login_required
def job_compute():
    """
    Running R script for job control visualization
    :return: json object
    """
    if request.method == 'POST':
        data = request.get_json(force=True)
        try:
            job_id = data.get('job_id')
            de_method = data.get('de_method')
            dz_p_threshold = data.get('dz_p_threshold', 0.001)
            dz_fc_threshold = data.get('dz_fc_threshold', 2)
            case_str = data.get('case_str', '')
            control_str = data.get('control_str', '')
            job = Job.query.filter(Job.id == job_id).first()
            job.jobs[0].update(commit=True, de_method=de_method, dz_fc_threshold=dz_fc_threshold,
                               dz_p_threshold=dz_p_threshold, case_sample_id=case_str, ctrl_sample_id=control_str)
        except Exception as e:
            print e
            return json.dumps("fail")
        case_path = join(r_output, str(job_id), 'case_ids.txt')
        control_path = join(r_output, str(job_id), 'control_ids.txt')
        case_ids = case_str.split(',')
        control_ids = control_str.split(',')
        debug = 'T'
        print len(case_ids)
        if not exists(dirname(case_path)):
            try:
                makedirs(dirname(case_path))
            except OSError as exc:  # Guard against race condition
                print str(exc)
                return "fail"
        with open(case_path, "w") as f:
            for case in case_ids:
                f.write(case + '\n')
            f.close()
        with open(control_path, "w") as f:
            for control in control_ids:
                f.write(control + '\n')
            f.close()
        cmd = [rscript_path, join(rdir_path,'DE_analysis.R'), job_id, case_path, control_path, de_method, dz_fc_threshold,
               dz_p_threshold, debug]
        print "Inside DE_analysis.R"
        print cmd
        # check_output will run the command and store to result
        try:
            x = subprocess.check_output(cmd, universal_newlines=True)
            file_path = '/static/data/' + job_id + '/enrichment_analysis/GeneEnrichment/'
            pdf_path = app.config['APPLICATION_ROOT'] + file_path
            pdfs = []
            for dirPath, dirNames, fileNames in walk(pdf_path):
                pdfs.extend([join(file_path, fileName) for fileName in fileNames if fileName.startswith('dz_enriched_')
                             and splitext(fileName)[1].lower() in ['.pdf']])
            job.update(commit=True, status=4)
            data = {'signature': file_path + 'signature.pdf',
                    'enricher': pdfs}
        except Exception as e:
            print e
            return json.dumps("fail")
        return json.dumps(data)


@dashboardRoute.route('/job/manual_check', methods=["POST"])
# @login_required
def manual_check():
    """
    Running R script for job control visualization
    :return: json object
    """
    if request.method == 'POST':
        data = request.get_json(force=True)
        try:
            job_id = data.get('job_id')
        except Exception as e:
            print e
            return json.dumps("fail")
        case_path = join(r_output, str(job_id), 'case_ids.txt')
        control_path = join(r_output, str(job_id), 'control_ids.txt')
        debug = 'T'

        cmd = [rscript_path, join(rdir_path,'manual_controls_check.R'), job_id, case_path, control_path, debug]
        print cmd
        print "Inside manual_controls_check.R"

        try:
            x = subprocess.check_output(cmd, universal_newlines=True)

            print x

            data = {'data': 'dataa'}
        except Exception as e:
            print "Inside Excep"
            print e
            return json.dumps("fail")
        return json.dumps(data)

        # return json.dumps(data)

### UPLOAD SIGNATURE FILE 
## added P Bills, MSU IT Services 5/2020

@dashboardRoute.route('/upload', methods=["GET", "POST"])
def signature_upload_form():
    """form to accept a signature file for processing.
    Post of the form 
        creates database records Job, JobDetails, and User
        creates new job folder and saves signature file with standard name
        and submit Rscript in subprocess"""


    if request.method == 'GET':
        return render_template('dashboard/signature_upload_form.html')

    # assuming post 
    print "posting from signature form"
    # handle post of sigfile
    # create new job record, and if no users logged in, also create new user 
    
    #### FILE
    # check if file was uploaded or not, and name it with .txt extension for safety

    if 'file' not in request.files:
        print 'no file in request.files'
        flash('No file selected')
        return redirect(request.url)

    sigfile = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if not sigfile:
        print 'no file sent, file not saved'
        flash('No file sent, please try upload again')
        return redirect(request.url)

    if sigfile.filename == '':
        print 'signature file upload, but filename blank'
        flash('No file actually selected')
        return redirect(request.url)
    
    ### collect form information
    job_name = request.form.get('job_name',"upload {} on {}".format(sigfile.filename, datetime.utcnow())) # validate this
    job_email = request.form.get('job_email',None)
    job_description = request.form.get('job_description','uploaded job')
    choose_fda_drugs = request.form.get('choose_fda_drugs', 'T')
    max_gene_size = request.form.get('max_genes_size', 50)
    landmark  = 1 # request.form.get('max_genes_size', 1)  # this value must be 1 or R code crashes
    job_timestamp = datetime.utcnow()

    ### DATABASE RECORDS : Job, JobDetails, AnonymousUser
    #### JOB
    try:
        job = Job(name=job_name,
            description=job_description,
            creationTime = job_timestamp,  
            is_save = True, 
            status = 6)
        job.save() # save to db, assign id  
        # Create Minimal Job details record for signature-only anonymous jobs.  It will not include case or other data
        jobdetails = JobDetails(job_id = job.id, 
            choose_fda_drugs = choose_fda_drugs,   
            max_gene_size = max_gene_size, 
            landmark = landmark, 
            creationTime = job_timestamp)

        jobdetails.save()

    except Exception as e:               
        flash('Could not create Job database entry')
        result = {"message": "error creating job record " + str(e), "category": "error" }
        return json.dumps(result)

    else:
        print("created new job {} id {}".format( job.name, job.id))

    ######## save uploaded sig file into new job folder using standard name
    DEFAULT_SIGFILE_NAME = "dz_signature.csv"  # discovered in R code
    stat_path = join(r_output, str(job.id)) # stat_path = app.config['APPLICATION_ROOT'] + '/static/data/' + str(job_id) + '/'
    signature_file_path = join(stat_path, DEFAULT_SIGFILE_NAME)

    # TODO add exception handling 
    if not exists(stat_path):
        makedirs(stat_path)

    sigfile.save(signature_file_path)

    ##### set user for this job
    # if a user is logged in during upload, use that user
    # if a user is not logged in, createa new 'job only' user account
    # a user account of some kind is needed for consistency and because the key generator uses user data

    if g.user:        
        job_user = g.user
        print('assigning job to logged-in user {}'.format(g.user))
    else:
        # create anonymous user
        job_user = User.job_only_user(job.id, job_email=job_email)
        job_user.save()
        print('created new user {}'.format(job_user.id))

    job.update(commit=True, user_id = job_user.id) # add user to job
    
    ### url and key for job
    # with a user id, can create a login-free access
    job_key = job.generate_key()
    job_url = url_for('.job_output', _external = True, job_id=job.id, key = job_key)
    
    #### R command
    rscript = 'compute_sRGES_from_signatures.R'
    cmd = [ rscript_path, join(rdir_path, rscript), str(job.id), signature_file_path, choose_fda_drugs, str(max_gene_size), str(landmark)]
    # example Rscript $RREPO_PATH/compute_sRGES_from_signatures.R 1041 $RREPO_OUTPUT/1041/dz_signature.csv true 50 1

    try:
        pid = subprocess.Popen(cmd).pid
        print "submitted cmd {} with pid {}".format(cmd, pid)
        pass

    except Exception as e:
        result = {"message": "Job submission error  {}".format(e), "category": "error" }
        return json.dumps(result)

    job.update(commit=True, status=6) # set to 6 for now to allow viewing output
    db.session.commit()

    # since post is called by JS, render job submission info html and return for inserting into page 
    headers = {'Content-Type': 'text/html'}
    return make_response(render_template('dashboard/signature_upload_result.html', job_url = job_url, job_id=job.id, cmd=cmd),200,headers)
    # return json.dumps(result)



@dashboardRoute.route('/job/<job_id>/status/<status>', methods=["POST"])
def update_job_status(job_id, status):
    """DRAFT WIP
    this is an api call to update the job's status
    given the job's key (or a complete URL) can set status to 6 (completed)
    example url would be http://octad.org/job/999/update/6?key=abcdef12345 
    Note this is a post but any posted data is ignored, 
    all data is in the URL to make it easy 
    
    if we send R the URL as a parameter, Call this from R with the httr package
       
       success_url=args[5]  # eg. "http://localhost:5000/job/1105/status/6?key=703cfd32716aeea94a2c51d260195e26"
       # process stuff successfully 
       resp = httr::POST(success_url)
       status = content(resp)
       # check that status was updated correctly
    """

    job_key = request.args.get('key', default = '', type = str)
    if not job_key:
        resp = {"status":""}

    #TODO validate status value
        
    job = Job.query.get(job_id)
    if job:
        if job.generate_key() == job_key:
            status = int(status)
            job.status = status
            job.save()
            return json.dumps({"status":str(status)}) 
        else:
            # incorrect key
            return json.dumps({"status":""}) 
    else:
        return json.dumps({"status":""})


### URL to view job output without logging in
def url_for_job_output(job):
    # TODO use url_for properly here 
    return url_for('.job_output', job_id=job.id, key = job.generate_key())
