from flask import g
from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, Boolean, TEXT, or_
from sqlalchemy.orm import relationship, backref
from models.base import CRUDMixin, db
import hashlib

STATUS = {0: 'Created', 1: 'Case Visualization', 2: 'Ref Tissue Algo Run', 3: 'Control Visualization',
		4: 'Signature Compute', 5: 'Drug Prediction In-progress', 6: 'Completed'}

FEATURES = {1: 'Tissue Type', 2: 'Site', 3: 'Gender', 4: 'Metastatic Site', 5: 'EGFR',
			6: 'IDH1', 7: 'IDH2', 8: 'TP53', 9: 'Age', 10: 'Tumor Grade', 11: 'Tumor Stage', 12: 'Mutation', 13: 'Gain', 14: 'Loss'}


class Samples(CRUDMixin, db.Model):
	"""
		Sample info is nothing but predefined data by application
	"""
	id = Column(Integer, primary_key=True, autoincrement=True)
	sample_id = Column(String(100), nullable=False)
	tissue_type = Column(String(50), nullable=False)
	site = Column(String(50), nullable=False)
	gender = Column(String(10), nullable=False)
	metastatic_site = Column(String(10), nullable=False)
	cancer = Column(String(100), nullable=False)
	EGFR = Column(String(10), nullable=False, default='NA')
	IDH1 = Column(String(10), nullable=False, default='NA')
	IDH2 = Column(String(10), nullable=False, default='NA')
	TP53 = Column(String(10), nullable=False, default='NA')
	age_in_year = Column(Integer, nullable=True)
	tumor_grade = Column(String(100), nullable=True)
	tumor_stage = Column(String(100), nullable=True)
	mutation_list = Column(String(100), nullable=False)
	gain_list = Column(String(100), nullable=False)
	loss_list = Column(String(100), nullable=False)

class Job(CRUDMixin, db.Model):
	"""
		Job Info created by user
	"""
	id = Column(Integer, primary_key=True, autoincrement=True)
	user_id = Column(Integer, ForeignKey('portaluser.id'), nullable=True)
	name = Column(String(50))
	status = Column(Integer, nullable=False, default=0)
	creationTime = Column(TIMESTAMP, nullable=False)
	description = Column(TEXT, nullable=True)
	is_save = Column(Boolean, default=False)

	userDetails = relationship("User", backref=backref("users"))


	#### job key generation methods 
	# added by P Bills, MSU IT Services, May 2020
	# goal is to allow access of job details without logging in, using a form of an api 'key'
	# a job can generate and show it's key, and check that a given key matches
	# key generation is based on the associated user's password and the job id
	# each job has it's own key
    # to create jobs without logging in, create a new random 'job only' user
	def check_key(self,key):
		""" given a job, check if key is correct against key generator"""
		job_user = self.userDetails
		if job_user:
			return(self.generate_key() == key)
		else:
			print("can't check key, job {} has no user_id".format(self.id))

	def generate_key(self):
		"""a given job can generate a key that can be used 
		   to look up the job via URL without login
		   use very basic method of hash the job id and associated user password
		"""

		# look up associated user id
		# combination of userid and 
		job_user = self.userDetails
		if job_user:
			hasher = hashlib.md5()
			hasher.update(str(self.id))
			hasher.update(job_user.password)
			return hasher.hexdigest()
		else:
			print("job {} has no user_id".format(self.id))
			return None

	# modified by PBills MSU IT Services, May 2020
	# allow job name as a parameter, and create time stamp as this field can not be null
	@staticmethod
	def get_new_id(jobname='new_job'):
		try:
			# lastrowid = Job.query.order_by('-id').first().id
			# print lastrowid
			# return lastrowid + 1
			import time, datetime
			if g.user:
				job = Job(name=jobname, user_id=g.user.id)
			else:
				job = Job(name=jobname)

			job.creationTime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

			job.save()
			jobDetails = JobDetails(job_id=job.id, creationTime = job.creationTime)
			jobDetails.save()
			return job.id
		except Exception as e:
			print str(e)
			return 1

