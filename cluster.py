from flask import Blueprint, request, redirect, url_for, flash, session, render_template
import sqlite3, time
from functools import wraps

cluster_bp = Blueprint("cluster_bp", __name__)

DB_PATH = "proxmox_gui.db"


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrap


def get_vm_ip(vmid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT ipaddr FROM vm_status WHERE vmid=?", (vmid,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None


# ✅ GET route to show page
@cluster_bp.route("/create_cluster", methods=["GET"])
@login_required
def create_cluster_form():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT vmid, vmname, ipaddr FROM vm_status")
    rows = c.fetchall()
    conn.close()

    vms = []
    for r in rows:
        vms.append({
            "vmid": r[0],
            "vmname": r[1],
            "ipaddr": r[2]
        })

    return render_template("create_cluster.html", vms=vms)


# ✅ POST route to save cluster
@cluster_bp.route("/create_cluster", methods=["POST"])
@login_required
def create_cluster():

    cluster_name = request.form.get("cluster_name")
    primary_master = request.form.get("primary_master")
    additional_masters = request.form.getlist("additional_masters[]")
    worker_nodes = request.form.getlist("worker_nodes[]")

    additional_masters = [vm for vm in additional_masters if vm]
    worker_nodes = [vm for vm in worker_nodes if vm]

    if not cluster_name:
        flash("Cluster name required", "danger")
        return redirect(url_for("dashboard"))

    if not primary_master:
        flash("Primary master required", "danger")
        return redirect(url_for("dashboard"))

    if not worker_nodes:
        flash("At least one worker required", "danger")
        return redirect(url_for("dashboard"))

    all_nodes = [primary_master] + additional_masters + worker_nodes
    if len(all_nodes) != len(set(all_nodes)):
        flash("Duplicate VM selection detected", "danger")
        return redirect(url_for("dashboard"))

    primary_ip = get_vm_ip(primary_master)
    additional_ips = [get_vm_ip(vm) for vm in additional_masters]
    worker_ips = [get_vm_ip(vm) for vm in worker_nodes]

    ts = int(time.time())

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS clusters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cluster_name TEXT,
        primary_master TEXT,
        primary_master_ip TEXT,
        additional_masters TEXT,
        additional_master_ips TEXT,
        worker_nodes TEXT,
        worker_ips TEXT,
        created_by TEXT,
        timestamp INTEGER
    )
    """)

    c.execute("""
        INSERT INTO clusters
        (cluster_name, primary_master, primary_master_ip,
         additional_masters, additional_master_ips,
         worker_nodes, worker_ips, created_by, timestamp)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (
        cluster_name,
        primary_master,
        primary_ip,
        ",".join(additional_masters),
        ",".join([ip for ip in additional_ips if ip]),
        ",".join(worker_nodes),
        ",".join([ip for ip in worker_ips if ip]),
        session["username"],
        ts
    ))

    conn.commit()
    conn.close()

    flash(f"Cluster '{cluster_name}' created successfully!", "success")
    return redirect(url_for("dashboard"))

