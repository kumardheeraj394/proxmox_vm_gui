import sqlite3

DB_PATH = "proxmox_vm_gui.db"

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# User table
c.execute("""
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

# VM status table
c.execute("""
CREATE TABLE IF NOT EXISTS vm_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vmid TEXT,
    vmname TEXT,
    ipaddr TEXT,
    target_node TEXT,
    ssh_status TEXT,
    timestamp INTEGER,
    created_by INTEGER
)
""")

conn.commit()
conn.close()
print("Database and tables created!")

