from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, BooleanField
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Email, EqualTo

from ..models import User

class AddUserForm(FlaskForm):
	"""
	Form for admin to create users
	"""

	email = StringField('email address', validators=[DataRequired(),Email()])
	username = StringField('username')
	affiliation = StringField('affiliation')
	is_admin = BooleanField('Admin?')
	password = PasswordField('Password', validators=[EqualTo('confirm_password')])
	confirm_password = PasswordField('Confirm Password')

	submit = SubmitField('Submit')

	def validate_email(self, field):
		if User.query.filter_by(email=field.data).first():
			raise ValidationError('Email is already in use.')

class EditUserForm(FlaskForm):
	"""
	Form for admin to create or edit users
	Had to create a separate form to avoid the validate_email method above,
	otherwise editing an existing user will fail.
	There's a better way to do it I know but I;m in a hurry. :/
	"""
	email = StringField('email address', validators=[DataRequired(),Email()])
	username = StringField('username')
	affiliation = StringField('affiliation')
	is_admin = BooleanField('admin?')
	password = PasswordField('password', validators=[EqualTo('confirm_password')])
	confirm_password = PasswordField('confirm password')

	submit = SubmitField('submit')
