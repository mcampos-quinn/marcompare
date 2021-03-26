import os

from flask import current_app

def clean_temp_folder():
	temp_folder = current_app.config['UPLOAD_FOLDER']
	for item in os.listdir(temp_folder):
		if not item.startswith('.'):
			os.remove(
				os.path.join(temp_folder,item)
			)
