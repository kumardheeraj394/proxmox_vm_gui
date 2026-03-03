from flask import Blueprint, render_template, request, redirect, url_for, flash
import sqlite3
import os
import subprocess
import threading
import json

vm_edit_bp = Blueprint("vm_edit", __name__)

DB_PATH = "proxmox_gui.db"

ANSIBLE_PLAYBOOK = "/home/dheeraj/.local/bin/ansible-playbook"
ROLES_PATH = "/home/dheeraj/ansible/roles"

ANSIBLE_USER = "ubuntu"
SSH_KEY = "/home/dheeraj/.ssh/id_ed25519"

LOG_DIR = "/tmp/ansible_logs"
INV_DIR = "/tmp/ansible_inventory"

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(INV_DIR, exist_ok=True)


# =====================================================
# Generate Inventory
# =====================================================
def generate_inventory(
        vmid,
        ipaddr,
        ssh_port,
        role,
        disksize,
        cluster_name,
        master_ip,
        extra_vars):

    inv_path = f"{INV_DIR}/{vmid}_{role}_inventory"
    clean_ip = ipaddr.split("/")[0].strip()

    with open(inv_path, "w") as f:

        f.write(f"[{role}]\n")
        f.write(
            f"{clean_ip} "
            f"ansible_user={ANSIBLE_USER} "
            f"ansible_port={ssh_port} "
            f"ansible_ssh_private_key_file={SSH_KEY} "
            f"ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'\n\n"
        )

        f.write(f"[{role}:vars]\n")
        f.write(f"vmid={vmid}\n")
        f.write(f"disksize={disksize}\n")
        f.write(f"cluster_name={cluster_name}\n")
        f.write(f"master_ip={master_ip}\n")

        # Write dynamic extra vars
        for key, value in extra_vars.items():
            f.write(f"{key}={value}\n")

    return inv_path


# =====================================================
# Run Ansible
# =====================================================
def run_ansible_background(vmid, role, inventory_path):

    logfile = f"{LOG_DIR}/{vmid}.log"
    playbook_path = f"{role}/tests/test.yml"

    cmd = [
        ANSIBLE_PLAYBOOK,
        playbook_path,
        "-i",
        inventory_path
    ]

    with open(logfile, "a") as log:
        subprocess.Popen(
            cmd,
            cwd=ROLES_PATH,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True
        ).wait()


# =====================================================
# Edit VM Route
# =====================================================
@vm_edit_bp.route("/edit_vm/<vmid>", methods=["GET", "POST"])
def edit_vm(vmid):

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        SELECT vmid, vmname, ipaddr, target_node,
               ssh_port, disksize,
               cluster_name, master_ip,
               extra_vars
        FROM vm_status
        WHERE vmid = ?
    """, (vmid,))
    row = c.fetchone()

    if not row:
        conn.close()
        return "VM not found", 404

    extra_vars_loaded = json.loads(row[8]) if row[8] else {}

    vm = {
        "vmid": row[0],
        "vmname": row[1],
        "ipaddr": row[2],
        "target_node": row[3],
        "ssh_port": row[4],
        "disksize": row[5] if row[5] else 20,
        "cluster_name": row[6] if row[6] else "",
        "master_ip": row[7] if row[7] else "",
        "extra_vars": extra_vars_loaded
    }

    if request.method == "POST":

        vmname = request.form["vmname"]
        ipaddr = request.form["ipaddr"]
        ssh_port = request.form["ssh_port"]
        target_node = request.form["target_node"]
        disksize = int(request.form.get("disksize", 20))
        cluster_name = request.form.get("cluster_name", "")
        master_ip = request.form.get("master_ip", "")
        selected_roles = request.form.getlist("ansible_roles")

        # ========= Collect Extra Vars =========
        var_names = request.form.getlist("var_name[]")
        var_values = request.form.getlist("var_value[]")

        extra_vars = {}
        for name, value in zip(var_names, var_values):
            if name.strip():
                extra_vars[name.strip()] = value.strip()

        extra_vars_json = json.dumps(extra_vars)

        current_size = int(vm["disksize"])

        if disksize < current_size:
            flash("Disk shrinking is not allowed in Proxmox", "danger")
            conn.close()
            return redirect(url_for("vm_edit.edit_vm", vmid=vmid))

        # ========= Update DB =========
        c.execute("""
            UPDATE vm_status
            SET vmname=?,
                ipaddr=?,
                target_node=?,
                ssh_port=?,
                disksize=?,
                cluster_name=?,
                master_ip=?,
                extra_vars=?
            WHERE vmid=?
        """, (
            vmname,
            ipaddr,
            target_node,
            ssh_port,
            disksize,
            cluster_name,
            master_ip,
            extra_vars_json,
            vmid
        ))

        conn.commit()
        conn.close()

        # Clear log
        logfile = f"{LOG_DIR}/{vmid}.log"
        open(logfile, "w").close()

        # ========= Run Roles =========
        for role in selected_roles:

            inventory_path = generate_inventory(
                vmid,
                ipaddr,
                ssh_port,
                role,
                disksize,
                cluster_name,
                master_ip,
                extra_vars
            )

            thread = threading.Thread(
                target=run_ansible_background,
                args=(vmid, role, inventory_path),
                daemon=True
            )
            thread.start()

        flash("VM updated & Ansible started", "success")
        return redirect(url_for("vm_edit.edit_vm", vmid=vmid))

    conn.close()

    roles = []
    if os.path.exists(ROLES_PATH):
        roles = [
            d for d in os.listdir(ROLES_PATH)
            if os.path.isdir(os.path.join(ROLES_PATH, d))
        ]

    return render_template("edit_vm.html", vm=vm, roles=roles)


# =====================================================
# Log Viewer
# =====================================================
@vm_edit_bp.route("/ansible_log/<vmid>")
def ansible_log(vmid):

    logfile = f"{LOG_DIR}/{vmid}.log"

    if not os.path.exists(logfile):
        return "No logs yet..."

    with open(logfile) as f:
        return f.read()
