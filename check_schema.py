import sqlite3
conn = sqlite3.connect('data/cybersrs.db')
cursor = conn.cursor()

# Check if there are any views or triggers with kb_version
cursor.execute("SELECT name, sql FROM sqlite_master WHERE sql LIKE '%kb_version%'")
for row in cursor.fetchall():
    print(row)