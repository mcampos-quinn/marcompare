from flask import current_app

from sqlalchemy import create_engine, text
from sqlalchemy import Column, Integer, String, Text, MetaData, Table

class DB_Hookup():
	"""docstring for DB_Hookup."""

	def __init__(self):
		self.engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'])
		self.metadata = MetaData()
		self.metadata.reflect(bind=self.engine)
