StackFlow Virtualization Manager (SVM)

StackFlow Virtualization Manager (SVM) is a Flask-based web portal for provisioning, managing, and automating Proxmox Virtual Machines using Ansible.

It provides a clean web interface for VM lifecycle management, user control, and background automation.

🚀 Overview

SVM enables:

VM creation (new or from template)

Automatic clone generation

Role-based user management

Live SSH status monitoring

Background Ansible execution

Dynamic inventory generation

Live Ansible console logs

CSV export of VM inventory

🖥 Dashboard Features

The dashboard provides:

VM Management Table

VM ID

VM Name

IP Address

Target Node

SSH Port

SSH Status (ONLINE / OFFLINE / UNKNOWN)

Timestamp

Created By

Edit / Delete actions

Advanced Table Features

Multi-column search filtering

Pagination

Dynamic rows per page (10 / 20 / 50 / 100)

Status badges with color indicators

Admin Panel

(Admin users only)

Create user

Modify user

Add VM record manually

Delete VM

View user list

Download inventory (CSV)

🔐 Authentication & Roles
Roles

Admin

Create / modify users

Delete VM records

Add manual VM entries

Full visibility

User

Create VMs

Edit VMs

Run Ansible roles

View dashboard

Security

Passwords hashed using Werkzeug

Session-based authentication

Role-based route protection

SSH key authentication for Ansible

⚙ VM Provisioning
Base VM Options

New VM

Template-based VM

Configurable Parameters

Storage

Image

Target Node

VM ID

VM Name

Memory

CPU Cores

Disk Size

IP (CIDR)

Gateway

VLAN ID

SSH Port

🔁 Clone Automation Logic

When clones are selected:

VM IDs auto-increment

IP addresses auto-increment

Supports manual override for first clone (template mode)

Dynamic clone form generation

Separate memory / cores / disk per clone

🧠 Edit VM & Ansible Role Execution

Edit VM page allows:

Update VM metadata

Change disk size (no shrinking allowed)

Define cluster settings

Set master IP

Add unlimited dynamic variables

Select multiple Ansible roles

Background execution per role

Auto-refreshing log console

Extra Variables

Users can dynamically add:
...
variable_name = value
...

These are passed to the Ansible inventory.

📡 Background Services
1️⃣ SSH Status Monitor

Runs every 5 seconds:

Checks socket connectivity

Updates status as:

ONLINE

OFFLINE

UNKNOWN

2️⃣ Playbook Executor

Runs in background thread

Stores execution logs

Log viewer supports tail view

3️⃣ Role Execution Engine

Generates dynamic inventory per VM

Runs selected roles asynchronously

Writes logs per VM

🗂 Project Structure

.
├── app.py
├── vm_edit.py
├── db.py
├── proxmox_gui.db
├── templates/
│   ├── dashboard.html
│   ├── form.html
│   ├── edit_vm.html
│   ├── login.html
│   ├── create_user.html
│   └── modify_user.html
├── proxmox_vm/
│   ├── tests/test.yml
│   └── inventory
├── /tmp/proxmox_logs/
├── /tmp/ansible_logs/
└── /tmp/ansible_inventory/


🗄 Database Schema
users
Field	Type
id	INTEGER
username	TEXT (unique)
email	TEXT
password	TEXT (hashed)
role	TEXT
vm_status
Field	Description
vmid	Primary Key
vmname	VM name
ipaddr	IP/CIDR
target_node	Proxmox node
ssh_port	SSH port
ssh_status	ONLINE/OFFLINE
disksize	Disk size
cluster_name	Cluster
master_ip	Master IP
extra_vars	JSON
timestamp	Creation time
created_by	Username
🧰 Requirements

Python 3.8+

Flask

Werkzeug

SQLite

Ansible

Linux (recommended)

Install Python dependencies:
pip install flask werkzeug
Verify Ansible:

⚙ Configuration
Update Paths in app.py

Update Paths in vm_edit.py

ANSIBLE_PLAYBOOK = "/home/<user>/.local/bin/ansible-playbook"
ROLES_PATH = "/home/<user>/ansible/roles"
SSH_KEY = "/home/<user>/.ssh/id_ed25519"


🎯 Summary

StackFlow Virtualization Manager (SVM) is a lightweight but powerful automation portal combining:

Flask + Ansible + Proxmox + SQLite

It provides VM provisioning, monitoring, automation, and user management in a single integrated web interface.
