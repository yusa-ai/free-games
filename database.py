import sqlite3

DB_FILE = "games.db"
DB_SCRIPT_FILE = "script.sql"

connection: sqlite3.Connection = sqlite3.connect(DB_FILE)
cursor: sqlite3.Cursor = connection.cursor()

with open(DB_SCRIPT_FILE) as file:
    script = file.read()

cursor.executescript(script)

connection.commit()
