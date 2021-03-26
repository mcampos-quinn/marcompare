import os

from flask import render_template, request, flash, url_for, redirect, current_app
from flask_login import login_required, current_user

from . import compare
from . forms import FileUploadForm

from .. import db
from .. models import Batch, Session

@compare.route('/start_session', methods=['GET','POST'])
# @login_required
def start_session():
	"""
	Render the file upload template on the /start_session route
	"""
	form = FileUploadForm()
	if form.validate_on_submit():
		print(" 11 "* 100)
		# print(type(request.files.getlist('batch_1')[0]))
		new_session = Session(user_id=current_user.id)
		db.session.add(new_session)
		db.session.commit()
		db.session.refresh(new_session)
		session_id = new_session.id
		print(session_id)

		batch_1 =  request.files.getlist('batch_1')[0]
		batch_1_path = os.path.join(
			current_app.config['UPLOAD_FOLDER'],
			batch_1.filename
			)
		batch_2 =  request.files.getlist('batch_2')[0]
		batch_2_path = os.path.join(
			current_app.config['UPLOAD_FOLDER'],
			batch_2.filename
			)
		# print(batch_1.filename)
		batch_1.save(batch_1_path)
		batch_2.save(batch_1_path)
		# if batch_3:
		# 	batch_3.save(os.path.join(current_app.config['UPLOAD_FOLDER'],batch_3.filename))
			# return redirect(url_for('index'))
		batch_1_record = Batch(filepath=batch_1_path)
		batch_2_record = Batch(filepath=batch_2_path)

	return render_template(
		'compare/start_session.html',
		title="Start comparing",
		form=form)