class JobDetails(CRUDMixin, db.Model):
	id = Column(Integer, primary_key=True, autoincrement=True)
	job_id = Column(Integer, ForeignKey('job.id', ondelete='cascade'))
	creationTime = Column(TIMESTAMP, nullable=False)
	disease_name = Column(String(200), nullable=True)
	case_sample_id = Column(TEXT, nullable=True)
	case_tissue_type = Column(String(50), nullable=True)
	case_site = Column(String(50), nullable=True)
	case_gender = Column(String(10), nullable=True)
	case_metastatic_site = Column(String(10), nullable=True)
	case_EGFR = Column(String(10), nullable=True, default='NA')
	case_IDH1 = Column(String(10), nullable=True, default='NA')
	case_IDH2 = Column(String(10), nullable=True, default='NA')
	case_TP53 = Column(String(10), nullable=True, default='NA')
	case_age_in_year = Column(String(50), nullable=True)
	case_tumor_grade = Column(String(100), nullable=True)
	case_tumor_stage = Column(String(100), nullable=True)
	ctrl_sample_id = Column(TEXT, nullable=True)
	ctrl_tissue_type = Column(String(50), nullable=True)
	ctrl_site = Column(String(50), nullable=True)
	ctrl_gender = Column(String(10), nullable=True)
	ctrl_metastatic_site = Column(String(10), nullable=True)
	ctrl_EGFR = Column(String(10), nullable=True, default='NA')
	ctrl_IDH1 = Column(String(10), nullable=True, default='NA')
	ctrl_IDH2 = Column(String(10), nullable=True, default='NA')
	ctrl_TP53 = Column(String(10), nullable=True, default='NA')
	ctrl_age_in_year = Column(String(50), nullable=True)
	ctrl_tumor_grade = Column(String(100), nullable=True)
	ctrl_tumor_stage = Column(String(100), nullable=True)
	de_method = Column(String(50), nullable=True)
	dz_fc_threshold = Column(String(50), nullable=True)
	dz_p_threshold = Column(String(50), nullable=True)
	database = Column(String(50), nullable=True)
	choose_fda_drugs = Column(String(10), nullable=True)
	max_gene_size = Column(String(50), nullable=True)
	landmark = Column(String(50), nullable=True)
	weight_cell_line = Column(String(10), nullable=True)
	debug = Column(String(10), nullable=True)
	signature_graphs = Column(String(255), nullable=True)
	drug_graphs = Column(String(255), nullable=True)

	jobDetails = relationship("Job", backref=backref("jobs"))


def get_sites(disease=None, tissue_type=None, gender=None, metastatic=None,
			  egfr=None, idh1=None, idh2=None, tp53=None, age=None,
			  tumor_grade=None, tumor_stage=None):
	filter_str = []
	if disease:
		filter_str.append(or_(Samples.cancer.in_(disease)))
	if tissue_type:
		filter_str.append(or_(Samples.tissue_type.in_(tissue_type)))
	if gender:
		filter_str.append(Samples.gender == gender)
	if metastatic:
		filter_str.append(Samples.metastatic_site == metastatic)
	if egfr:
		filter_str.append(Samples.EGFR == egfr)
	if idh1:
		filter_str.append(Samples.IDH1 == idh1)
	if idh2:
		filter_str.append(Samples.IDH2 == idh2)
	if tp53:
		filter_str.append(Samples.TP53 == tp53)
	if age:
		age_range = age.split('-')
		start = int(age_range[0].strip())
		end = int(age_range[1].strip())
		filter_str.append(Samples.age_in_year.between(start, end))
	if tumor_grade:
		filter_str.append(Samples.tumor_grade == tumor_grade)
	if tumor_stage:
		filter_str.append(or_(Samples.tumor_stage.in_(tumor_stage)))

	sites = db.session.query(Samples.site).filter(*filter_str).order_by(Samples.site.asc()).distinct().all()

	return [s[0] for s in sites if s[0] and s[0] != '<NOT PROVIDED>']


