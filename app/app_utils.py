import os

from flask import current_app

from app import db
from . models import Session

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
