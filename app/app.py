# imports
from csv import reader
from typing import Type
from flask import flash, Flask, redirect, render_template, request, session, url_for
from itertools import product
from os import path as os_path
from re import match
from sqlite3 import connect, Connection, Cursor, Row
from sys import path as sys_path
from uuid import uuid4
from werkzeug.security import check_password_hash, generate_password_hash


# create flask app
app = Flask(__name__)
app.secret_key = uuid4().hex


# database schematics
class schema:
	allowed_permits = [
		'Cafe/Restaurant',
		'Mobile Food Unit',
	]
	registration = [
		'username',
		'email',
		'phone',
		'password',
	]
	restaurant = [
		'id',
		'name',
		'address',
		'rating',
		'phone',
		'email',
		'owner',
	]
	users = [
		'id',
		'username',
		'email',
		'phone',
		'password',
		'role',
	]


# database connection
def get_db():
	return connect(
		os_path.join(
			sys_path[0], 'eatsafe.db'
		)
	)


# database cursor
def get_db_cursor(db=get_db):
	return db().cursor()


# close database connections
def cleanup_connections(namespace: dict):
	for var in namespace:
		if isinstance(var, Connection):
			var.close()
		if isinstance(var, Cursor):
			var.connection.close()


# check if logged in
def logged_in() -> bool:
	global session
	if 'logged_in' not in session:
		session.update({'logged_in': False})
	return session['logged_in']


# index; redirects to search
@app.route('/')
def index():
	return redirect(url_for('search'))


# search page
@app.route('/search', methods=['GET', 'POST'])
def search():

	# set default query and search results
	query = ''
	results = []

	# check if user submitted a query
	if request.args.get('q'):

		# get search results from eatsafe.db
		query = request.args.get('q', '', str)
		c = get_db_cursor()
		try:
			c.execute(
				f'SELECT * FROM restaurants WHERE {
					' AND '.join([
						f'({
							' OR '.join([
								f'{field} LIKE "%{word}%"' for field in schema.restaurant
							])
						})' for word in query.replace('"', '""').split(' ')
					])
				}'
			)
			results = [dict(zip(schema.restaurant, result)) for result in c.fetchall()]
			for result in results:
				try:
					result['rating'] = int(result['rating'])
				except (IndexError, TypeError, ValueError):
					result['rating'] = None
			print(f'search query "{query}" returned {len(results)} results')
		finally:
			c.close()

	# render search page with results
	return render_template(
		'search.html',
		logged_in=logged_in(),
		query=query or '',
		results=results,
		session=session,
	)


# dashboard page
@app.route('/dashboard')
def dashboard():

	# check if user is logged in
	if logged_in():

		# show dashboard with account info
		return render_template('dashboard.html', logged_in=logged_in(), session=session)

	# if user is not logged in, redirect to login page
	return redirect(url_for('login'))


# admin page
@app.route('/admin', methods=['GET', 'POST'])
def admin():

	# check if user is logged in
	if logged_in():

		# check if user is an admin
		if session['role'] == 'admin':

			# check if file is uploaded
			if request.method == 'POST' and 'csv_file' in request.files:

				# read csv file
				csv_file = request.files['csv_file']
				csv_reader = reader(csv_file.read().decode('utf-8').splitlines())

				# connect to database
				c = get_db_cursor()

				# iterate over rows and insert into database
				first_iter = True
				for row in csv_reader:
					if first_iter:
						first_iter = False
						continue
					if not any([
						row[8].lower() == permit_type.lower() for permit_type in schema.allowed_permits
					]):
						continue
					try:
						name = str(row[1])
						address = str(row[2])
					except (IndexError, TypeError, ValueError):
						continue
					try:
						rating = int(row[7])
					except (IndexError, TypeError, ValueError):
						rating = None
					if not all([name, address]):
						continue
					c.execute('INSERT INTO restaurants (name, address, rating) VALUES (?, ?, ?)', [
						name,
						address,
						rating,
					])

				# commit changes and close connection
				c.connection.commit()
				c.connection.close()

				# return with message
				flash(f'Successfully uploaded {csv_file.filename}! {csv_reader.line_num} rows inserted.', 'success')

				# redirect to search
				return redirect(url_for('search'))

			# show admin page
			return render_template('admin.html', logged_in=logged_in(), session=session)

		# if user is not an admin, redirect to dashboard
		return redirect(url_for('dashboard'))

	# if user is not logged in, redirect to index to handle further redirections
	return redirect(url_for('index'))


