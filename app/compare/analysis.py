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
from .. app_utils import get_session_timestamp, get_session_batches

from .db_handling import DB_Hookup



def compare_batches(current_session_id):
	# Analysis of overall difference between record batches
	hookup = DB_Hookup()

	comparison_dict, my_batches, batch_ids = get_session_batches(current_session_id)
	comparison_dict['batches'] = []
	match_query_sql = '''
	records.oclc_number=:record_a_oclc
	AND records.id!=:record_a_id
	AND records.batch_id IN :batch_ids
	'''
	with hookup.engine.connect() as connection:
		records_table = hookup.metadata.tables['records']
		batches_table = hookup.metadata.tables['batches']
		for _batch in my_batches:
			# print("* * * "*500)
			the_other_batch = [x for x in my_batches if x != _batch][0]

			this_batch_more_fields = 0
			other_batch_more_fields = 0

			this_batch_no_oclc_matches = 0
			other_batch_no_oclc_matches = 0

			# Add the total record tallies to each batch object
			this_batch_records = Record.query.filter_by(batch_id=_batch.id).all()
			this_batch_records_tally = len(this_batch_records)
			other_batch_records = Record.query.filter_by(batch_id=the_other_batch.id).all()
			other_batch_records_tally = len(other_batch_records)

			if not _batch.records_tally:
				_batch.records_tally = this_batch_records_tally
				the_other_batch.records_tally = other_batch_records_tally
				db.session.commit()

			for a_record in this_batch_records:
				# only do the query if there isn't already a match from another pass
				if a_record.oclc_number and not a_record.oclc_match_id:
					t = text(match_query_sql).bindparams(
						bindparam('batch_ids',expanding=True)
					)
					s = records_table.select(t)
					match_result = connection.execute(
							s,
							{'record_a_oclc':a_record.oclc_number,
							'batch_ids':batch_ids,
							'record_a_id':a_record.id}
						)
					match = match_result.fetchall()
					# print("this many oclc matches for the record "+str(len(match)))
					if not match == []:
						match_record = match[0]
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

						record_field_count = a_record.field_count
						match_field_count = match_record.field_count
						# fixme this logic is stupid
						if record_field_count > match_field_count:
							this_batch_more_fields += 1
						elif match_field_count > record_field_count:
							other_batch_more_fields += 1
						# u = update(batches_table)
						# u = u.values(
						# 		{"records_w_more_fields": this_batch_more_fields}
						# 	).where(
						# 		batches_table.c.id == _batch.id
						# 	)
						# connection.execute(u)
						# u = update(batches_table)
						# u = u.values(
						# 		{"records_w_more_fields": other_batch_more_fields}
						# 	).where(
						# 		batches_table.c.id == the_other_batch.id
						# 	)
						# connection.execute(u)
					else:
						this_batch_no_oclc_matches += 1
						# print("found a no oclc match on batch "+str(_batch.id))
				elif a_record.oclc_match_id:
					# print("^ ^ "*100)
					# print(a_record.oclc_match_id)
					# match_record = Record.query.get(a_record.oclc_match_id).fetchall()[0]
					# match_field_count = match_record.field_count

					# a = time.time()
					s = records_table.select(
						records_table.c.field_count
						).where(records_table.c.id==a_record.oclc_match_id)
					# s = records_table.select(
					# 	records_table.c.field_count
					# 	).where(records_table.c.id==a_record.oclc_match_id)
					result = connection.execute(s)
					# b = time.time()
					# print("select based on match id: "+str(b-a))
					record_field_count = a_record.field_count
					# match_field_count = match.field_count
					match_field_count = result.first()[0]
					# print(match_field_count)

					# do the comparison
					if record_field_count > match_field_count:
						this_batch_more_fields += 1
					elif match_field_count > record_field_count:
						other_batch_more_fields += 1
				else:
					this_batch_no_oclc_matches += 1
					# print("found a no oclc match on batch "+str(_batch.id))

			if not _batch.records_w_more_fields:
				_batch.records_w_more_fields = this_batch_more_fields
				the_other_batch.records_w_more_fields = other_batch_more_fields
				db.session.commit()

			if not _batch.records_w_no_oclc_match:
				_batch.records_w_no_oclc_match = this_batch_no_oclc_matches
				the_other_batch.records_w_no_oclc_match = other_batch_no_oclc_matches
				db.session.commit()

			# comparison_dict['batches'].append(batch_dict)

		# parse the batches into a dict for comparison
		for _batch in my_batches:
			batch_dict = {}
			# comparison_dict[_batch.id] = {}
			batch_dict['source'] = _batch.source
			batch_dict['records tally'] = _batch.records_tally
			batch_dict['records w more fields'] = _batch.records_w_more_fields
			batch_dict['no oclc match'] = _batch.records_w_no_oclc_match
			comparison_dict['batches'].append(batch_dict)
		# print(comparison_dict)
		_session = Session.query.get(current_session_id)
		_session.overall_batch_comparison_dict = str(comparison_dict)
		db.session.commit()
		return comparison_dict

