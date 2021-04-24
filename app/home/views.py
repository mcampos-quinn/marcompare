from flask import render_template, abort
from flask_login import login_required, current_user

from . import home

def check_admin():
	"""
	Prevent non-admins from accessing the page
	"""
	if not current_user.is_admin:
		abort(403)

@home.route('/',methods=['GET','POST'])
def homepage():
	"""
	Render the homepage template on the / route
	"""
	return render_template('home/index.html', title="Welcome", current_user=current_user)

@home.route('/dashboard')
@login_required
def dashboard():
	"""
	Render the dashboard template on the /dashboard route
	"""
	return render_template('home/dashboard.html', title="Dashboard")

@home.route('/admin_dashboard')
@login_required
def admin_dashboard():
	"""
	Render the admin dashboard template on the /admin_dashboard route
	"""
	check_admin()

	return render_template('home/admin_dashboard.html', title="Admin Dashboard")
