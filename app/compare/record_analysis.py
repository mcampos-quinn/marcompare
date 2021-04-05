import json
import os
import re
import time

from collections import Counter

from flask import current_app
from sqlalchemy import create_engine, text, func, and_, or_, bindparam
from sqlalchemy.sql import insert, select, update

import app
from .. import db
from .. models import Session, Batch, Record, Field
from .. app_utils import get_session_timestamp, get_session_batches

from .db_handling import DB_Hookup

def compare_records(row_dict):
	# this is the row_dict that gets passed:
	# {'row': 27,
	# 'session_timestamp':1235,
	# 'records': [
	# 	{'id': 503, 'data': {'batch_id': '15', 'color': None, 'subject_field_count': 3, 'oclc_match_id': 537}},
	# 	{'id': 537, 'data': {'batch_id': '16', 'color': None, 'subject_field_count': 3, 'oclc_match_id': 503}}
	# 	]
	# }
	hookup = DB_Hookup()

	get_fields_sql = '''
	fields.record_id=:record_id
	'''
	# batch_source_sql = '''
	# INNER JOIN records
	# ON batches.id=:record_id;
	# '''
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
		for record in row_dict['records']:
			# first grab the basic info for the records in the comparison
			print(record)
			record_dict = {'record':record['id'],'column':None,'data':{}}
			source = Batch.query.get(int(record['data']['batch_id'])).source
			print(source)
			record_dict['record'] = record['id']
			record_dict['column'] = row_dict['records'].index(record)
			record_dict['data']['batch_source'] = source
			record_dict['data']['title'] = record['data']['title']

			compare_dict['records'].append(record_dict)

			s = fields_table.select().where(
				fields_table.c.record_id==record['id'])
			fields = connection.execute(s).fetchall()
			# print(fields)

			for field in fields:
				field_dict = {
					'field_id':field.id,
					'color': None,
					'column':record_dict['column'],
					 'data':{
					 	'record_id':record['id'],
						'tag':field.tag,
						'ind1':field.indicator_1,
						'ind2':field.indicator_2,
						'text':field.text
						}
					}
				fields_list.append(
					field_dict
				)
				del field
			del fields

	# now do the field matching
	matched_fields = []
	num_records = len(row_dict['records'])
	rows = []
	for field in fields_list:
		if not str(field) in matched_fields:
		# check that the field hasn't already been matched
			row = {
				'row':'',
				'fields':[None for i in range(num_records)]
			}

			matched_tags = [
				f for f in fields_list \
				if f['column'] != field['column'] and \
				f['data']['tag'] == field['data']['tag'] and not \
				str(f) in matched_fields
			]
			if matched_tags != []:
				for f in matched_tags:
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
				other_column = [
					x for x in range(num_records) \
					if not x == field['column']
					][0]
				field['color'] = 'green'
				row['fields'][field['column']] = field
				row['fields'][other_column] = empty_field
				row['fields'][other_column]['column'] = other_column
				matched_fields.append(str(field))

			# row['row'] is a string that we use to sort the rows
			# by matched field pairs
			row['row'] = ''.join([x['data']['tag'] for x in row['fields']])
			print(row['row'])
			rows.append(row)

	compare_dict['rows'] = rows

	# sort the rows by field tag pairs
	compare_dict['rows'].sort(key=lambda x: x['row'])

	# print(compare_dict)
	return compare_dict
