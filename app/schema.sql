CREATE TABLE IF NOT EXISTS users (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	username TEXT NOT NULL UNIQUE,
	email TEXT NOT NULL,
	phone TEXT NOT NULL,
	password TEXT NOT NULL,
	role TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS restaurants (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT NOT NULL,
	address TEXT NOT NULL,
	rating INTEGER,
	phone TEXT,
	email TEXT,
	owner INTEGER,
	FOREIGN KEY (owner) REFERENCES users (id)
);
CREATE TABLE IF NOT EXISTS comments (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	comment TEXT NOT NULL,
	timestamp TEXT NOT NULL,
	user INTEGER NOT NULL,
	restaurant INTEGER NOT NULL,
	FOREIGN KEY (user) REFERENCES users (id),
	FOREIGN KEY (restaurant) REFERENCES restaurants (id)
);
CREATE TABLE IF NOT EXISTS images (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	filename TEXT NOT NULL,
	comment INTEGER NOT NULL,
	FOREIGN KEY (comment) REFERENCES comments (id)
);
INSERT INTO users (
	username, email, phone, password, role
) VALUES (
	'admin', 'admin@eatsafe', '1234567890', '$admin', 'admin'
);
