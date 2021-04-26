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
		'admin/users.html',
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
		user = User(
			email=form.email.data,
			username=form.username.data,
			affiliation=form.affiliation.data,
			is_admin=form.is_admin.data,
			password=form.password.data
			)
		try:
			db.session.add(user)
			db.session.commit()
			flash('You have successfully added a new user.')
		except Exception as e:
			flash('Error: user already exists.')

		return redirect(url_for('admin.list_users'))

	return render_template(
		'admin/user.html',
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
		user.email = form.email.data
		user.username = form.username.data
		user.affiliation = form.affiliation.data
		user.is_admin = form.is_admin.data
		if form.password.data:
			user.password = form.password.data
		try:
			db.session.commit()
			flash('You have successfully edited the user.')

			# redirect to the users page
			return redirect(url_for('admin.list_users'))
		except Exception as e:
			print(e)
			flash('Error editing the user.')
			return redirect(url_for('admin.list_users'))

	# this pre-populates the form with existing data from the db
	form.email.data = user.email
	form.username.data = user.username
	form.affiliation.data = user.affiliation
	form.is_admin.data = user.is_admin
	return render_template(
		'admin/user.html',
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
