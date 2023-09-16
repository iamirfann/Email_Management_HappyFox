import sqlite3

conn = sqlite3.connect('email_db.sqlite')
cursor = conn.cursor()

# Execute SQL queries to retrieve data
cursor.execute('SELECT * FROM email_details')
data = cursor.fetchall()

# Print or process the retrieved data
for row in data:
    print(row)

conn.close()
