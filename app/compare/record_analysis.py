import json
import os
import re
import subprocess
import time

from collections import Counter

from flask import current_app
from sqlalchemy import create_engine, text, func, and_, or_, bindparam
from sqlalchemy.sql import insert, select, update

import app
from .. import db
from .. models import Session, Batch, Record, Field
from .. import app_utils
from .. app_utils import get_session_timestamp, get_session_batches

from .db_handling import DB_Hookup
from .batch_processing import parse_json

def compare_records(record_id_list,oclc=None):
	hookup = DB_Hookup()
	oclc_number = None
	get_fields_sql = '''
	fields.record_id=:record_id
	'''
	compare_dict = {
		'records': [
 			{'record':None,
			'column':None,
			'data': {
	 			'batch_source':'SOURCE',
	 			'title':"TITLE"
				}
 			}
 		],
		'rows': [
			{'row': None,
			'fields': [
				{'field_id': None,
				'color': None,
				'column':None,
				'data': {
					'record_id': None,
					'tag': None,
					'ind1': '',
					'ind2': '',
					'text': None
					}
					}
				]
			}
		]
	}
	empty_field = {
		'field_id': '',
		'color': 'red',
		'column': None,
		'data': {
			'record_id': '',
			'tag': '',
			'ind1': '',
			'ind2': '',
			'text': ''
			}
	}
	with hookup.engine.connect() as connection:
		fields_table = hookup.metadata.tables['fields']
		batches_table = hookup.metadata.tables['batches']

		fields_list = []
		for record in record_id_list:
			# first grab the basic info for the records in the comparison
			# print(record)
			the_record = Record.query.get(record)
			oclc_number = the_record.oclc_number
			record_dict = {'record':record,'column':None,'data':{}}
			if the_record.batch_id != 0:
				source = Batch.query.get(the_record.batch_id).source
			else:
				source = "OCLC"
			print(source)
			record_dict['record'] = the_record.id
			record_dict['column'] = record_id_list.index(record)
			record_dict['data']['batch_source'] = source
			record_dict['data']['title'] = the_record.title

			compare_dict['records'].append(record_dict)

			s = fields_table.select().where(
				fields_table.c.record_id==the_record.id
				)
			fields = connection.execute(s).fetchall()
			# print(fields)

			for field in fields:
				field_dict = {
					'field_id':field.id,
					'color': None,
					'column':record_dict['column'],
					 'data':{
					 	'record_id':the_record.id,
						'tag':field.tag,
						'ind1':field.indicator_1,
						'ind2':field.indicator_2,
						'text':field.text
						}
					}
				fields_list.append(
					field_dict
				)
				# del field
			# del fields

	# now do the field matching
	matched_fields = []
	num_records = len(record_id_list)
	if oclc:
		num_records = num_records + 1

	# print(fields_list)
	rows = []
	for field in fields_list:
		if not str(field) in matched_fields:
			# check that the field hasn't already been matched
			row = {
				'row':'',
				'fields':[None for i in range(num_records)]
			}

			matched_tags = [
				f for f in fields_list
				if f['column'] != field['column'] and
				f['data']['tag'] == field['data']['tag']
				# and not str(f) in matched_fields
			]
			if matched_tags != []:
				for f in matched_tags:
					print(f)
					# print(field)
					if not str(field) in matched_fields:
						if f['data']['text'] == field['data']['text']:
							row['fields'][f['column']] = f
							matched_fields.append(str(f))
							row['fields'][field['column']] = field
							matched_fields.append(str(field))
						else:
							f['color'] = 'yellow'
							field['color'] = 'yellow'
							row['fields'][f['column']] = f
							matched_fields.append(str(f))
							row['fields'][field['column']] = field
							matched_fields.append(str(field))

			if matched_tags == []:
				other_columns = [
					x for x in range(num_records)
					if not x == field['column']
					]
				print('*** ***')
				print(other_columns)
				print('*** ***')
				field['color'] = 'green'
				row['fields'][field['column']] = field
				for other_column in other_columns:
					row['fields'][other_column] = empty_field
					row['fields'][other_column]['column'] = other_column
					matched_fields.append(str(field))

			print(row)
			intermediate = row['fields']
			for x in row['fields']:
				if x == None:
					index = row['fields'].index(x)
					intermediate.pop(index)
					intermediate.insert(index,empty_field)
			row['fields'] = intermediate
			# row['row'] is a string that we use to sort the rows
			# by matched field pairs
			row['row'] = ''.join([x['data']['tag'] for x in row['fields']])
			# print(row['row'])
			rows.append(row)

	compare_dict['rows'] = rows

	# sort the rows by field tag pairs
	compare_dict['rows'].sort(key=lambda x: x['row'])

	# print(compare_dict)
	return compare_dict