def get_metastatics(disease=None, tissue_type=None, site=None, gender=None, egfr=None, idh1=None, idh2=None, tp53=None,
					age=None, tumor_grade=None, tumor_stage=None):
	filter_str = []
	if disease:
		filter_str.append(or_(Samples.cancer.in_(disease)))
	if tissue_type:
		filter_str.append(or_(Samples.tissue_type.in_(tissue_type)))
	if gender:
		filter_str.append(Samples.gender == gender)
	if site:
		filter_str.append(Samples.site == site)
	if egfr:
		filter_str.append(Samples.EGFR == egfr)
	if idh1:
		filter_str.append(Samples.IDH1 == idh1)
	if idh2:
		filter_str.append(Samples.IDH2 == idh2)
	if tp53:
		filter_str.append(Samples.TP53 == tp53)
	if age:
		age_range = age.split('-')
		start = int(age_range[0].strip())
		end = int(age_range[1].strip())
		filter_str.append(Samples.age_in_year.between(start, end))
	if tumor_grade:
		filter_str.append(Samples.tumor_grade == tumor_grade)
	if tumor_stage:
		filter_str.append(or_(Samples.tumor_stage.in_(tumor_stage)))

	metastatics = db.session.query(Samples.metastatic_site).filter(*filter_str).order_by(Samples.metastatic_site.asc()).distinct().all()

	return [m[0] for m in metastatics if m[0]]


def get_grades(disease=None, tissue_type=None, site=None, gender=None, metastatic=None,
			   egfr=None, idh1=None, idh2=None, tp53=None, age=None, tumor_stage=None):
	filter_str = []

	print "Here is:"
	print disease

	print tumor_stage

	if disease:
		filter_str.append(or_(Samples.cancer.in_(disease)))
	if tissue_type:
		filter_str.append(or_(Samples.tissue_type.in_(tissue_type)))
	if gender:
		filter_str.append(Samples.gender == gender)
	if site:
		filter_str.append(Samples.site == site)
	if egfr:
		filter_str.append(Samples.EGFR == egfr)
	if idh1:
		filter_str.append(Samples.IDH1 == idh1)
	if idh2:
		filter_str.append(Samples.IDH2 == idh2)
	if tp53:
		filter_str.append(Samples.TP53 == tp53)
	if age:
		age_range = age.split('-')
		start = int(age_range[0].strip())
		end = int(age_range[1].strip())
		filter_str.append(Samples.age_in_year.between(start, end))
	if metastatic:
		filter_str.append(Samples.metastatic_site == metastatic)
	if tumor_stage:
		filter_str.append(or_(Samples.tumor_stage.in_(tumor_stage)))

	print filter_str

	grades = db.session.query(Samples.tumor_grade).filter(*filter_str).order_by(Samples.tumor_grade.asc()).distinct().all()

	return [g[0] for g in grades if g[0]]


def get_stages(disease=None, tissue_type=None, site=None, gender=None, metastatic=None,
			   egfr=None, idh1=None, idh2=None, tp53=None, age=None, tumor_grade=None):
	filter_str = []
	if disease:
		filter_str.append(or_(Samples.cancer.in_(disease)))
	if tissue_type:
		filter_str.append(or_(Samples.tissue_type.in_(tissue_type)))
	if gender:
		filter_str.append(Samples.gender == gender)
	if site:
		filter_str.append(Samples.site == site)
	if egfr:
		filter_str.append(Samples.EGFR == egfr)
	if idh1:
		filter_str.append(Samples.IDH1 == idh1)
	if idh2:
		filter_str.append(Samples.IDH2 == idh2)
	if tp53:
		filter_str.append(Samples.TP53 == tp53)
	if age:
		age_range = age.split('-')
		start = int(age_range[0].strip())
		end = int(age_range[1].strip())
		filter_str.append(Samples.age_in_year.between(start, end))
	if tumor_grade:
		filter_str.append(Samples.tumor_grade == tumor_grade)
	if metastatic:
		filter_str.append(Samples.metastatic_site == metastatic)

	stages = db.session.query(Samples.tumor_stage).filter(*filter_str).order_by(Samples.tumor_stage.asc()).distinct().all()

	return [s[0] for s in stages if s[0]]


def get_diseases():
	diseases = db.session.query(Samples.cancer).order_by(Samples.cancer.asc()).distinct().all()
	return [d[0] for d in diseases if d[0]]


