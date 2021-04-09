import os
# from instance import config as instance

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    DEBUG = False
    HELLO = True
    UPLOAD_FOLDER = os.path.join(basedir,"app/tmp")
    MARCEDIT_BINARY_PATH = "/full/path/to/marcedit/binary"
    # MARCEDIT_BINARY_PATH = "/Applications/MarcEdit3.app/Contents/MacOS/MarcEdit3"
    # ALLOWED_EXTENSIONS = {'json'}

class DevelopmentConfig(Config):
	"""
	Development configurations
	"""
	SQLALCHEMY_DATABASE_URI = "sqlite:///{}".format(
        os.path.join(basedir,"app.db")
    )
	DEBUG = True
	SQLALCHEMY_ECHO = True
	DEBUG_TB_PROFILER_ENABLED = True
	SQLALCHEMY_TRACK_MODIFICATIONS = False

class ProductionConfig(Config):
	"""
	Production configurations
	"""

	DEBUG = False
	SQLALCHEMY_DATABASE_URI = "sqlite:///{}".format(os.path.join(basedir,"app.db"))
	SQLALCHEMY_ECHO = False
	SQLALCHEMY_TRACK_MODIFICATIONS = False

config_options = {
    'development':DevelopmentConfig,
    'production':ProductionConfig
}
