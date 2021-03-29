import json
import os
import re

from flask import current_app
from sqlalchemy import create_engine, text, func

import app
from .. import db
from .. models import Session, Batch, Record, Field
from .. app_utils import get_session_timestamp

def compare_batches(session_id):
	engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'])
	comparison_dict = {'batches':[]}
	session_timestamp = get_session_timestamp(session_id)
	comparison_dict['session timestamp'] = session_timestamp
	my_batches = Batch.query.filter_by(session_id=session_id).all()
	batch_ids = [str(batch.id) for batch in my_batches]
	# print(" i "*100)
	# print(my_batches)

	record_tally_sql = '''
	SELECT COUNT(records.id)
	FROM records
	WHERE records.batch_id=:batch;
	'''
	get_batch_records_sql = '''
	SELECT records.id,records.batch_id,records.oclc_number
	FROM records
	WHERE records.batch_id=:batch;
	'''
	find_oclc_match_sql = '''
	SELECT records.id
	FROM records
	WHERE records.oclc_number=:record_a_oclc
	AND records.batch_id=:record_b_batch;
	'''
	match_query_sql = '''
	SELECT records.id
	FROM records
	WHERE records.oclc_number=:record_a_oclc
	AND records.batch_id IN (:batch_ids)
	AND records.batch_id!=:record_a_batch;
	'''

	get_field_count_sql = '''
	SELECT COUNT(fields.id)
	FROM fields
	WHERE fields.record_id=:record_id;
	'''
	with engine.connect() as connection:
		for _batch in my_batches:
			batch_dict = {}
			batch_dict['source'] = _batch.source
			batch_dict['no oclc match'] = 0
			batch_dict['records w more fields'] = 0
			# batch_dict['record count'] = get_count(Record,Record.batch_id,_batch.id)
			# batch_dict['record count'] = connection.execute(
			# 		text(record_tally_sql),
			# 		{'batch': _batch.id}
			# 	).first()[0]
			batch_records = db.session.query(Record).filter_by(batch_id=_batch.id).all()
			batch_dict['record count'] = len(batch_records)
			# batch_records = connection.execute(
			# 	text(get_batch_records_sql),
			# 	{'batch': _batch.id}
			# 	).fetchall()

			# print('o '*100)
			# print(batch_records)
			for a_record in batch_records:
				# print(type(record))
				if a_record.oclc_number:
					# match_query = connection.query(Record).filter(
					# 	Record.batch_id!=_batch.id,
					# 	Record.batch_id.in_(batch_ids),
					# 	Record.oclc_number==a_record.oclc_number
					# ).with_entities(Record.id)
					match = connection.execute(
						text(match_query_sql),
						{
							'record_a_oclc':a_record.oclc_number,
							'batch_ids':",".join(batch_ids),
							'record_a_batch':a_record.batch_id
						}
					)
					# match = connection.execute(
					# 		text(find_oclc_match_sql),
					# 		{
					# 			'record_a_oclc':record.oclc_number,
					# 			'record_a_batch':record.batch_id
					# 		}
					# 	).first()
					if match.fetchall() != []:
						# print(match.fetchall())
						match_id = match.first()[0]
						print(match_id)
						# record_field_count = get_count(
						# 	Field,
						# 	Field.record_id,
						# 	a_record.id
						# )
						record_field_count = connection.execute(
								text(get_field_count_sql),
								{
									'record_id':a_record.id
								}
							).first()[0]
						print(record_field_count)
						# match_field_count = get_count(
						# 	Field,
						# 	Field.record_id,
						# 	match_id
						# )
						match_field_count = connection.execute(
								text(get_field_count_sql),
								{
									'record_id':match_id
								}
							).first()[0]
						print(match_field_count)
						if record_field_count > match_field_count:
							batch_dict['records w more fields'] += 1
					else:
						batch_dict['no oclc match'] += 1
				else:
					batch_dict['no oclc match'] += 1
			comparison_dict['batches'].append(batch_dict)
		print(comparison_dict)
		_session = Session.query.get(session_id)
		_session.overall_batch_comparison_dict = str(comparison_dict)
		db.session.commit()
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
