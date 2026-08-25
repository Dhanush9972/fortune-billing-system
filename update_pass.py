import sqlite3
from werkzeug.security import generate_password_hash

NEW_USERNAME = 'admin'
NEW_PASSWORD = 'kalyankumar'

conn = sqlite3.connect('fortune_billing.db')
cursor = conn.cursor()
hashed_password = generate_password_hash(NEW_PASSWORD)

cursor.execute('UPDATE users SET username = ?, password = ? WHERE id = 1', (NEW_USERNAME, hashed_password))
conn.commit()
conn.close()
print("Password updated successfully!")