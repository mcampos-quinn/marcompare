import os

from flask import current_app

from app import db
from . models import Session, Batch

def clean_temp_folder():
	temp_folder = current_app.config['UPLOAD_FOLDER']
	for item in os.listdir(temp_folder):
		if not item.startswith('.'):
			os.remove(
				os.path.join(temp_folder,item)
			)

def get_session_timestamp(session_id):
	timestamp = Session.query.get(session_id).started_timestamp.strftime("%Y-%m-%d, %H:%M:%S")

	return timestamp

def get_session_batches(current_session_id):
	comparison_dict = {}
	comparison_dict['batches'] = {}
	session_timestamp = get_session_timestamp(current_session_id)
	comparison_dict['session timestamp'] = session_timestamp
	my_batches = Batch.query.filter_by(session_id=current_session_id).all()
	batch_ids = [str(batch.id) for batch in my_batches]

	return comparison_dict, my_batches, batch_ids
