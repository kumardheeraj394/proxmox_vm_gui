import sqlite3
import time

DB_PATH = "/home/dheeraj/proxmox_vm_gui/proxmox_gui.db"
NOW = int(time.time())

records = [
#    (113, "Zulu-RabbitMQ-M1", "10.0.25.151/22", "pve59"),
#    (114, "Zulu-RabbitMQ-M2", "10.0.25.152/22", "pve51"),
#    (115, "Zulu-RabbitMQ-M3", "10.0.25.153/22", "pve54"),
#    (116, "Zulu-RabbitMQ-W1", "10.0.25.154/22", "pve55"),
#    (117, "Zulu-RabbitMQ-W2", "10.0.25.155/22", "pve56"),
#    (118, "Zulu-RabbitMQ-W3", "10.0.25.156/22", "pve57"),
#    (119, "Zulu-MySQL-M1", "10.0.25.121/22", "pve58"),
#    (120, "Zulu-MySQL-M2", "10.0.25.122/22", "pve59"),
#    (121, "Zulu-MySQL-M3", "10.0.25.123/22", "pve51"),
    (122, "Zulu-Kafka", "10.0.25.127/22", "pve58"),    
]

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

for vmid, vmname, ipaddr, target_node in records:
    c.execute("""
        INSERT OR REPLACE INTO vm_status
        (vmid, vmname, ipaddr, target_node, ssh_port,
         ssh_status, timestamp, created_by)
        VALUES (?,?,?,?,?,?,?,?)
    """, (
        str(vmid),
        vmname,
        ipaddr,
        target_node.lower(),
        10457,                 # default SSH port
        "ONLINE",          # status will update automatically
        NOW,
        "bhaskar"
    ))

conn.commit()
conn.close()

print("✅ Manual VM records added successfully")

