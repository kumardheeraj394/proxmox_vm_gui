import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = "vm_gui.db"  # your database file

# Replace these with your desired credentials
username = "admin"
password = "Admin@123"  # login password

# Hash the password
hashed_password = generate_password_hash(password)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Create users table if it doesn't exist
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

# Insert the user
try:
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
    conn.commit()
    print(f"✅ User '{username}' created successfully. Password: {password}")
except sqlite3.IntegrityError:
    print(f"⚠️ User '{username}' already exists. Try logging in with that user.")

conn.close()

