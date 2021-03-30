import json
import os
import re
import time

from flask import current_app
from sqlalchemy import create_engine, text, func, and_, or_, bindparam
from sqlalchemy.sql import insert, select, update

import app
from .. import db
from .. models import Session, Batch, Record, Field
from .. app_utils import get_session_timestamp

from .db_handling import DB_Hookup

def get_batches(current_session_id):
	comparison_dict = {'batches':[]}
	session_timestamp = get_session_timestamp(current_session_id)
	comparison_dict['session timestamp'] = session_timestamp
	my_batches = Batch.query.filter_by(session_id=current_session_id).all()
	batch_ids = [str(batch.id) for batch in my_batches]

	return comparison_dict, my_batches, batch_ids

def compare_batches(current_session_id):
	# Analysis of overall difference between record batches
	hookup = DB_Hookup()

	comparison_dict, my_batches, batch_ids = get_batches(current_session_id)

	match_query_sql = '''
	records.oclc_number=:record_a_oclc
	AND records.id!=:record_a_id
	'''

	with hookup.engine.connect() as connection:
		records_table = hookup.metadata.tables['records']
		batches_table = hookup.metadata.tables['batches']
		for _batch in my_batches:
			the_other_batch = [x for x in my_batches if x != _batch]
			batch_dict = {}
			batch_dict['no oclc match'] = 0
			# batch_dict['records w more fields'] = 0
			this_batch_more_fields = 0
			other_batch_more_fields = 0
			batch_dict['source'] = _batch.source
			batch_records = Record.query.filter_by(batch_id=_batch.id).all()
			batch_dict['record count'] = len(batch_records)

			for a_record in batch_records:
				# only do the query if there isn't already a match from another pass
				if a_record.oclc_number and not a_record.oclc_match_id:
					# print("oclc: "+a_record.oclc_number)
					# a = time.time()

					t = text(match_query_sql)
					s = records_table.select(t)
					# print(str(s))
					match_result = connection.execute(
							s,
							{'record_a_oclc':a_record.oclc_number,
							'record_a_id':a_record.id}
						)

					match = match_result.fetchall()
					# print("match? : "+str(match))
					# b = time.time()
					# print('select: '+str(b-a))

					if not match == []:
						match_record = match[0]
						# a = time.time()
						u = update(records_table)
						u = u.values(
								{"oclc_match_id": match_record.id}
							).where(
								records_table.c.id == a_record.id
							)
						connection.execute(u)
						u = update(records_table)
						u = u.values(
								{"oclc_match_id": a_record.id}
							).where(
								records_table.c.id == match_record.id
							)
						connection.execute(u)
						# b = time.time()
						# print("update : "+str(b-a))

						record_field_count = a_record.field_count
						match_field_count = match_record.field_count
						# fixme this logic is stupid
						if record_field_count > match_field_count:
							this_batch_more_fields += 1
						elif match_field_count > record_field_count:
							other_batch_more_fields += 1
						u = update(batches_table)
						u = u.values(
								{"records_w_more_fields": this_batch_more_fields}
							).where(
								batches_table.c.id == _batch.id
							)
						connection.execute(u)
						u = update(batches_table)
						u = u.values(
								{"records_w_more_fields": other_batch_more_fields}
							).where(
								batches_table.c.id == the_other_batch.id
							)
						connection.execute(u)
					else:
						batch_dict['no oclc match'] += 1
				elif a_record.oclc_match_id:
					record_field_count = a_record.field_count
					# a = time.time()
					s = records_table.select(
						records_table.c.field_count
						).where(records_table.c.id==a_record.oclc_match_id)
					result = connection.execute(s)
					# b = time.time()
					# print("select based on match id: "+str(b-a))
					match_field_count = result.first()[0]
				else:
					batch_dict['no oclc match'] += 1

			comparison_dict['batches'].append(batch_dict)

		# print(comparison_dict)
		_session = Session.query.get(current_session_id)
		_session.overall_batch_comparison_dict = str(comparison_dict)
		db.session.commit()
		return comparison_dict

def batch_compare_subjects(current_session_id):
	hookup = DB_Hookup()

	comparison_dict, my_batches, batch_ids = get_batches(current_session_id)
	comparison_dict['batches'] = {}
	for _batch in batch_ids:
		comparison_dict['batches'][_batch] = {}
		comparison_dict['batches'][_batch]['records'] = []

	with hookup.engine.connect() as connection:
		batch_records_sql = '''
		records.batch_id IN :batch_ids
		'''
		records_table = hookup.metadata.tables['records']
		t = text(batch_records_sql).bindparams(
			bindparam('batch_ids',expanding=True)
			)
		s = records_table.select(t)
		result = connection.execute(s,{'batch_ids':batch_ids})

		records = []
		for row in result:
			if row.oclc_match_id:
				print(row.oclc_match_id)
				print(row.id)
				record_dict = {}
				record_dict['id'] = row.id
				record_dict['batch_id'] = row.batch_id
				record_dict['color'] = None
				record_dict['oclc_match'] = row.oclc_match_id
				record_dict['subject_field_count'] = row.subject_field_count
				# comparison_dict['batches'][row.batch_id]['records'].append(
				# 	record_dict
				# )
				records.append(record_dict)
		print(type(records))
		for _record in records:
			if not _record['color']:
				oclc_match = [
					x for x in records if x['oclc_match'] == _record['id']
					]
				print(oclc_match)
				if oclc_match['subject_field_count'] > _record["subject_field_count"]:
					_record['color'] = 'red'
					oclc_match['color'] = 'green'
				elif oclc_match['subject_field_count'] < _record["subject_field_count"]:
					_record['color'] = 'green'
					oclc_match['color'] = 'red'
				comparison_dict['batches'][_record['batch_id']]['records'].append(
					_record
				)
	print(comparison_dict)
	return comparison_dict

def get_count(connection,table,column,filter_value):
	# from https://gist.github.com/hest/8798884
	count_q = connection.query(table).filter(
		column == filter_value
		).statement.with_only_columns(
			[func.count(table.id)]
			).order_by(None)

	count = connection.execute(count_q).scalar()
	return count
