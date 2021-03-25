from flask import Blueprint

compare = Blueprint('compare', __name__)

from . import views
