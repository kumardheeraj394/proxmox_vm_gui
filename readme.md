# 🚀 Proxmox VM GUI (SVM)

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

---
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
---


---

## 🧩 Installation

### Requirements

- Python 3.8+
- Flask
- Ansible
- Proxmox VE host/API access
- `gunicorn` for production deployment

### Python Dependencies

```bash
pip install flask gunicorn
```
🔐 Login

Visit:

```
http://<server-ip>:8000/login
```
