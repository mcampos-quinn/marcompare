import json
import os
import re

from flask import current_app

from .. import db
from .. models import Session, Batch, Record, Field
from .. import app_utils

def compare_batches(session_id):
	comparison_dict = {}
	my_batches = Batch.query.filter_by(session_id=my_session_id).all()
	record_tally_sql = '''
	SELECT COUNT(records.id)
	FROM records
	WHERE records.batch_id=:batch;
	'''
	get_batch_records_sql = '''
	SELECT records.id
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
		comparison_dict[_batch.id] = {}
		comparison_dict[_batch.id]['no oclc match'] = 0
		comparison_dict[_batch.id]['records w more fields'] = 0
		comparison_dict[_batch.id]['record count'] = db.session.execute(
			record_tally_sql,
			{'batch': _batch.id}
			).first()[0]
		batch_records = db.session.execute(
			get_batch_records_sql,
			{'batch': _batch.id}
			).fetchall()
		for record in batch_records:
			match = db.session.execute(
					find_oclc_match_sql,
					{
						'record_a_oclc':record.oclc_number,
						'record_a_batch':record.batch_id
					}
				).first()
			if match:
				record
