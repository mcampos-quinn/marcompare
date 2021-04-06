# non-standard libraries
from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed, FileField
import wtforms
from wtforms.fields import MultipleFileField, StringField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email
# from wtforms.ext.sqlalchemy.fields import QuerySelectField


class FileUploadForm(FlaskForm):
	'''
	Session upload form
	tbd: how to handle more than two files
	'''
	session_notes = StringField('Session notes')
	batch_1 = FileField('Batch 1',validators=[FileRequired(),FileAllowed(['json'])])
	batch_1_source = StringField('Batch source')
	batch_1_identifier_field = SelectField(
		'Field w/ OCLC number',
		choices=[('001', '001'), ('035', '035')],
		default='001'
		)
	batch_1_namespaces = BooleanField(
		'Does this file use XML namespaces?',
		default=False
		)

	batch_2 = FileField('Batch 2',validators=[FileRequired(),FileAllowed(['json'])])
	batch_2_source = StringField('Batch source')
	batch_2_identifier_field = SelectField(
		'Field w/ OCLC number',
		choices=[('001', '001'), ('035', '035')],
		default='001'
		)
	batch_2_namespaces = BooleanField(
		'Does this file use XML namespaces?',
		default=False
		)
	# batch_3 = FileField('File 3',validators=[FileAllowed(['json','csv','pdf'])])

	submit = SubmitField('Submit')

class SessionForm(FlaskForm):
	"""
	Form for user to edit a session
	"""
	session_notes = StringField('Session notes')
	# description = StringField('Description', validators=[DataRequired()])
	submit = SubmitField('Submit')
