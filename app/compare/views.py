import ast
import os

from flask import render_template, request, flash, url_for, redirect, current_app
from flask_login import login_required, current_user
from sqlalchemy.sql import text

from . import compare
from . import analysis
from . import batch_processing
from . forms import FileUploadForm

from .. import db
from .. models import Batch, Session
from .. app_utils import get_session_timestamp

def check_admin():
	"""
	Prevent non-admins from accessing a page
	"""
	if not current_user.is_admin:
		abort(403)

@compare.route('/start_session', methods=['GET','POST'])
@login_required
def start_session():
	"""
	Render the file upload template on the /start_session route
	"""
	form = FileUploadForm()
	if form.validate_on_submit():
		session_id = batch_processing.create_session(current_user.id)
		batch_processing.process_batches(session_id,request)
		batch_processing.read_files(session_id)

		# flash('You have successfully deleted the session.')
		return redirect(url_for('compare.list_sessions'))

	return render_template(
		'compare/start_session.html',
		title="Start comparing",
		form=form)

@compare.route('/list_sessions', methods=['GET','POST'])
@login_required
def list_sessions():
	"""
	Render the session list template on the /list_sessions route
	"""
	list_sessions_sql = '''
	SELECT sessions.id, sessions.started_timestamp, GROUP_CONCAT(batches.source, ' ; ') AS sources
	FROM sessions
	JOIN batches ON sessions.id=batches.session_id
	GROUP BY sessions.id, sessions.started_timestamp;
	'''
	# sql = "select sessions.id, sessions.started_timestamp, group_concat(batches.source) from sessions join batches on sessions.id=batches.session_id group by sessions.id, sessions.started_timestamp;"
	sessions = db.session.execute(list_sessions_sql).fetchall()
	return render_template(
		'compare/list_sessions.html',
		title="Your comparison sessions",
		sessions=sessions
		)

@compare.route('/delete_session/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_session(id):
	"""
	Delete a session from the database
	"""
	# check_admin()

	_session = Session.query.get_or_404(id)
	db.session.delete(_session)
	db.session.commit()
	flash('You have successfully deleted the session.')

	# redirect to the users page
	return redirect(url_for('compare.list_sessions'))

	return render_template(title="Delete Session")

@compare.route('/analysis_menu/session_<int:id>', methods=['GET','POST'])
@login_required
def analysis_menu(id):
	"""
	Render the analysis template on the /analysis_menu route
	list the different analyses you can do on a session
	"""
	session_timestamp = get_session_timestamp(id)
	return render_template(
		'compare/analysis_menu.html',
		title="Analysis Menu",
		id=id,
		session_timestamp=session_timestamp
		)

@compare.route('/batch_compare/session_<int:id>', methods=['GET','POST'])
@login_required
def batch_compare(id):
	"""
	Render the batch comparison template on the /batch_compare route
	this is an overal comparison of two record batches from a session
	"""
	_session = Session.query.get(id)
	session_dict = _session.overall_batch_comparison_dict
	if session_dict:
		session_dict = ast.literal_eval(session_dict)
	if not session_dict:
		session_dict = analysis.compare_batches(id)
	return render_template(
		'compare/batch_compare.html',
		title="Compare batches",
		session_dict=session_dict,
		id=id
		)

@compare.route('/batch_compare_subjects/session_<int:id>', methods=['GET','POST'])
@login_required
def batch_compare_subjects(id):
	"""
	Render the batch subject comparison template on the /subject_compare route
	this is a comparison of two record batches from a session
	focusing on 6xx fields
	"""
	session_dict = Session.query.get(id).subject_batch_comparison_dict
	if session_dict:
		session_dict = ast.literal_eval(session_dict)
	if not session_dict:
		overall_dict = Session.query.get(id).overall_batch_comparison_dict
		if overall_dict:
			session_dict = analysis.batch_compare_subjects(id)
		else:
			flash("Please run an overall comparison analysis\
				on session {} before running more detailed analyses :)".format(id))
			return redirect(url_for('compare.analysis_menu',id=id))
	print(session_dict)
	return render_template(
		'compare/batch_compare_subjects.html',
		title="Compare batches by subject",
		session_dict=session_dict,
		id=id
		)

@compare.route('/record_compare_subjects/row_<int:id>', methods=['GET','POST'])
@login_required
def record_compare_subjects(id):
	"""
	Render the batch subject comparison template on the /subject_compare route
	this is a comparison of two record batches from a session
	focusing on 6xx fields
	"""
	session_dict = Session.query.get(id).subject_batch_comparison_dict
	if session_dict:
		session_dict = ast.literal_eval(session_dict)
	if not session_dict:
		overall_dict = Session.query.get(id).overall_batch_comparison_dict
		if overall_dict:
			session_dict = analysis.batch_compare_subjects(id)
		else:
			flash("Please run an overall comparison analysis\
				on session {} before running more detailed analyses :)".format(id))
			return redirect(url_for('compare.analysis_menu',id=id))
	print(session_dict)
	return render_template(
		'compare/batch_compare_subjects.html',
		title="Compare batches by subject",
		session_dict=session_dict,
		id=id
		)
