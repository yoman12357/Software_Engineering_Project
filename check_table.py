import sqlite3
conn = sqlite3.connect('data/cybersrs.db')
cursor = conn.cursor()
cursor.execute('SELECT sql FROM sqlite_master WHERE type="table" AND name="phase5_evaluation_run"')
print('phase5_evaluation_run schema:')
print(cursor.fetchone()[0])
cursor.execute('SELECT sql FROM sqlite_master WHERE type="table" AND name="phase5_case_result"')
result = cursor.fetchone()
if result:
    print('phase5_case_result schema:')
    print(result[0])
else:
    print('phase5_case_result table does not exist')