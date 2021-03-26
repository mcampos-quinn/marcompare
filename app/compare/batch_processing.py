import json
import os
import re

from .. import db
from .. models import Batch, Session, Record, Field

def read_files(my_session_id):
	the_session = Session.query.get(my_session_id)
	my_batches = Batch.query.filter_by(session_id=my_session_id).all()
	# print("RUBY "*100)
	for batch in my_batches:
		parse_json(batch)

def parse_json(batch):
	with open(batch.filepath,'r') as f:
		data = json.load(f)
		for record in data['collection']['record']:
			_record = Record(
					batch_id = batch.id
				)
			db.session.add(_record)
			db.session.commit()
			db.session.refresh(_record)

			for data_tag in record['datafield']:
				_tag = data_tag['@tag']
				_ind1 = data_tag['@ind1']
				_ind2 = data_tag['@ind2']
				field_content =  parse_subfields(data_tag['subfield'])
				_field = Field(
					tag=_tag,
					indicator_1=_ind1,
					indicator_2=_ind2,
					text=field_content,
					record_id = _record.id
				)
				db.session.add(_field)
				if data_tag['@tag'] == '035':
					if isinstance(data_tag['subfield'],list):
						for sf in data_tag['subfield']:
							if sf['@code'] == 'a' and 'OCoLC' in sf['#text']:
								_record.oclc_number = re.sub(r"\D", "", sf['#text']).lstrip('0')
					elif isinstance(data_tag['subfield'],dict):
						if data_tag['subfield']['@code'] == 'a' \
							and 'OCoLC' in data_tag['subfield']['#text']:
							# print(tag['subfield']['#text'])
							_record.oclc_number = re.sub(r"\D", "", data_tag['subfield']['#text']).lstrip('0')
			db.session.commit()

def parse_subfields(_subfield):
	_list = []
	if isinstance(_subfield,list):
		for subfield_dict in _subfield:
			for code,text in subfield_dict.items():
				_list.append("${} {}; ".format(code,text))
	elif isinstance(_subfield,dict):
		for code,text in _subfield.items():
			_list.append("${} {}; ".format(code,text))
	return "".join(_list)