def get_tissue_types(disease=None, site=None, gender=None, metastatic=None, egfr=None, idh1=None,
					 idh2=None, tp53=None, age=None, tumor_grade=None, tumor_stage=None):
	filter_str = []
	if disease:
		filter_str.append(or_(Samples.cancer.in_(disease)))
	if gender:
		filter_str.append(Samples.gender == gender)
	if site:
		filter_str.append(Samples.site == site)
	if egfr:
		filter_str.append(Samples.EGFR == egfr)
	if idh1:
		filter_str.append(Samples.IDH1 == idh1)
	if idh2:
		filter_str.append(Samples.IDH2 == idh2)
	if tp53:
		filter_str.append(Samples.TP53 == tp53)
	if age:
		age_range = age.split('-')
		start = int(age_range[0].strip())
		end = int(age_range[1].strip())
		filter_str.append(Samples.age_in_year.between(start, end))
	if tumor_grade:
		filter_str.append(Samples.tumor_grade == tumor_grade)
	if metastatic:
		filter_str.append(Samples.metastatic_site == metastatic)
	if tumor_stage:
		filter_str.append(or_(Samples.tumor_stage.in_(tumor_stage)))

	tissue_types = db.session.query(Samples.tissue_type).filter((or_(Samples.cancer.in_(disease)))).order_by(Samples.tissue_type.asc()).distinct().all()

	return [s[0] for s in tissue_types if s[0] and s[0] != 'adjacent']



def get_gender(disease=None, tissue_type=None, site=None, metastatic=None, egfr=None, idh1=None, idh2=None,
			   tp53=None, age=None, tumor_grade=None, tumor_stage=None):
	filter_str = []
	if disease:
		filter_str.append(or_(Samples.cancer.in_(disease)))
	if tissue_type:
		filter_str.append(or_(Samples.tissue_type.in_(tissue_type)))
	if metastatic:
		filter_str.append(Samples.metastatic_site == metastatic)
	if site:
		filter_str.append(Samples.site == site)
	if egfr:
		filter_str.append(Samples.EGFR == egfr)
	if idh1:
		filter_str.append(Samples.IDH1 == idh1)
	if idh2:
		filter_str.append(Samples.IDH2 == idh2)
	if tp53:
		filter_str.append(Samples.TP53 == tp53)
	if age:
		age_range = age.split('-')
		start = int(age_range[0].strip())
		end = int(age_range[1].strip())
		filter_str.append(Samples.age_in_year.between(start, end))
	if tumor_grade:
		filter_str.append(Samples.tumor_grade == tumor_grade)
	if tumor_stage:
		filter_str.append(or_(Samples.tumor_stage.in_(tumor_stage)))

	gender = db.session.query(Samples.gender).filter(*filter_str).order_by(Samples.gender.asc()).distinct().all()

	return [s[0] for s in gender if s[0]]


def get_EGFR(disease=None, tissue_type=None, site=None, gender=None, metastatic=None, idh1=None, idh2=None, tp53=None, age=None, tumor_grade=None, tumor_stage=None):
	filter_str = []
	if disease:
		filter_str.append(or_(Samples.cancer.in_(disease)))
	if tissue_type:
		filter_str.append(or_(Samples.tissue_type.in_(tissue_type)))
	if metastatic:
		filter_str.append(Samples.metastatic_site == metastatic)
	if site:
		filter_str.append(Samples.site == site)
	if gender:
		filter_str.append(Samples.gender == gender)
	if idh1:
		filter_str.append(Samples.IDH1 == idh1)
	if idh2:
		filter_str.append(Samples.IDH2 == idh2)
	if tp53:
		filter_str.append(Samples.TP53 == tp53)
	if age:
		age_range = age.split('-')
		start = int(age_range[0].strip())
		end = int(age_range[1].strip())
		filter_str.append(Samples.age_in_year.between(start, end))
	if tumor_grade:
		filter_str.append(Samples.tumor_grade == tumor_grade)
	if tumor_stage:
		filter_str.append(or_(Samples.tumor_stage.in_(tumor_stage)))

	egfr = db.session.query(Samples.EGFR).filter(*filter_str).order_by(Samples.EGFR.asc()).distinct().all()

	return [s[0] for s in egfr if s[0]]


