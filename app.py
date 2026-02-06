from flask import (
    Flask, render_template, request, jsonify,
    redirect, url_for, session, flash, send_file
)
import os, json, time, socket, threading, subprocess, sqlite3, csv, io
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db

# ================= CONFIG =================
app = Flask(__name__)
app.secret_key = "supersecretkey"

DB_PATH = "proxmox_gui.db"
LOGS_DIR = "/tmp/proxmox_logs"
DISCOVER_JSON = "/tmp/proxmox_discover.json"
PLAYBOOK_PATH = "proxmox_vm/tests/test.yml"
INVENTORY_PATH = "proxmox_vm/tests/inventory"

os.makedirs(LOGS_DIR, exist_ok=True)

# ================= DB INIT =================
def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT,
        password TEXT,
        role TEXT DEFAULT 'user'
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS vm_status (
        vmid TEXT PRIMARY KEY,
        vmname TEXT,
        ipaddr TEXT,
        target_node TEXT,
        ssh_port INTEGER,
        ssh_status TEXT,
        timestamp INTEGER,
        created_by TEXT
    )
    """)
    conn.commit()
    conn.close()
init_db()

# ================= HELPERS =================
def ssh_up(ipaddr, port, timeout=2):
    try:
        host = ipaddr.split("/")[0]
        with socket.create_connection((host, int(port)), timeout):
            return True
    except:
        return False

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrap

def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Admin only", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return wrap

# ================= AUTH =================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT password, role FROM users WHERE username=?", (u,))
        row = c.fetchone()
        conn.close()
        if row and check_password_hash(row[0], p):
            session["username"] = u
            session["role"] = row[1]
            return redirect(url_for("dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ================= DASHBOARD =================
@app.route("/dashboard")
@login_required
def dashboard():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    offset = (page-1)*per_page

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM vm_status")
    total_vms = c.fetchone()[0]

    c.execute(f"""
        SELECT vmid, vmname, ipaddr, target_node,
               ssh_port, ssh_status, timestamp, created_by
        FROM vm_status
        ORDER BY timestamp DESC
        LIMIT {per_page} OFFSET {offset}
    """)
    rows = c.fetchall()

    users = []
    if session["role"] == "admin":
        c.execute("SELECT username, email, role FROM users")
        users = c.fetchall()

    conn.close()

    vms = []
    for r in rows:
        vms.append({
            "vmid": r[0],
            "vmname": r[1],
            "ipaddr": r[2],
            "target_node": r[3],
            "ssh_port": r[4],
            "ssh_status": r[5],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(r[6])),
            "created_by": r[7]
        })

    total_pages = (total_vms + per_page - 1) // per_page

    return render_template(
        "dashboard.html",
        vms=vms,
        users=users,
        role=session["role"],
        username=session["username"],
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )

# ================= CREATE / MODIFY USER =================
@app.route("/create_user", methods=["GET","POST"])
@login_required
@admin_required
def create_user():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form.get("email","")
        role = request.form.get("role","user")
        password = generate_password_hash(request.form["password"])
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("INSERT INTO users (username,email,password,role) VALUES (?,?,?,?)",
                      (username,email,password,role))
            conn.commit()
            conn.close()
            flash("User created", "success")
            return redirect(url_for("dashboard"))
        except sqlite3.IntegrityError:
            flash("Username already exists", "danger")
    return render_template("create_user.html")

@app.route("/modify_user/<username>", methods=["GET","POST"])
@login_required
@admin_required
def modify_user(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if request.method == "POST":
        email = request.form["email"]
        role = request.form["role"]
        password = request.form.get("password")
        if password:
            hashed = generate_password_hash(password)
            c.execute("UPDATE users SET email=?, role=?, password=? WHERE username=?",
                      (email, role, hashed, username))
        else:
            c.execute("UPDATE users SET email=?, role=? WHERE username=?",
                      (email, role, username))
        conn.commit()
        conn.close()
        flash("User updated", "success")
        return redirect(url_for("dashboard"))

    c.execute("SELECT username, email, role FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    return render_template("modify_user.html", user=user)

# ================= CHANGE OWN PASSWORD =================
@app.route("/change_password", methods=["GET","POST"])
@login_required
def change_password():
    if request.method=="POST":
        old = request.form["old_password"]
        new = request.form["new_password"]
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username=?", (session["username"],))
        row = c.fetchone()
        if row and check_password_hash(row[0], old):
            c.execute("UPDATE users SET password=? WHERE username=?",
                      (generate_password_hash(new), session["username"]))
            conn.commit()
            flash("Password updated","success")
        else:
            flash("Old password incorrect","danger")
        conn.close()
    return render_template("change_password.html")

# ================= VM FORM =================
@app.route("/vm")
@login_required
def vm_form():
    data = {"nodes":[], "storage":[], "images":[]}
    if os.path.exists(DISCOVER_JSON):
        with open(DISCOVER_JSON) as f:
            data = json.load(f)
    return render_template(
        "form.html",
        nodes=data.get("nodes",[]),
        storage=data.get("storage",[]),
        images=data.get("images",[]),
        ssh_port=10457
    )

# ================= RUN PLAYBOOK =================
@app.route("/run", methods=["POST"])
@login_required
def run():
    payload = request.json
    ts = int(time.time())
    vars_file = f"proxmox_{ts}.json"
    vars_path = os.path.join(LOGS_DIR, vars_file)

    # Save payload for Ansible
    with open(vars_path, "w") as f:
        json.dump(payload, f, indent=2)

    # Start Ansible in background
    threading.Thread(target=run_playbook, args=(vars_path,), daemon=True).start()

    # Insert base VM and clones into DB immediately
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Base VM
    c.execute("""
        INSERT OR REPLACE INTO vm_status
        (vmid, vmname, ipaddr, target_node, ssh_port, ssh_status, timestamp, created_by)
        VALUES (?,?,?,?,?,?,?,?)
    """, (
        payload["vmid"],
        payload["vmname"],
        payload["ipaddr"],
        payload["target_node"],
        payload["ssh_port"],
        "UNKNOWN",
        ts,
        session["username"]
    ))

    # Clones
    for clone in payload.get("clones", []):
        c.execute("""
            INSERT OR REPLACE INTO vm_status
            (vmid, vmname, ipaddr, target_node, ssh_port, ssh_status, timestamp, created_by)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            clone["clonevmid"],
            clone["clonevmname"],
            clone["cloneipaddr"],
            clone["clonetarget_node"],
            clone.get("ssh_port", payload["ssh_port"]),
            "UNKNOWN",
            ts,
            session["username"]
        ))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok", "vars_file": vars_file})

