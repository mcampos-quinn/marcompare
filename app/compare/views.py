from flask import render_template
from flask_login import login_required, current_user

from . import compare

@compare.route('/start_session')
# @login_required
def start_session():
	"""
	Render the dashboard template on the /dashboard route
	"""
	return render_template('compare/start_session.html', title="Start comparing")