# login page
@app.route('/login', methods=['GET', 'POST'])
def login():

	# database connection wrapper
	try:

		# get email from session if exists
		username_temp = session.get('username_temp', '')

		# check if user is already logged in
		if logged_in():
			return redirect(url_for('dashboard'))

		# check if user submitted the login form
		if request.method == 'POST':
			print(request.form | {'password': 'redacted'})

			# query database for user
			c = get_db_cursor()

			# database connection wrapper
			try:
				c.execute(
					'SELECT * FROM users WHERE username = ?',
					(request.form['username'],)
				)
				account = c.fetchone()
				print(f'login attempted | username linked to user: {account}')

			# close database connection
			finally:
				c.close()

			# check if user exists and password is correct
			# note: password hash is at index 4
			if account and check_password_hash(account[4], request.form['password']):

				# set session variables
				session.update({'logged_in': True})
				for cred in schema.users:
					session.update({cred: account[schema.users.index(cred)]})

				# redirect to dashboard
				return redirect(url_for('dashboard'))

			# if login failed, show error message
			flash('Invalid email or password!', 'error')

		# render login page
		return render_template('login.html', username_temp=username_temp)

	# close database connection
	finally:
		cleanup_connections(locals())
		cleanup_connections(globals())


# register page
@app.route('/register', methods=['GET', 'POST'])
def register():

	# connect to database
	get_db().row_factory = Row
	c = get_db_cursor()

	# database connection wrapper
	try:

		# check if credentials were entered
		if request.method == 'POST':
			print(request.form | {'password': 'redacted'})

			# check if all fields are filled out
			if all(field in request.form for field in schema.registration):

				# hash password
				_hashed_password = generate_password_hash(
					request.form['password']
				)

				# check if account exists
				c.execute(
					'SELECT * FROM users WHERE username = ?',
					(request.form['username'],)
				)
				account = c.fetchone()
				print(f'registry attempted | username linked to user: {account}')

				# account exists error + validation checks
				if account:
					flash('Account already exists!')
				elif not match(r'[^@]+@[^@]+\.[^@]+', request.form['email']):
					flash('Invalid email address!')
				elif not all(
					match(r'[A-Za-z]+', request.form[name_type]) for name_type in [
						'username',
					]
				):
					flash('Usernames must contain only letters!')
				elif not all(
					request.form[field] for field in schema.registration
				):
					flash('Please fill out the form!')

				# otherwise, create account
				else:
					c.execute(
						'''INSERT INTO users (
							username, email, phone, password, role
						) VALUES (
							?, ?, ?, ?, ?
						)''',
						(
							request.form['username'],
							request.form['email'],
							request.form['phone'],
							_hashed_password,
							'user',
						)
					)

					# commit changes to database
					c.connection.commit()

					# delete password from memory for security (account creation succeeded)
					del _hashed_password

					# store username for login autofill
					session['email_temp'] = request.form['email']

					# redirect to login page
					flash('Account created successfully!')
					return redirect(url_for('login'))

				# delete password from memory for security (account creation failed)
				del _hashed_password

		# render register page with form data (if any)
		return render_template('register.html', form_data=(
			request.form | {key: '' for key in schema.registration} | {'password': ''}
		))

	# close database connection
	finally:
		c.close()
		cleanup_connections(locals())
		cleanup_connections(globals())


# logout; redirects to index, then to search
@app.route('/logout')
def logout():

	# check if user is logged in
	if not logged_in():
		return redirect(url_for('index'))

	# remove session data to log out user
	print(f'logging out from session: {session['username']}')
	for cred in schema.users:
		session.pop(cred)
		print(f'\t- popped: {cred}')
	session.update({'logged_in': False})

	# redirect to login page via index
	return redirect(url_for('index'))


# run app
if __name__ == '__main__':
	app.run(debug=True)
