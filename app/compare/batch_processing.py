import json
import os
import re

from flask import current_app
from sqlalchemy import create_engine, text, update
from sqlalchemy import Column, Integer, Text, MetaData, Table

from .db_handling import DB_Hookup

from .. import db
from .. models import Session, Batch, Record, Field
from .. import app_utils

def create_session(user_id):
	new_session = Session(user_id=user_id)
	db.session.add(new_session)
	db.session.commit()
	db.session.refresh(new_session)

	return new_session.id

def process_batches(session_id,request):
	batch_1 = request.files.getlist('batch_1')[0]
	batch_1_path = os.path.join(
		current_app.config['UPLOAD_FOLDER'],
		batch_1.filename
		)
	batch_1_source = request.form['batch_1_source']
	batch_2 =  request.files.getlist('batch_2')[0]
	batch_2_path = os.path.join(
		current_app.config['UPLOAD_FOLDER'],
		batch_2.filename
		)
	batch_2_source = request.form['batch_2_source']
	batch_1.save(batch_1_path)
	batch_2.save(batch_1_path)
	# if batch_3:
	# 	batch_3.save(os.path.join(current_app.config['UPLOAD_FOLDER'],batch_3.filename))
		# return redirect(url_for('index'))
	batch_1_record = Batch(
		filepath=batch_1_path,
		source=batch_1_source,
		session_id=session_id
		)
	batch_2_record = Batch(
		filepath=batch_2_path,
		source=batch_2_source,
		session_id=session_id
		)
	db.session.add(batch_1_record)
	db.session.add(batch_2_record)
	db.session.commit()

def read_files(my_session_id):
	the_session = Session.query.get(my_session_id)
	my_batches = Batch.query.filter_by(session_id=my_session_id).all()
	# print("RUBY "*100)
	for batch in my_batches:
		parse_json(batch.id,batch.filepath)

def parse_json(batch_id,batch_filepath):
	hookup = DB_Hookup()
	with open(batch_filepath,'r') as f:
		data = json.load(f)
		with hookup.engine.connect() as connection:
			for record in data['collection']['record']:
				insert_record = hookup.metadata.tables['records'].insert().values(
					{'batch_id':batch_id}
				)
				result = connection.execute(insert_record)
				record_id = result.inserted_primary_key[0]

				for data_tag in record['datafield']:
					_tag = data_tag['@tag']
					_ind1 = data_tag['@ind1']
					_ind2 = data_tag['@ind2']
					field_content =  parse_subfields(data_tag['subfield'])
					insert_field = hookup.metadata.tables['fields'].insert().values(
						{
							'tag':_tag,
							'indicator_1':_ind1,
							'indicator_2':_ind2,
							'text':field_content,
							'record_id':record_id
						}
					)
					connection.execute(insert_field)

					# _field = Field(
					# 	tag=_tag,
					# 	indicator_1=_ind1,
					# 	indicator_2=_ind2,
					# 	text=field_content,
					# 	record_id = record_id
					# )
					# db.session.add(_field)
					if data_tag['@tag'] == '035':
						oclc_number = None
						if isinstance(data_tag['subfield'],list):
							for sf in data_tag['subfield']:
								if sf['@code'] == 'a' and 'OCoLC' in sf['#text']:
									oclc_number = re.sub(r"\D", "", sf['#text']).lstrip('0')
						elif isinstance(data_tag['subfield'],dict):
							if data_tag['subfield']['@code'] == 'a' \
								and 'OCoLC' in data_tag['subfield']['#text']:
								# print(tag['subfield']['#text'])
								oclc_number = re.sub(r"\D", "", data_tag['subfield']['#text']).lstrip('0')

						if oclc_number:
							update_oclc_number = hookup.metadata.tables['records'].update().values(
								{'oclc_number':oclc_number}
							)
							connection.execute(update_oclc_number)

				db.session.commit()

def parse_subfields(_subfield):
	_list = []
	if isinstance(_subfield,list):
		for subfield_dict in _subfield:
			for code,text in subfield_dict.items():
				_list.append("${} {}; ".format(code,text))
	elif isinstance(_subfield,dict):
		for code,text in _subfield.items():
			_list.append("${} {}; ".format(code,text))
	return "".join(_list)
