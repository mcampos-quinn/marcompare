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

	@property
	def password(self):
		"""
		Prevent pasword from being accessed
		"""
		raise AttributeError('password is not a readable attribute.')

	@password.setter
	def password(self, password):
		"""
		Set password to a hashed password
		"""
		self.password_hash = generate_password_hash(password)

	def verify_password(self, password):
		"""
		Check if hashed password matches actual password
		"""
		return check_password_hash(self.password_hash, password)

	def __repr__(self):
		return '<User: {}>'.format(self.username)

# Set up user_loader
@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

class Session(db.Model):
	"""
	Create a Session table
	this is a comparison session
	there should be at least two batches
	"""

	__tablename__ = 'sessions'

	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	started_timestamp = db.Column(
		db.DateTime,
		default=datetime.datetime.utcnow
		)
	overall_batch_comparison_dict = db.Column(db.Text)
	author_batch_comparison_dict = db.Column(db.Text)
	title_batch_comparison_dict = db.Column(db.Text)
	physical_batch_comparison_dict = db.Column(db.Text)
	note_batch_comparison_dict = db.Column(db.Text)
	subject_batch_comparison_dict = db.Column(db.Text)
	added_author_batch_comparison_dict = db.Column(db.Text)

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
		db.ForeignKey('sessions.id'),
		nullable=False
		)
	source = db.Column(db.String(200))
	filepath = db.Column(db.String(200))

	records_w_more_fields = db.Column(db.Integer)

	records = db.relationship('Record', cascade="all,delete", backref='batch', lazy='dynamic')

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
		db.ForeignKey('batches.id'),
		nullable=False
		)
	oclc_number = db.Column(db.String(200))
	# this is the id of the record containing a matching oclc number
	oclc_match_id = db.Column(db.Integer)
	raw_record = db.Column(db.Text)
	# all the fields
	field_count = db.Column(db.Integer)
	# 1xx
	author_field_count = db.Column(db.Integer)
	# 2xx
	title_field_count = db.Column(db.Integer)
	# 3xx
	physical_field_count = db.Column(db.Integer)
	# 5xx
	note_field_count = db.Column(db.Integer)
	# 6xx
	subject_field_count = db.Column(db.Integer)
	# 7xx
	added_author_field_count = db.Column(db.Integer)
	# 856
	link_field_count = db.Column(db.Integer)

	fields = db.relationship('Field', cascade="all,delete", backref='record', lazy='dynamic')

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
		db.ForeignKey('records.id'),
		nullable=False
		)
	tag = db.Column(db.String(100))
	indicator_1 = db.Column(db.String(10))
	indicator_2 = db.Column(db.String(10))
	text = db.Column(db.Text)
