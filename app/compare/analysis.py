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

def compare_batches(current_session_id):
	# Analysis of overall difference between record batches
	hookup = DB_Hookup()
	comparison_dict = {'batches':[]}
	session_timestamp = get_session_timestamp(current_session_id)
	comparison_dict['session timestamp'] = session_timestamp
	my_batches = Batch.query.filter_by(session_id=current_session_id).all()
	batch_ids = [str(batch.id) for batch in my_batches]

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

	match_query_sql = '''
	records.oclc_number=:record_a_oclc
	AND records.batch_id IN :batch_ids
	AND records.batch_id!=:record_a_batch;
	'''

	get_field_count_sql = '''
	SELECT COUNT(fields.id)
	FROM fields
	WHERE fields.record_id=:record_id;
	'''
	with hookup.engine.connect() as connection:
		records_table = hookup.metadata.tables['records']
		for _batch in my_batches:
			# the_other_batch = [x for x in ]
			batch_dict = {}
			batch_dict['no oclc match'] = 0
			batch_dict['records w more fields'] = 0
			batch_dict['source'] = _batch.source
			batch_records = Record.query.filter_by(batch_id=_batch.id).all()
			batch_dict['record count'] = len(batch_records)

			for a_record in batch_records:
				print("start of record in loop")
				print(a_record.id)
				print(_batch.id)
				print(batch_ids)
				# only do the query if there isn't already a match from another pass
				if a_record.oclc_number and not a_record.oclc_match_id:
					print("oclc: "+a_record.oclc_number)
					a = time.time()

					t = text(match_query_sql).bindparams(bindparam('batch_ids',expanding=True))
					s = records_table.select(t)
					match_result = connection.execute(
						s,
						{
							'record_a_oclc':a_record.oclc_number,
							'batch_ids':batch_ids,
							'record_a_batch':a_record.batch_id
						})

					match = match_result.fetchall()
					print("match? : "+str(match))
					b = time.time()
					print('select: '+str(b-a))

					if not match == []:
						match_record = match[0]
						# a = time.time()
						u = update(records_table)
						u = u.values(
							{"oclc_match_id": match_record.id}
							).where(
								or_(
									records_table.c.id == a_record.id,
									records_table.c.id == match_record.id
									)
								)
						connection.execute(u)
						# b = time.time()
						# print("update : "+str(b-a))

						record_field_count = a_record.field_count
						match_field_count = match_record.field_count

						if record_field_count > match_field_count:
							batch_dict['records w more fields'] += 1
					else:
						batch_dict['no oclc match'] += 1
				elif a_record.oclc_match_id:
					record_field_count = a_record.field_count
					a = time.time()
					s = records_table.select(
						records_table.c.field_count
						).where(records_table.c.id==a_record.oclc_match_id)
					result = connection.execute(s)
					b = time.time()
					print("select based on match id: "+str(b-a))
					match_field_count = result.first()[0]
				else:
					batch_dict['no oclc match'] += 1

			comparison_dict['batches'].append(batch_dict)

		# print(comparison_dict)
		_session = Session.query.get(current_session_id)
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
