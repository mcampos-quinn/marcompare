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
	SELECT COUNT()
	'''
	for _batch in my_batches:
		comparison_dict[_batch.id] = {}
		comparison_dict[_batch.id]['record count'] = db.execute(record_tally_sql)
