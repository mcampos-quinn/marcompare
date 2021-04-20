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
				if a_record.oclc_number:
					if a_record.oclc_match_id == None:
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
						print("this many oclc matches for the record "+str(len(match)))
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
							print(" &  "*300)
							print(record_field_count)
							print(match_field_count)
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
					print("^ ^ "*100)
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

field_set_criteria = {
	"1xx":{
		'field count':'author_field_count',
		'comparison dict':'author_batch_comparison_dict'
	},
	"2xx":{
		'field count':'title_field_count',
		'comparison dict':'title_batch_comparison_dict'
	},
	"3xx":{
		'field count':'physical_field_count',
		'comparison dict':'physical_batch_comparison_dict'
	},
	"5xx":{
		'field count':'note_field_count',
		'comparison dict':'note_batch_comparison_dict'
	},
	"6xx":{
		'field count':'subject_field_count',
		'comparison dict':'subject_batch_comparison_dict'
	},
	"7xx":{
		'field count':'added_author_field_count',
		'comparison dict':'added_author_batch_comparison_dict'
	}
}

def batch_compare_field_set(current_session_id,field_set):
	hookup = DB_Hookup()
	field_set_count = field_set_criteria[field_set]['field count']
	stored_comparison_dict = field_set_criteria[field_set]['comparison dict']

	comparison_dict, my_batches, batch_ids = get_session_batches(current_session_id)
	# print(comparison_dict)
	session_timestamp = get_session_timestamp(current_session_id)
	batches = []
	for b in my_batches:
		# make a list of dicts representing each batch
		d = {
			'id':b.id,
			'source':b.source,
			'column':my_batches.index(b),
			'colspan':None
			}
		batches.append(d)
	compare = {
		'batches':batches,
		'session_timestamp': session_timestamp,
		'session_timestamp_int': re.sub(r"\D", "", session_timestamp),
		'session_max_records': '',
		'rows':[{'row':0,'records':[]}]}

	with hookup.engine.connect() as connection:
		batch_records_sql = '''
		records.batch_id IN :batch_ids
		'''
		records_table = hookup.metadata.tables['records']
		t = text(batch_records_sql).bindparams(
			bindparam('batch_ids',expanding=True)
			)
		s = records_table.select(t)
		# this returns all the records that are in the set of batch ids
		result = connection.execute(s,{'batch_ids':batch_ids})

		records = []
		for item in result:
			if item.oclc_match_id:
				# only include records with an OCLC match
				record_dict = {}
				record_dict['id'] = item.id
				record_dict['title'] = item.title
				record_dict['batch_id'] = str(item.batch_id) # this is a string in the batch_ids list
				record_dict['column'] = [x['column'] for x in batches if x['id'] == item.batch_id][0]
				record_dict['color'] = None
				record_dict['oclc_match'] = item.oclc_match_id
				# print('oclc match from subj '+str(record_dict['oclc_match']))
				record_dict[field_set_count] = item[field_set_count]
				records.append(record_dict)
			del item
		# print(records)
		for _record in records:
			if not _record['color']:
				oclc_match = [
					x for x in records if (x['oclc_match'] == _record['id'])
					# and (x['batch_id'] != _record['batch_id'])
					]
				if not oclc_match == []:
					# print(oclc_match)
					oclc_match = oclc_match[0]
					if oclc_match[field_set_count] > _record[field_set_count]:
						_record['color'] = 'red'
						oclc_match['color'] = 'green'
					elif oclc_match[field_set_count] < _record[field_set_count]:
						_record['color'] = 'green'
						oclc_match['color'] = 'red'

	row_counter = 1
	matched_records = []
	for _record in records:
		if not _record in matched_records:
			row = {
				'row':row_counter,
				'record_ids':[],
				'records':[]
			}
			row_record = build_field_comparison_dict(_record,field_set_count)
			row['records'].append(row_record)
			row['record_ids'].append(_record['id'])
			# @fixme this result list includes records
			# that are dupe OCLC records in a system
			# update: that's... a good thing
			_match = [item for item in records if item['oclc_match'] == _record['id']]
			for item in _match:
				i = build_field_comparison_dict(item,field_set_count)
				row['records'].append(i)
				row['record_ids'].append(item['id'])
				matched_records.append(item)

			row['records'].sort(key= lambda x : x['data']['batch_id'])
			matched_records.append(_record)
			compare['rows'].append(row)
			row_counter += 1

	# print(compare['rows'])
	empty_record = {'id':'empty','column':''}
	# get the number of columns necessary, i.e. the number of batches
	# in the session.
	# iterate over this integer's range() and match each
	# to the batch's column.
	# this sets the width of each batch's column in display
	columns = [i for i in range(len(my_batches))]
	# print("* ^ "*100)
	# print(columns)
	# use this integer to get the right number of <th> tags in the table
	session_max_records = 0
	for column_index in columns:
		# print(column_index)
		counts = []
		for row in compare['rows']:
			# go through each row and count how many records
			# are in each batch's column
			count = [r['column'] for r in row['records']].count(column_index)
			counts.append(count)
		colspan = max(counts)
		session_max_records += colspan
		# print("** ** "*100)
		# print(colspan)
		for batch in compare['batches']:
			# now set the <th> colspan attribute for each batch to the correct
			# number of records
			if batch['column'] == column_index:
				batch['colspan'] = colspan
		for row in compare['rows']:
			# now if there are fewer records than the max in a given column
			# fluff out the row with extra empty records so the table
			# will have the correct shape (i.e. the right number of <td> per row)
			count = [r['column'] for r in row['records']].count(column_index)
			# print("%% %% "*100)
			# print(x)
			# print([r['column'] for r in row['records']])
			if count < colspan:
				empties = abs(colspan - count)
				# print("EMPTIES")
				# print(empties)
				# print(count)
				# print(list(range(empties)))
				for x in list(range(empties)):
					empty_record['column'] = column_index
					row['records'].append(empty_record)
					empty_record['column'] = ''

	# print(compare)
	# get 1-indexed version of the max number of records in a row
	#
	session_max_records = list(range(session_max_records+1))[1:]
	compare['session_max_records'] = session_max_records
	_session = Session.query.get(current_session_id)
	setattr(_session,stored_comparison_dict,str(compare))
	db.session.commit()
	return compare

def build_field_comparison_dict(record,field_set_count):
	# field_set_count should be e.g. record[field_set_count]
	record_dict = {
			'id':record['id'],
			'column':record['column'],
			'data':{
				'batch_id':record['batch_id'],
				'title':record['title'],
				'color':record['color'],
				field_set_count:record[field_set_count],
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
