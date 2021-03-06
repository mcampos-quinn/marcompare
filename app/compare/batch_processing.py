import itertools
import json
import os
import re
import time

from flask import current_app
from sqlalchemy import create_engine, text, update, and_
from sqlalchemy import Column, Integer, Text, MetaData, Table
from sqlalchemy.sql import select, insert

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
	batch_1_identifier_field = request.form['batch_1_identifier_field']
	try:
		if request.form['batch_1_namespaces']:
			batch_1_namespaces = True
	except:
		batch_1_namespaces = False

	batch_2 =  request.files.getlist('batch_2')[0]
	batch_2_path = os.path.join(
		current_app.config['UPLOAD_FOLDER'],
		batch_2.filename
		)
	batch_2_source = request.form['batch_2_source']
	batch_2_identifier_field = request.form['batch_2_identifier_field']
	try:
		if request.form['batch_2_namespaces']:
			batch_2_namespaces = True
	except:
		batch_2_namespaces = False

	batch_1.save(batch_1_path)
	batch_2.save(batch_2_path)
	# if batch_3:
	# 	batch_3.save(os.path.join(current_app.config['UPLOAD_FOLDER'],batch_3.filename))
		# return redirect(url_for('index'))
	batch_1_record = Batch(
		filepath=batch_1_path,
		source=batch_1_source,
		namespaces=batch_1_namespaces,
		identifier_field=batch_1_identifier_field,
		session_id=session_id
		)
	batch_2_record = Batch(
		filepath=batch_2_path,
		source=batch_2_source,
		namespaces=batch_2_namespaces,
		identifier_field=batch_2_identifier_field,
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
		parse_json(
			batch.id,
			batch.filepath,
			batch.identifier_field,
			batch.namespaces
			)

def parse_json(
	batch_id,
	batch_filepath,
	identifier_field,
	namespaces,
	oclc_number=None
	):
	# Go thru the batch's JSON and make entries in the db for all
	# the records and each field
	if namespaces:
		prefix = "marc:"
	else:
		prefix = ""
	if oclc_number:
		# i.e. if this is a batch of 1 record from oclc
		the_oclc_number = oclc_number
	hookup = DB_Hookup()
	print("&& & &"*300)
	print(batch_filepath)
	# print(prefix)
	with open(batch_filepath,'r') as f:
		data = json.load(f)
		print(data)
		db_records = []
		with hookup.engine.connect() as connection:
			if isinstance(data[prefix+'collection'][prefix+'record'],dict):
				record_dict = parse_record(
					data[prefix+'collection'][prefix+'record'],
					prefix,
					batch_id,
					identifier_field
				)
				db_records.append(record_dict)

			elif isinstance(data[prefix+'collection'][prefix+'record'],list):
				for record in data[prefix+'collection'][prefix+'record']:
					record_dict = parse_record(
						record,
						prefix,
						batch_id,
						identifier_field
					)
					db_records.append(record_dict)
					del record

			# Take out the field list from each record temporarily so we
			# can insert the records themselves in bulk to the DB (saves A LOT
			# of processing overhead)
			db_records_temp = []
			for record in db_records:
				db_records_temp.append(
					{k:v for k,v in record.items() if not isinstance(v,list)}
				)

			records_table = hookup.metadata.tables['records']

			# limit the list of record dicts to 999 at a time
			record_chunker = chunker(db_records_temp,999)
			for chunk in record_chunker:
				insert_records = records_table.insert().values(
					[x for x in chunk if x]
					)
				connection.execute(insert_records)
			# Go back and retrieve all the record ids in a new dict
			# Have to do it this way since the bulk INSERT operation
			# above doesn't return primary keys from the db
			if batch_id != 0:
				select_records = select(
					(records_table.c.id,records_table.c.raw_record)
					).where(records_table.c.batch_id == batch_id)
			else:
				# if it's just a single record from OCLC
				select_records = select(
					(records_table.c.id,records_table.c.raw_record)
					).where(
						and_(
							records_table.c.oclc_number == the_oclc_number,
							records_table.c.from_oclc == True
							)
						)
			result = connection.execute(select_records)
			record_ids_temp = {}
			for row in result:
				# print(row)
				record_ids_temp[row.raw_record] = row.id
			# Now go back and add the record ids to each entry in the original
			# db_records dict so we can add the record id to each field dict
			# print("# ^# "*100)
			fields = []
			for record in db_records:
				record['record_id'] = None
				record['record_id'] = record_ids_temp[record['raw_record']]
				# print(record['record_id'])
				for tag_dict in record['fields']:
					tag_dict['record_id'] = record['record_id']
					fields.append(tag_dict)

			fields_table = hookup.metadata.tables['fields']

			# limit the list of field dicts to chunks of 999 at a time
			field_chunker = chunker(fields,999)
			for chunk in field_chunker:
				insert_fields = fields_table.insert().values(
					[x for x in chunk if x]
					)
				connection.execute(insert_fields)

def chunker(iterable, n, fillvalue=None):
	# This function will output a designated number of chunks from an
	# iterable of arbitrary size. I need it to get around the SQLite3
	# limitation of 999 variables per insert transaction. With more than a few
	# bib records the number of fields can easily go way past that.
	# taken from https://codereview.stackexchange.com/questions/161889/iterate-through-python-iterable-in-chunk-of-n
    yield from itertools.zip_longest(*[iter(iterable)] * n, fillvalue=fillvalue)

def parse_record(record,prefix,batch_id,identifier_field):
	print("XX XX")
	print(record)
	record_dict = {}
	record_dict['fields'] = []
	if not batch_id:
		record_dict['from_oclc'] = True
	record_dict['batch_id'] = batch_id
	record_dict['oclc_number'] = None
	record_dict['title'] = None
	# record_dict['record_id'] = None # we'll get this id later
	record_dict['raw_record'] = str(record)
	# get the count of data fields
	record_dict['field_count'] = len(record[prefix+'datafield'])
	# get 1xx count
	record_dict['author_field_count'] = len(
		[x for x in record[prefix+'datafield'] if x['@tag'].startswith('1')]
		)
	# get 2xx count
	record_dict['title_field_count'] = len(
		[x for x in record[prefix+'datafield'] if x['@tag'].startswith('2')]
		)
	# get 3xx count
	record_dict['physical_field_count'] = len(
		[x for x in record[prefix+'datafield'] if x['@tag'].startswith('3')]
		)
	# get 5xx count
	record_dict['note_field_count'] = len(
		[x for x in record[prefix+'datafield'] if x['@tag'].startswith('5')]
		)
	# get 6xx count
	record_dict['subject_field_count'] = len(
		[x for x in record[prefix+'datafield'] if x['@tag'].startswith('6')]
		)
	# get 7xx count
	record_dict['added_author_field_count'] = len(
		[x for x in record[prefix+'datafield'] if x['@tag'].startswith('7')]
		)
	# get 856 count
	record_dict['link_field_count'] = len(
		[x for x in record[prefix+'datafield'] if x['@tag'] == '856']
		)
	# Loop thru all the control fields and grab data
	if isinstance(record[prefix+'controlfield'],list):
		for control_tag in record[prefix+'controlfield']:
			tag_dict = {}
			tag_dict['tag'] = control_tag['@tag']
			tag_dict['indicator_1'] = None
			tag_dict['indicator_2'] = None
			tag_dict['text'] =  control_tag['#text'].lstrip('0')

			record_dict['fields'].append(tag_dict)
			# Now look for an OCLC number
			if identifier_field == '001':
				if control_tag['@tag'] == '001':
					record_dict['oclc_number'] = re.sub(r"\D", "", control_tag['#text']).lstrip('0')
	elif isinstance(record[prefix+'controlfield'],dict):
		tag_dict = {}
		tag_dict['tag'] = record[prefix+'controlfield']['@tag']
		tag_dict['indicator_1'] = None
		tag_dict['indicator_2'] = None
		tag_dict['text'] =  record[prefix+'controlfield']['#text'].lstrip('0')
		record_dict['fields'].append(tag_dict)
		# Now look for an OCLC number
		if identifier_field == '001':
			if control_tag['@tag'] == '001':
				record_dict['oclc_number'] = re.sub(r"\D", "", record[prefix+'controlfield']['#text']).lstrip('0')

	# Loop thru all the data fields and grab data
	for data_tag in record[prefix+'datafield']:
		tag_dict = {}
		tag_dict['tag'] = data_tag['@tag']
		tag_dict['indicator_1'] = data_tag['@ind1']
		tag_dict['indicator_2'] = data_tag['@ind2']
		tag_dict['text'] =  parse_subfields(data_tag[prefix+'subfield'])

		record_dict['fields'].append(tag_dict)
		# Now look for an OCLC number
		if identifier_field == '035':
			if data_tag['@tag'] == '035':
				oclc_number = None
				if isinstance(data_tag[prefix+'subfield'],list):
					for sf in data_tag[prefix+'subfield']:
						if sf['@code'] == 'a' and 'OCoLC' in sf['#text']:
							record_dict['oclc_number'] = re.sub(r"\D", "", sf['#text']).lstrip('0')
				elif isinstance(data_tag[prefix+'subfield'],dict):
					if data_tag[prefix+'subfield']['@code'] == 'a' \
						and 'OCoLC' in data_tag[prefix+'subfield']['#text']:
						record_dict['oclc_number'] = re.sub(r"\D", "", data_tag[prefix+'subfield']['#text']).lstrip('0')

		# look for a 245 to be "title"
		if data_tag['@tag'] == '245':
			title = None
			if isinstance(data_tag[prefix+'subfield'],list):
				title = ' '.join([sf['#text'] for sf in data_tag[prefix+'subfield']])
				record_dict['title'] = title
			elif isinstance(data_tag[prefix+'subfield'],dict):
				record_dict['title'] = data_tag[prefix+'subfield']['#text']

	return record_dict

def parse_subfields(_subfield):
	_list = []
	if isinstance(_subfield,list):
		for subfield_dict in _subfield:
			_list.append(
				"${} ;".format(" ".join(x for x in subfield_dict.values()))
				)
	elif isinstance(_subfield,dict):
		_list.append(
			"${} ;".format(" ".join(x for x in _subfield.values()))
			)
	return " ".join(_list)