def pull_oclc(oclc_number):
	# do a z39.50 query to get the current OCLC main record
	output = None
	marcedit_path = current_app.config['MARCEDIT_BINARY_PATH']
	oclc_z3950_auth = current_app.config['OCLC_Z3950_AUTH']
	# marcedit_path = current_app.config['MARCEDIT_BINARY_PATH']
	tmp_path = current_app.config['UPLOAD_FOLDER']
	yaz_commands_path = os.path.join(tmp_path,'yaz_commands.txt')
	yaz_oclc_record_marc_path = os.path.join(tmp_path,'yaz_oclc_record.mrc')
	yaz_oclc_record_xml_path = os.path.join(tmp_path,'yaz_oclc_record.xml')
	yaz_oclc_record_json_path = os.path.join(tmp_path,'yaz_oclc_record.json')
	yaz_commands_temp_path = yaz_commands_path.replace('yaz_commands','yaz_commands_temp')
	with open(yaz_commands_path,'r') as f:
		# store the original commands to return the file to its previous state
		yaz_command_original = f.read()
		# get the commands for yaz to query OCLC using the current oclc number
		yaz_command = yaz_command_original.format(oclc_z3950_auth,oclc_number)
	with open(yaz_commands_temp_path,'w') as f:
		f.write(yaz_command)
	command = [
		'yaz-client',
		'-f',os.path.join(tmp_path,'yaz_commands_temp.txt'),
		'-m',yaz_oclc_record_marc_path
		]
	yaz_output = subprocess.run(command,stdout=subprocess.PIPE)
	os.remove(yaz_commands_temp_path)

	if b"Search was a success" in yaz_output.stdout:
		# do an annoying back and forth w MARCEdit to get the record in
		# the correct XML/JSON formats
		to_xml_command = [
			marcedit_path,
			'-s',yaz_oclc_record_marc_path,
			'-d',yaz_oclc_record_xml_path,
			'-marcxml'
		]
		subprocess.run(to_xml_command)
		to_json_command = [
			marcedit_path,
			'-s',yaz_oclc_record_xml_path,
			'-d',yaz_oclc_record_json_path,
			'-xml2json'
		]
		subprocess.run(to_json_command)

		parse_json(
			0,
			os.path.join(tmp_path,'yaz_oclc_record.json'),
			'001',
			True,
			oclc_number=oclc_number
			)
		oclc_main_record = db.session.query(Record).filter(
			Record.from_oclc == True,
			Record.oclc_number == oclc_number
			).first()
		oclc_main_record_id = oclc_main_record.id
		matching_records = db.session.query(Record).filter(
			Record.oclc_number == oclc_number
		)
		for record in matching_records:
			record.oclc_main_record_id = oclc_main_record_id
		db.session.commit()

	else:
		# the search failed?
		outcome = False
	with open(yaz_oclc_record_xml_path,'w') as x, \
		open(yaz_oclc_record_json_path,'w') as j, \
		open(yaz_oclc_record_marc_path,'w') as m:
		m.truncate(0)
		j.truncate(0)
		x.truncate(0)

	return oclc_main_record_id
