import sqlite3

DB_PATH = "proxmox_gui.db"
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Add missing columns if they don't exist
try:
    c.execute("ALTER TABLE users ADD COLUMN email TEXT")
except sqlite3.OperationalError:
    pass  # already exists

try:
    c.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
except sqlite3.OperationalError:
    pass  # already exists

conn.commit()
conn.close()
print("✅ Database columns ensured")

