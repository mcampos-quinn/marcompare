# non-standard libraries
from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed, FileField
import wtforms
from wtforms.fields import MultipleFileField, StringField
from wtforms.validators import DataRequired, Email
from wtforms.ext.sqlalchemy.fields import QuerySelectField


class FileUploadForm(FlaskForm):
	'''
	Session upload form
	tbd: how to handle more than two files
	'''
	batch_1 = FileField('File 1',validators=[FileRequired(),FileAllowed(['json','csv','pdf'])])
	batch_1_source = StringField('Optional: list the source of this file')
	batch_2 = FileField('File 2',validators=[FileRequired(),FileAllowed(['json','csv','pdf'])])
	batch_2_source = StringField('Optional: list the source of this file')
	# batch_3 = FileField('File 3',validators=[FileAllowed(['json','csv','pdf'])])
	submit = wtforms.SubmitField('Submit')
