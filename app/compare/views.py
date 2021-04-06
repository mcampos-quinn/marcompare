import ast
import os

from flask import render_template, request, flash, url_for, redirect, current_app
from flask_login import login_required, current_user
from sqlalchemy.sql import text

from . import compare
from . import record_analysis, batch_analysis
from . import batch_processing
from . forms import FileUploadForm, SessionForm

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
		print(request.form)
		session_id = batch_processing.create_session(current_user.id)
		batch_processing.process_batches(session_id,request)
		batch_processing.read_files(session_id)

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
	SELECT sessions.id, sessions.started_timestamp, sessions.notes, GROUP_CONCAT(batches.source, ' ; ') AS sources
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

@compare.route('/edit_session/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_session(id):
	"""
	Edit a session
	"""

	session = Session.query.get_or_404(id)
	form = SessionForm(obj=session)
	if form.validate_on_submit():
		session.notes = form.session_notes.data
		db.session.commit()
		flash('You have successfully edited session {}.'.format(id))

		# redirect to the departments page
		return redirect(url_for('compare.list_sessions'))

	form.session_notes.data = session.notes
	return render_template(
		'compare/edit_session.html',
		action="Edit",
		form=form,
		session=session,
		title="Edit Session"
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
		session_dict = batch_analysis.compare_batches(id)
	return render_template(
		'compare/batch_compare.html',
		title="Compare batches",
		session_dict=session_dict,
		id=id
		)

@compare.route('/batch_compare_author/session_<int:id>', methods=['GET','POST'])
@login_required
def batch_compare_author(id):
	"""
	Render the batch author comparison template on the /batch_compare_author route
	this is a comparison of two record batches from a session
	focusing on 1xx fields
	"""
	field_set = "1xx"
	session_dict = Session.query.get(id).author_batch_comparison_dict
	if session_dict:
		session_dict = ast.literal_eval(session_dict)
	if not session_dict:
		overall_dict = Session.query.get(id).overall_batch_comparison_dict
		if overall_dict:
			session_dict = batch_analysis.batch_compare_field_set(id,field_set)
		else:
			flash("Please run an overall comparison analysis\
				on session {} before running more detailed analyses :)".format(id))
			return redirect(url_for('compare.analysis_menu',id=id))
	# print(session_dict)
	return render_template(
		'compare/batch_compare_field_set.html',
		title="Compare batches by {} fields".format(field_set),
		session_dict=session_dict,
		field_set=field_set,
		field_set_label="Author",
		field_set_count="author_field_count",
		id=id
		)

@compare.route('/batch_compare_title/session_<int:id>', methods=['GET','POST'])
@login_required
def batch_compare_title(id):
	"""
	Render the batch title comparison template on the /batch_compare_title route
	this is a comparison of two record batches from a session
	focusing on 2xx fields
	"""
	field_set = "2xx"
	session_dict = Session.query.get(id).title_batch_comparison_dict
	if session_dict:
		session_dict = ast.literal_eval(session_dict)
	if not session_dict:
		overall_dict = Session.query.get(id).overall_batch_comparison_dict
		if overall_dict:
			session_dict = batch_analysis.batch_compare_field_set(id,field_set)
		else:
			flash("Please run an overall comparison analysis\
				on session {} before running more detailed analyses :)".format(id))
			return redirect(url_for('compare.analysis_menu',id=id))
	print(session_dict)
	return render_template(
		'compare/batch_compare_field_set.html',
		title="Compare batches by {} fields".format(field_set),
		session_dict=session_dict,
		field_set=field_set,
		field_set_label="Title",
		field_set_count="title_field_count",
		id=id
		)

@compare.route('/batch_compare_physical/session_<int:id>', methods=['GET','POST'])
@login_required
def batch_compare_physical(id):
	"""
	Render the batch physical description comparison template on the /batch_compare_physical route
	this is a comparison of two record batches from a session
	focusing on 3xx fields
	"""
	field_set = "3xx"
	session_dict = Session.query.get(id).physical_batch_comparison_dict
	if session_dict:
		session_dict = ast.literal_eval(session_dict)
	if not session_dict:
		overall_dict = Session.query.get(id).overall_batch_comparison_dict
		if overall_dict:
			session_dict = batch_analysis.batch_compare_field_set(id,field_set)
		else:
			flash("Please run an overall comparison analysis\
				on session {} before running more detailed analyses :)".format(id))
			return redirect(url_for('compare.analysis_menu',id=id))
	print(session_dict)
	return render_template(
		'compare/batch_compare_field_set.html',
		title="Compare batches by {} fields".format(field_set),
		session_dict=session_dict,
		field_set=field_set,
		field_set_label="Physical",
		field_set_count="physical_field_count",
		id=id
		)

@compare.route('/batch_compare_notes/session_<int:id>', methods=['GET','POST'])
@login_required
def batch_compare_notes(id):
	"""
	Render the batch note comparison template on the /batch_compare_notes route
	this is a comparison of two record batches from a session
	focusing on 5xx fields
	"""
	field_set = '5xx'
	session_dict = Session.query.get(id).note_batch_comparison_dict
	if session_dict:
		session_dict = ast.literal_eval(session_dict)
	if not session_dict:
		overall_dict = Session.query.get(id).overall_batch_comparison_dict
		if overall_dict:
			session_dict = batch_analysis.batch_compare_field_set(id,field_set)
		else:
			flash("Please run an overall comparison analysis\
				on session {} before running more detailed analyses :)".format(id))
			return redirect(url_for('compare.analysis_menu',id=id))
	print(session_dict)
	return render_template(
		'compare/batch_compare_field_set.html',
		title="Compare batches by {} fields".format(field_set),
		session_dict=session_dict,
		field_set=field_set,
		field_set_label="Note",
		field_set_count="note_field_count",
		id=id
		)

@compare.route('/batch_compare_subjects/session_<int:id>', methods=['GET','POST'])
@login_required
def batch_compare_subjects(id):
	"""
	Render the batch subject comparison template on the /batch_compare_subjects route
	this is a comparison of two record batches from a session
	focusing on 6xx fields
	"""
	field_set = '6xx'
	session_dict = Session.query.get(id).subject_batch_comparison_dict
	if session_dict:
		session_dict = ast.literal_eval(session_dict)
	if not session_dict:
		overall_dict = Session.query.get(id).overall_batch_comparison_dict
		if overall_dict:
			session_dict = batch_analysis.batch_compare_field_set(id,field_set)
		else:
			flash("Please run an overall comparison analysis\
				on session {} before running more detailed analyses :)".format(id))
			return redirect(url_for('compare.analysis_menu',id=id))
	print(session_dict)
	return render_template(
		'compare/batch_compare_field_set.html',
		title="Compare batches by {} fields".format(field_set),
		session_dict=session_dict,
		field_set=field_set,
		field_set_label="Subject",
		field_set_count="subject_field_count",
		id=id
		)

@compare.route('/batch_compare_added_author/session_<int:id>', methods=['GET','POST'])
@login_required
def batch_compare_added_author(id):
	"""
	Render the batch added author comparison template on the /batch_compare_added_author route
	this is a comparison of two record batches from a session
	focusing on 7xx fields
	"""
	field_set = '7xx'
	session_dict = Session.query.get(id).added_author_batch_comparison_dict
	if session_dict:
		session_dict = ast.literal_eval(session_dict)
	if not session_dict:
		overall_dict = Session.query.get(id).overall_batch_comparison_dict
		if overall_dict:
			session_dict = batch_analysis.batch_compare_field_set(id,field_set)
		else:
			flash("Please run an overall comparison analysis\
				on session {} before running more detailed analyses :)".format(id))
			return redirect(url_for('compare.analysis_menu',id=id))
	print(session_dict)
	return render_template(
		'compare/batch_compare_field_set.html',
		title="Compare batches by {} fields".format(field_set),
		session_dict=session_dict,
		field_set=field_set,
		field_set_label="Added author",
		field_set_count="added_author_field_count",
		id=id
		)

@compare.route('/record_compare/<records>_<session_id>', methods=['GET','POST'])
@login_required
def record_compare(records,session_id):
	"""
	Render the record comparison template on the /record_compare route
	this is a comparison of two records that match on OCLC number from a session
	"""
	# print("& & "*200)
	# print(row)
	records = ast.literal_eval(records)
	print(records)
	# record_ids = row
	# row_id = row['row']
	compare_dict = record_analysis.compare_records(records)

	return render_template(
		'compare/record_compare.html',
		title="Compare records",
		# session_timestamp=session_timestamp,
		session_id=session_id,
		# id=row_id,
		compare_dict=compare_dict
		)