def batch_compare_subjects(current_session_id):
	hookup = DB_Hookup()

	get_title_sql = '''

	'''

	comparison_dict, my_batches, batch_ids = get_session_batches(current_session_id)
	# print(comparison_dict)
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
				# print(row.oclc_match_id)
				# print(row.id)
				record_dict = {}
				record_dict['id'] = row.id
				record_dict['batch_id'] = str(row.batch_id) # this is a string in the batch_ids list
				# record_dict['batch_source'] = str(row.batch_source)
				record_dict['color'] = None
				record_dict['oclc_match'] = row.oclc_match_id
				# print('oclc match from subj '+str(record_dict['oclc_match']))
				record_dict['subject_field_count'] = row.subject_field_count
				# comparison_dict['batches'][row.batch_id]['records'].append(
				# 	record_dict
				# )
				records.append(record_dict)
			del row
		print(records)

		for _record in records:
			if not _record['color']:
				oclc_match = [
					x for x in records if x['oclc_match'] == _record['id']
					]
				if not oclc_match == []:
					print(oclc_match)
					oclc_match = oclc_match[0]
					if oclc_match['subject_field_count'] > _record["subject_field_count"]:
						_record['color'] = 'red'
						oclc_match['color'] = 'green'
					elif oclc_match['subject_field_count'] < _record["subject_field_count"]:
						_record['color'] = 'green'
						oclc_match['color'] = 'red'
	session_timestamp = get_session_timestamp(current_session_id)
	compare = {
		'batches':[x.id for x in my_batches],
		'session_timestamp': session_timestamp,
		'session_timestamp_int': re.sub(r"\D", "", session_timestamp),
		'rows':[{'row':0,'records':[]}]}
	row_counter = 1
	matched_records = []
	for _record in records:
		if not _record in matched_records:
			row = {
				'row':row_counter,
				'records':[]
			}
			row_record = build_field_comparison_dict(_record,'subject_field_count')
			row['records'].append(row_record)
			_match = [item for item in records if item['oclc_match'] == _record['id']]
			for item in _match:
				i = build_field_comparison_dict(item,'subject_field_count')
				row['records'].append(i)
				matched_records.append(item)

			row['records'].sort(key= lambda x : x['data']['batch_id'])
			matched_records.append(_record)
			compare['rows'].append(row)
			row_counter += 1

	# print(compare)
	_session = Session.query.get(current_session_id)
	_session.subject_batch_comparison_dict = str(compare)
	db.session.commit()
	return compare

def compare_records(row_dict):
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
		'records':[]
		}
	with hookup.engine.connect() as connection:
		fields_table = hookup.metadata.tables['fields']
		batches_table = hookup.metadata.tables['batches']
		for record in row_dict['records']:
			print(record)
			record_dict = {"record" : record['id'], 'fields':[]}
			source = Batch.query.get(int(record['data']['batch_id'])).source
			record_dict['batch_source'] = source

			s = fields_table.select().where(
				fields_table.c.record_id==record['id'])
			fields = connection.execute(s).fetchall()

			for field in fields:
				field_dict = {
					field.id : {
						'tag':field.tag,
						'ind1':field.indicator_1,
						'ind2':field.indicator_2,
						'text':field.text
						}
					}
				record_dict['fields'].append(
					field_dict
				)
			compare_dict['records'].append(record_dict)

	print(compare_dict)
	return compare_dict

def build_field_comparison_dict(record,field_set_count):
	# field_set_count should be e.g. record['subject_field_count']
	record_dict = {
			'id':record['id'],
			'data':{
				'batch_id':record['batch_id'],
				'color':record['color'],
				'subject_field_count':record[field_set_count],
				'oclc_match_id':record['oclc_match']
			}
		}
	return record_dict

def get_count(connection,table,column,filter_value):
	# from https://gist.github.com/hest/8798884
	count_q = connection.query(table).filter(
		column == filter_value
		).statement.with_only_columns(
			[func.count(table.id)]
			).order_by(None)

	count = connection.execute(count_q).scalar()
	return count
