from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email

from .. models import User

class LoginForm(FlaskForm):
	"""
	Form for users to login
	"""
	email = StringField('email', validators=[DataRequired(), Email()])
	password = PasswordField('password', validators=[DataRequired()])
	submit = SubmitField('login')