def get_IDH1(disease=None, tissue_type=None, site=None, gender=None, metastatic=None, egfr=None, idh2=None, tp53=None, age=None, tumor_grade=None, tumor_stage=None):
	filter_str = []
	if disease:
		filter_str.append(or_(Samples.cancer.in_(disease)))
	if tissue_type:
		filter_str.append(or_(Samples.tissue_type.in_(tissue_type)))
	if metastatic:
		filter_str.append(Samples.metastatic_site == metastatic)
	if site:
		filter_str.append(Samples.site == site)
	if egfr:
		filter_str.append(Samples.EGFR == egfr)
	if gender:
		filter_str.append(Samples.gender == gender)
	if idh2:
		filter_str.append(Samples.IDH2 == idh2)
	if tp53:
		filter_str.append(Samples.TP53 == tp53)
	if age:
		age_range = age.split('-')
		start = int(age_range[0].strip())
		end = int(age_range[1].strip())
		filter_str.append(Samples.age_in_year.between(start, end))
	if tumor_grade:
		filter_str.append(Samples.tumor_grade == tumor_grade)
	if tumor_stage:
		filter_str.append(or_(Samples.tumor_stage.in_(tumor_stage)))

	idh1 = db.session.query(Samples.IDH1).filter(*filter_str).order_by(Samples.IDH1.asc()).distinct().all()

	return [s[0] for s in idh1 if s[0]]


def get_IDH2(disease=None, tissue_type=None, site=None, gender=None, metastatic=None, egfr=None, idh1=None, tp53=None, age=None, tumor_grade=None, tumor_stage=None):
	filter_str = []
	if disease:
		filter_str.append(or_(Samples.cancer.in_(disease)))
	if tissue_type:
		filter_str.append(or_(Samples.tissue_type.in_(tissue_type)))
	if metastatic:
		filter_str.append(Samples.metastatic_site == metastatic)
	if site:
		filter_str.append(Samples.site == site)
	if egfr:
		filter_str.append(Samples.EGFR == egfr)
	if idh1:
		filter_str.append(Samples.IDH1 == idh1)
	if gender:
		filter_str.append(Samples.gender == gender)
	if tp53:
		filter_str.append(Samples.TP53 == tp53)
	if age:
		age_range = age.split('-')
		start = int(age_range[0].strip())
		end = int(age_range[1].strip())
		filter_str.append(Samples.age_in_year.between(start, end))
	if tumor_grade:
		filter_str.append(Samples.tumor_grade == tumor_grade)
	if tumor_stage:
		filter_str.append(or_(Samples.tumor_stage.in_(tumor_stage)))

	idh2 = db.session.query(Samples.IDH2).filter(*filter_str).order_by(Samples.IDH2.asc()).distinct().all()

	return [s[0] for s in idh2 if s[0]]


def get_TP53(disease=None, tissue_type=None, site=None, gender=None, metastatic=None, egfr=None, idh1=None, idh2=None, age=None, tumor_grade=None, tumor_stage=None):
	filter_str = []
	if disease:
		filter_str.append(or_(Samples.cancer.in_(disease)))
	if tissue_type:
		filter_str.append(or_(Samples.tissue_type.in_(tissue_type)))
	if metastatic:
		filter_str.append(Samples.metastatic_site == metastatic)
	if site:
		filter_str.append(Samples.site == site)
	if egfr:
		filter_str.append(Samples.EGFR == egfr)
	if idh1:
		filter_str.append(Samples.IDH1 == idh1)
	if idh2:
		filter_str.append(Samples.IDH2 == idh2)
	if gender:
		filter_str.append(Samples.gender == gender)
	if age:
		age_range = age.split('-')
		start = int(age_range[0].strip())
		end = int(age_range[1].strip())
		filter_str.append(Samples.age_in_year.between(start, end))
	if tumor_grade:
		filter_str.append(Samples.tumor_grade == tumor_grade)
	if tumor_stage:
		filter_str.append(or_(Samples.tumor_stage.in_(tumor_stage)))

	tp53 = db.session.query(Samples.TP53).filter(*filter_str).order_by(Samples.TP53.asc()).distinct().all()

	return [s[0] for s in tp53 if s[0]]

