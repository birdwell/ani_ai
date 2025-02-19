import sqlite3

db_path = "anilist_global.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE global_media ADD COLUMN average_score INTEGER;")
    print("Added column: average_score")
except sqlite3.OperationalError as e:
    print("Column average_score may already exist:", e)

try:
    cursor.execute("ALTER TABLE global_media ADD COLUMN popularity INTEGER;")
    print("Added column: popularity")
except sqlite3.OperationalError as e:
    print("Column popularity may already exist:", e)

try:
    cursor.execute("ALTER TABLE global_media ADD COLUMN rankings TEXT;")
    print("Added column: rankings")
except sqlite3.OperationalError as e:
    print("Column rankings may already exist:", e)

conn.commit()
conn.close()