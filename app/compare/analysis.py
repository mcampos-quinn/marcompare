import json
import os
import re

from flask import current_app

from .. import db
from .. models import Session, Batch, Record, Field
from .. import app_utils

def compare_batches(session_id):
	comparison_dict = {'batches':[]}
	session_timestamp = Session.query.get(session_id).started_timestamp.strftime("%Y-%m-%d, %H:%M:%S")
	comparison_dict['session timestamp'] = session_timestamp
	my_batches = Batch.query.filter_by(session_id=session_id).all()
	print(" i "*100)
	print(my_batches)

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
	AND records.batch_id=:record_a_batch;
	'''
	get_field_count_sql = '''
	SELECT COUNT(fields.id)
	FROM fields
	WHERE fields.record_id=:record_id;
	'''

	for _batch in my_batches:
		batch_dict = {}
		batch_dict['source'] = _batch.source
		batch_dict['no oclc match'] = 0
		batch_dict['records w more fields'] = 0
		batch_dict['record count'] = db.session.execute(
			record_tally_sql,
			{'batch': _batch.id}
			).first()[0]
		batch_records = db.session.execute(
			get_batch_records_sql,
			{'batch': _batch.id}
			).fetchall()
		# print('o '*100)
		# print(batch_records)
		for record in batch_records:
			# print(type(record))
			if record.oclc_number:
				match = db.session.execute(
						find_oclc_match_sql,
						{
							'record_a_oclc':record.oclc_number,
							'record_a_batch':record.batch_id
						}
					).first()
				if match:
					record_field_count = db.session.execute(
							get_field_count_sql,
							{
								'record_id':record.id
							}
						).first()[0]
					match_field_count = db.session.execute(
							get_field_count_sql,
							{
								'record_id':match.id
							}
						).first()[0]
					if record_field_count > match_field_count:
						batch_dict['records w more fields'] += 1
				else:
					batch_dict['no oclc match'] += 1
			else:
				batch_dict['no oclc match'] += 1
		comparison_dict['batches'].append(batch_dict)
	print(comparison_dict)
	return comparison_dict
