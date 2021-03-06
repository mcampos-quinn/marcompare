import os
import sys

from flask import current_app

from app import db
from . models import Session, Batch, Record

def clean_temp_folder():
	temp_folder = current_app.config['UPLOAD_FOLDER']
	for item in os.listdir(temp_folder):
		if not item.startswith(('.','yaz')):
			os.remove(
				os.path.join(temp_folder,item)
			)

def get_system():
	if sys.platform.startswith("darwin"):
		return "mac"
	elif sys.platform.startswith("win"):
		return "windows"
	elif sys.platform.startswith("linux"):
		return "linux"
	else:
		return False

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

def get_record_oclc_number(record_id):
	oclc_number = Record.query.get(record_id).oclc_number

	return oclc_number

def check_oclc_main(record_id):
	has_oclc_main_already = Record.query.get(record_id).oclc_main_record_id

	return has_oclc_main_already