def run_playbook(vars_path):
    """
    Executes the Ansible playbook with the given vars file.
    Logs all output to a .log file in LOGS_DIR.
    """
    log_path = vars_path.replace(".json", ".log")
    cmd = [
        "/home/dheeraj/.local/bin/ansible-playbook",
        PLAYBOOK_PATH,
        "-i", INVENTORY_PATH,
        "--extra-vars", f"@{vars_path}"
    ]

    with open(log_path, "w") as log:
        try:
            p = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            for line in p.stdout:
                log.write(line)
                log.flush()
            p.wait()
        except Exception as e:
            log.write(f"\nERROR executing playbook: {e}\n")
            log.flush()

# ================= BACKGROUND VM STATUS UPDATER =================
def update_vm_status():
    """
    Background thread to periodically check VM SSH connectivity
    and update the database.
    """
    while True:
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT vmid, ipaddr, ssh_port FROM vm_status")
            rows = c.fetchall()
            for vmid, ipaddr, ssh_port in rows:
                status = "ONLINE" if ssh_up(ipaddr, ssh_port) else "OFFLINE"
                c.execute("UPDATE vm_status SET ssh_status=? WHERE vmid=?", (status, vmid))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[VM STATUS ERROR] {e}")
        time.sleep(5)  # check every 5 seconds

# ================= LOG TAIL =================
@app.route("/log/<vars_file>")
@login_required
def view_log(vars_file):
    lines = int(request.args.get("lines", 100))
    log_path = os.path.join(LOGS_DIR, vars_file.replace(".json",".log"))

    if not os.path.exists(log_path):
        return jsonify({"log": "Log not available yet"})

    with open(log_path) as f:
        content = f.readlines()[-lines:]

    return jsonify({"log": "".join(content)})

# ================= ADD VM MANUALLY =================
@app.route("/add_vm", methods=["POST"])
@login_required
def add_vm():
    payload = request.form
    ts = int(time.time())
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO vm_status
        (vmid, vmname, ipaddr, target_node, ssh_port, ssh_status, timestamp, created_by)
        VALUES (?,?,?,?,?,?,?,?)
    """, (
        payload["vmid"], payload["vmname"], payload["ipaddr"],
        payload["target_node"], payload["ssh_port"], "UNKNOWN",
        ts, session["username"]
    ))
    conn.commit()
    conn.close()
    flash("VM added manually","success")
    return redirect(url_for("dashboard"))

# ================= DELETE VM =================
@app.route("/delete_vm/<vmid>")
@login_required
@admin_required
def delete_vm(vmid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM vm_status WHERE vmid=?", (vmid,))
    conn.commit()
    conn.close()
    flash("VM deleted", "success")
    return redirect(url_for("dashboard"))

# ================= DOWNLOAD INVENTORY =================
@app.route("/download_inventory")
@login_required
def download_inventory():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT vmid, vmname, ipaddr, target_node, ssh_port, ssh_status, timestamp, created_by FROM vm_status")
    rows = c.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["VM ID","VM Name","IP","Target Node","SSH Port","SSH Status","Timestamp","Created By"])
    for r in rows:
        writer.writerow(r)
    output.seek(0)

    return send_file(io.BytesIO(output.getvalue().encode()),
                     mimetype="text/csv",
                     as_attachment=True,
                     download_name="vm_inventory.csv")

# ================= START BACKGROUND THREADS =================
# Start the VM status updater thread immediately when app is imported
if os.environ.get("RUN_MAIN") != "true":
    threading.Thread(
        target=update_vm_status,
        daemon=True
    ).start()
# ================= MAIN =================
if __name__ == "__main__":
    # Only used when running directly with python3 app.py
    app.run(host="0.0.0.0", port=8000, debug=True)

