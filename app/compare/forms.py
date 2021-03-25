# non-standard libraries
from flask_wtf import FlaskForm
from flask_wtf import FileField
import wtforms
from wtforms.validators import DataRequired, Email
from wtforms.ext.sqlalchemy.fields import QuerySelectField


class FileUploadForm(FlaskForm):
	'''
	Session upload form
	'''
	batch_1 = wtforms.FileField()
    batch_2 = wtforms.FileField()
	submit = wtforms.SubmitField('Submit')