def get_mutation_list(disease=None, tissue_type=None, site=None, gender=None, metastatic=None, egfr=None, idh1=None, idh2=None, age=None, tumor_grade=None, tumor_stage=None, mutation_list=None):
	filter_str = []
	if disease:
		filter_str.append(or_(Samples.cancer.in_(disease)))
	if tissue_type:
		filter_str.append(or_(Samples.tissue_type.in_(tissue_type)))
	if metastatic:
		filter_str.append(Samples.metastatic_site == metastatic)
	if site:
		filter_str.append(Samples.site == site)
	if egfr:
		filter_str.append(Samples.EGFR == egfr)
	if idh1:
		filter_str.append(Samples.IDH1 == idh1)
	if idh2:
		filter_str.append(Samples.IDH2 == idh2)
	if gender:
		filter_str.append(Samples.gender == gender)
	if age:
		age_range = age.split('-')
		start = int(age_range[0].strip())
		end = int(age_range[1].strip())
		filter_str.append(Samples.age_in_year.between(start, end))
	if tumor_grade:
		filter_str.append(Samples.tumor_grade == tumor_grade)
	if tumor_stage:
		filter_str.append(or_(Samples.tumor_stage.in_(tumor_stage)))
	if mutation_list:
		filter_str.append(or_(Samples.mutation_list.in_(mutation_list)))

	mutation_list_data = db.session.query(Samples.mutation_list).filter(*filter_str).order_by(Samples.mutation_list.asc()).distinct().all()

	return [s[0] for s in mutation_list_data if s[0]]

def get_gain_list(disease=None, tissue_type=None, site=None, gender=None, metastatic=None, egfr=None, idh1=None, idh2=None, age=None, tumor_grade=None, tumor_stage=None, gain_list=None):
	filter_str = []
	if disease:
		filter_str.append(or_(Samples.cancer.in_(disease)))
	if tissue_type:
		filter_str.append(or_(Samples.tissue_type.in_(tissue_type)))
	if metastatic:
		filter_str.append(Samples.metastatic_site == metastatic)
	if site:
		filter_str.append(Samples.site == site)
	if egfr:
		filter_str.append(Samples.EGFR == egfr)
	if idh1:
		filter_str.append(Samples.IDH1 == idh1)
	if idh2:
		filter_str.append(Samples.IDH2 == idh2)
	if gender:
		filter_str.append(Samples.gender == gender)
	if age:
		age_range = age.split('-')
		start = int(age_range[0].strip())
		end = int(age_range[1].strip())
		filter_str.append(Samples.age_in_year.between(start, end))
	if tumor_grade:
		filter_str.append(Samples.tumor_grade == tumor_grade)
	if tumor_stage:
		filter_str.append(or_(Samples.tumor_stage.in_(tumor_stage)))
	if gain_list:
		filter_str.append(or_(Samples.gain_list.in_(gain_list)))

	gain_list_data = db.session.query(Samples.gain_list).filter(*filter_str).order_by(Samples.gain_list.asc()).distinct().all()

	return [s[0] for s in gain_list_data if s[0]]


def get_loss_list(disease=None, tissue_type=None, site=None, gender=None, metastatic=None, egfr=None, idh1=None, idh2=None, age=None, tumor_grade=None, tumor_stage=None, loss_list=None):
	filter_str = []
	if disease:
		filter_str.append(or_(Samples.cancer.in_(disease)))
	if tissue_type:
		filter_str.append(or_(Samples.tissue_type.in_(tissue_type)))
	if metastatic:
		filter_str.append(Samples.metastatic_site == metastatic)
	if site:
		filter_str.append(Samples.site == site)
	if egfr:
		filter_str.append(Samples.EGFR == egfr)
	if idh1:
		filter_str.append(Samples.IDH1 == idh1)
	if idh2:
		filter_str.append(Samples.IDH2 == idh2)
	if gender:
		filter_str.append(Samples.gender == gender)
	if age:
		age_range = age.split('-')
		start = int(age_range[0].strip())
		end = int(age_range[1].strip())
		filter_str.append(Samples.age_in_year.between(start, end))
	if tumor_grade:
		filter_str.append(Samples.tumor_grade == tumor_grade)
	if tumor_stage:
		filter_str.append(or_(Samples.tumor_stage.in_(tumor_stage)))
	if loss_list:
		filter_str.append(or_(Samples.loss_list.in_(loss_list)))

	loss_list_data = db.session.query(Samples.loss_list).filter(*filter_str).order_by(Samples.loss_list.asc()).distinct().all()

	return [s[0] for s in loss_list_data if s[0]]