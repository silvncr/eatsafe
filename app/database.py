# imports
from os import path as os_path
from sqlite3 import connect
from sys import path as sys_path
from werkzeug.security import generate_password_hash


# create database
def init_database(
	name: str,
	commands: list[str],
):

	# connect to database
	db = connect(
		os_path.join(sys_path[0], name)
	)

	# create cursor
	c = db.cursor()

	# create tables
	for command in commands:
		command_mod = command.strip()
		for key in [
			'admin',
		]:
			command_mod = command_mod.replace(
				f'${key}',
				generate_password_hash(key)
			)
		c.execute(command_mod)
		print(command_mod)

	# commit changes
	db.commit()
	db.close()


# main
if __name__ == '__main__':
	init_database('eatsafe.db', open(
		os_path.join(sys_path[0], 'schema.sql')
	).read().split(';'))
