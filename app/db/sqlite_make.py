import sqlite3

conn = sqlite3.connect('LINEUser.db')
cur = conn.cursor()

cur.execute("INSERT INTO Users VALUES ('000111222333444555666777888999000', 'testBot', 'Jakarta', '-6.121435', '106.774124')")

conn.commit()
conn.close()
print("Database configured!")
