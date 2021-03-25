import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager

class User(UserMixin, db.Model):
	'''
	Create a User table
	Attributes
	- username
	- email
	- affiliation
	- password hash
	- is_admin
	'''

	__tablename__ = 'users'

	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(60), index=True, unique=True)
	username = db.Column(db.String(60), index=True, unique=True)
	affiliation = db.Column(db.String(100))
	password_hash = db.Column(db.String(128))
	is_admin = db.Column(db.Boolean, default=False)

	sessions = db.relationship('Session', backref='user', lazy=True)

class Session(db.Model):
	"""
	Create a Session table
	this is a comparison session
	there should be at least two batches
	"""

	__tablename__ = 'sessions'

	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	started_timestamp = db.Column(
		db.DateTime,
		default=datetime.datetime.utcnow
		)

	batches = db.relationship('Batch', backref='session', lazy=True)

	def __repr__(self):
		return '<Session: {}>'.format(self.id)

class Batch(db.Model):
	"""
	Create a Batch table
	this is one set of records from a particular source
	there should be at least one record in the batch
	"""

	__tablename__ = 'batches'

	id = db.Column(db.Integer, primary_key=True)
	session_id = db.Column(
		db.Integer,
		db.ForeignKey('session.id'),
		nullable=False
		)
	source = db.Column(db.String(200))

	records = db.relationship('Record', backref='batch', lazy=True)

	def __repr__(self):
		return '<Batch: {}>'.format(self.id)

class Record(db.Model):
	"""
	Create a Record table
	"""

	__tablename__ = 'records'

	id = db.Column(db.Integer, primary_key=True)
	batch_id = db.Column(
		db.Integer,
		db.ForeignKey('batch.id'),
		nullable=False
		)
	oclc_number = db.Column(db.String(200))

	fields = db.relationship('Field', backref='record', lazy='dynamic')

	def __repr__(self):
		return '<Record: {}>'.format(self.id)

class Field(db.Model):
	"""
	Create a Field table
	Field content stored as a single string
	"""

	__tablename__ = 'fields'

	id = db.Column(db.Integer, primary_key=True)
	record_id = db.Column(
		db.Integer,
		db.ForeignKey('record.id'),
		nullable=False
		)
	tag = db.Column(db.String(100))
	indicator_1 = db.Column(db.String(10))
	indicator_2 = db.Column(db.String(10))
	text = db.Column(db.Text)
