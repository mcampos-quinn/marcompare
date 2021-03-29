from flask import current_app

from sqlalchemy import create_engine, text
from sqlalchemy import Column, Integer, String, Text, MetaData, Table
from sqlalchemy.pool import StaticPool

class DB_Hookup():
	"""docstring for DB_Hookup."""

	def __init__(self):
		self.engine = create_engine(
			current_app.config['SQLALCHEMY_DATABASE_URI']
			# poolclass=StaticPool,
			# connect_args={'check_same_thread': False}
			)
		self.metadata = MetaData()
		self.metadata.reflect(bind=self.engine)
