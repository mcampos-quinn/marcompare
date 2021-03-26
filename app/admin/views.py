#!/usr/bin/env python3

'''
Taken from https://scotch.io/tutorials/build-a-crud-web-app-with-python-and-flask-part-two
'''

from flask import abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from . import admin
from .forms import AddUserForm, EditUserForm
from .. import db
from ..models import User


def check_admin():
	"""
	Prevent non-admins from accessing the page
	"""
	if not current_user.is_admin:
		abort(403)

####################
# User Views
@admin.route('/users')
@login_required
def list_users():
	"""
	List all users
	"""
	check_admin()

	users = User.query.all()
	return render_template(
		'admin/users/users.html',
		users=users,
		title='Users'
		)

@admin.route('/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
	"""
	Add a user to the database
	"""
	check_admin()

	add_user = True

	form = AddUserForm()
	# print(form.data)
	# print("HIIHII")
	if form.validate_on_submit():
		# print(form.department_id.data.id)
		# print(type(form.department_id.data))

		user = User(
			department_id=form.department_id.data.id,
			email=form.email.data,
			username=form.username.data,
			first_name=form.first_name.data,
			last_name=form.last_name.data,
			RSusername=form.RSusername.data,
			RSkey=form.RSkey.data,
			is_admin=form.is_admin.data,
			password=form.password.data
			)
		try:
			# add department to the database
			db.session.add(user)
			# print(user)
			db.session.commit()
			flash('You have successfully added a new user.')
		except Exception as e:
			# in case department name already exists
			# print(str(e))
			flash('Error: user already exists.')

		# redirect to departments page
		return redirect(url_for('admin.list_users'))

	# load department template
	return render_template(
		'admin/users/user.html',
		action="Add",
		add_user=add_user,
		form=form,
		title="Add User"
		)

@admin.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_user(id):
	"""
	Edit a user
	"""
	check_admin()

	add_user = False

	user = User.query.get_or_404(id)
	form = EditUserForm(obj=user)
	if form.validate_on_submit():
		# print(form.data)
		if not form.department_id.data == None:
			user.department_id=form.department_id.data.id
		user.email = form.email.data
		user.username = form.username.data
		user.first_name = form.first_name.data
		user.last_name = form.last_name.data
		user.RSusername = form.RSusername.data
		user.RSkey = form.RSkey.data
		user.is_admin = form.is_admin.data
		if form.password.data:
			user.password = form.password.data
		try:
			db.session.commit()
			# print(form.data)
			flash('You have successfully edited the user.')

			# redirect to the users page
			return redirect(url_for('admin.list_users'))
		except Exception as e:
			print(e)
			flash('Error editing the user.')
			return redirect(url_for('admin.list_users'))

	# this pre-populates the form with existing data from the db
	if not user.department_id in ('',None,"Null"):
		deptID = Department.query.get(user.department_id).id
		form.department_id=deptID
	form.email.data = user.email
	form.username.data = user.username
	form.first_name.data = user.first_name
	form.last_name.data = user.last_name
	form.RSusername.data = user.RSusername
	form.RSkey.data = user.RSkey
	form.is_admin.data = user.is_admin
	return render_template(
		'admin/users/user.html',
		action="Edit",
		add_user=add_user,
		form=form,
		user=user,
		title="Edit User"
		)

@admin.route('/users/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_user(id):
	"""
	Delete a user from the database
	"""
	check_admin()

	user = User.query.get_or_404(id)
	db.session.delete(user)
	db.session.commit()
	flash('You have successfully deleted the user.')

	# redirect to the users page
	return redirect(url_for('admin.list_users'))

	return render_template(title="Delete User")
