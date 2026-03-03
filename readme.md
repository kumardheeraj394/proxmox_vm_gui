📁 Project Structure
---
```
├── app.py                  # Main Flask application
├── vm_edit.py              # VM edit + role execution blueprint
├── db.py                   # Database helper
├── proxmox_gui.db          # SQLite DB (auto-created)
├── templates/              # HTML UI templates
│   ├── dashboard.html
│   ├── form.html
│   ├── edit_vm.html
│   ├── login.html
│   ├── create_user.html
│   └── modify_user.html
├── proxmox_vm/             # Ansible playbook + inventory
├── /tmp/proxmox_logs/      # Playbook logs
├── /tmp/ansible_logs/      # Role execution logs
└── /tmp/ansible_inventory/ # Generated inventories
```

# 🚀 Proxmox VM GUI (SVM)
---
Proxmox VM GUI (StackFlow Virtualization Manager) is a lightweight web interface to manage virtual machines on a Proxmox VE infrastructure using Flask and Ansible.

This project provides an easy way to:
- Create VMs from templates
- Clone VMs with auto IP/VMID logic
- Execute Ansible playbooks for post-provisioning tasks
- View VM SSH status and logs

---

## 📌 Features

- **Web-based VM creation UI**
- **Automatic VM ID and IP generation**
- **Clone multiple VMs from a template**
- **Ansible playbook integration**
- **SSH status monitoring**
- **Manual addition & editing of VM records**

---

## 🧠 Architecture

Your Flask application:
- Renders UI for login, dashboard, and VM form
- Processes form submissions
- Writes Ansible variable files
- Executes Ansible playbooks in the background
- Stores VM metadata in SQLite database

```
User (Browser)
↓
Flask Web UI
↓
Writes vars JSON
↓
Runs Ansible Playbook
↓
Proxmox VE API
↓
VM Provisioned / Cloned
```


## 🧩 Installation
---

### Requirements

- Python 3.8+
- Flask
- Ansible
- Proxmox VE host/API access
- `gunicorn` for production deployment

### Python Dependencies
---

```bash
pip install flask gunicorn
```
🔐 Login

Visit:

```
http://<server-ip>:8000/login
```

###🖥 VM Lifecycle Management
---
Create VM (New or Template)

Automatic Clone Generation

Edit VM configuration

Disk expansion validation (no shrinking)

Manual VM record addition

Delete VM (Admin only)

CSV Inventory Export

###⚙ Automation (Ansible Integration)
---
Background playbook execution

Dynamic inventory generation

Multi-role execution per VM

Per-VM log storage

Live log console (auto-refresh)

###📡 Monitoring
---
Background SSH status checker

Status updates every 5 seconds

Status indicators:

🟢 ONLINE

🔴 OFFLINE

⚪UNKNOWN

🛠 Installation
---
1. Clone the Repository
```
git clone https://github.com/kumardheeraj394/proxmox_vm_gui.git
cd proxmox_vm_gui
```
2. Install Python Dependencies

Make sure you have Python 3.8+ installed.

Create a virtual environment (recommended):
```
python3 -m venv venv
source venv/bin/activate
```

3. Setup Database

The app uses SQLite. On the first run, it will automatically create:

users table

vm_status table

No manual setup is required.

To add an admin user:

```
from werkzeug.security import generate_password_hash
import sqlite3

conn = sqlite3.connect("proxmox_gui.db")
c = conn.cursor()
c.execute("""
INSERT INTO users (username, email, password, role)
VALUES (?, ?, ?, ?)
""", ("admin", "admin@example.com", generate_password_hash("YourPassword"), "admin"))
conn.commit()
conn.close()
```
4. Configure Paths

The app expects:

```
LOGS_DIR = "/tmp/proxmox_logs"
DISCOVER_JSON = "/tmp/proxmox_discover.json"
PLAYBOOK_PATH = "proxmox_vm/tests/test.yml"
INVENTORY_PATH = "proxmox_vm/tests/inventory"
```
Ensure these paths exist and are writable. The logs directory will store playbook execution logs.

5. Install Ansible (Required)
Ensure ansible-playbook is installed and accessible. Adjust the path in app.py if needed:

6. Run the Application

7. Optional: Prepopulate DISCOVER_JSON

The vm form fetches nodes, storage, and images from /tmp/proxmox_discover.json. Example structure:

```
{
  "nodes": ["pve57", "pve51"],
  "storage": ["local-lvm", "ISO"],
  "images": ["ubuntu-22.04-server-cloudimg-amd64.img"],
  "next_vmid": 1000
}
```
This setup will allow your Flask GUI to manage VMs and run Ansible playbooks automatically.
