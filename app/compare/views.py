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

		flash('You have successfully deleted the session.')
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
	list the different analyses you can do an a session
	"""
	return render_template(
		'compare/analysis_menu.html',
		title="Analysis Menu",
		id=id
		)

@compare.route('/batch_compare/session_<int:id>', methods=['GET','POST'])
@login_required
def batch_compare(id):
	"""
	Render the batch comparison template on the /batch_compare route
	this is an overal comparison of two record batches from a session
	"""

	session_dict = analysis.compare_batches(id)
	return render_template(
		'compare/batch_compare.html',
		title="Compare batches",
		session_dict=session_dict
		)
