#!/usr/bin/env python3
import time
import socket
from db import get_db

CHECK_INTERVAL = 10

def ssh_up(ipaddr, port, timeout=2):
    try:
        host = ipaddr.split("/")[0]
        with socket.create_connection((host, int(port)), timeout):
            return True
    except:
        return False

def update_vm_status():
    while True:
        conn = None
        try:
            conn = get_db()
            c = conn.cursor()

            c.execute("SELECT vmid, ipaddr, ssh_port FROM vm_status")
            rows = c.fetchall()

            for vmid, ipaddr, ssh_port in rows:
                status = "ONLINE" if ssh_up(ipaddr, ssh_port) else "OFFLINE"
                c.execute(
                    "UPDATE vm_status SET ssh_status=? WHERE vmid=?",
                    (status, vmid)
                )

        except Exception as e:
            print(f"[VM STATUS ERROR] {e}")

        finally:
            if conn:
                conn.close()

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    update_vm_status()

