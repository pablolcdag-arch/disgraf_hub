import sqlite3
import os

db_path = os.environ.get('DATA_DIR', './data') + '/disgraf_hub.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", cursor.fetchall())
conn.close()
