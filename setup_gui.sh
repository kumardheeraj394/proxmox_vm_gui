#!/bin/bash
set -e

# 1️⃣ Update and install Python3 and pip if not installed
echo "Installing Python3 and pip..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv

# 2️⃣ Create a project directory
PROJECT_DIR="$HOME/proxmox_vm_gui"
mkdir -p "$PROJECT_DIR/templates"
cd "$PROJECT_DIR"

# 3️⃣ Set up Python virtual environment
echo "Setting up virtual environment..."
python3 -m venv venv
source venv/bin/activate

# 4️⃣ Install Flask
echo "Installing Flask..."
pip install --upgrade pip
pip install Flask PyYAML

# 5️⃣ Create Flask app.py
cat > app.py << 'EOF'
from flask import Flask, render_template, request
import yaml
import subprocess

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = {
            "vmid": int(request.form["vmid"]),
            "vmname": request.form["vmname"],
            "memory": int(request.form["memory"]),
            "cores": int(request.form["cores"]),
            "storage": request.form["storage"],
            "vlan_id": request.form["vlan_id"],
            "image": request.form["image"],
            "ipaddr": request.form["ipaddr"],
            "gateway": request.form["gateway"],
            "ssh_port": int(request.form["ssh_port"]),
            "disksize": int(request.form["disksize"]),
            "ciuser": "ubuntu",
            "cipassword": "Admin@112233",
            "clones": []
        }

        clone_count = int(request.form.get("clone_count", 0))
        for i in range(1, clone_count + 1):
            clone = {
                "vmid": int(request.form[f"clone_vmid_{i}"]),
                "vmname": request.form[f"clone_name_{i}"],
                "ipaddr": request.form[f"clone_ip_{i}"],
                "memory": int(request.form.get(f"clone_memory_{i}", 4096)),
                "cores": int(request.form.get(f"clone_cores_{i}", 2)),
                "disksize": int(request.form.get(f"clone_disksize_{i}", 20))
            }
            data["clones"].append(clone)

        with open("vars.yml", "w") as f:
            yaml.dump(data, f)

        # Run Ansible playbook
        subprocess.run([
            "ansible-playbook",
            "proxmox_vm/tests/test.yml",
            "-i",
            "proxmox_vm/tests/inventory",
            "-e",
            "@vars.yml"
        ])

        return "Playbook executed successfully!"

    return render_template("form.html")
EOF

# 6️⃣ Create HTML template
cat > templates/form.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Proxmox VM GUI</title>
<style>
    body { font-family: Arial; margin: 20px; }
    input, select { margin: 5px 0; padding: 5px; width: 300px; }
    .clone { border: 1px solid #ccc; padding: 10px; margin: 10px 0; }
</style>
<script>
function generateClones() {
    let container = document.getElementById('clones-container');
    container.innerHTML = '';
    let count = parseInt(document.getElementById('clone_count').value);
    for (let i = 1; i <= count; i++) {
        let div = document.createElement('div');
        div.className = 'clone';
        div.innerHTML = `
            <h4>Clone ${i}</h4>
            VMID: <input type="number" name="clone_vmid_${i}" required><br>
            Name: <input type="text" name="clone_name_${i}" required><br>
            IP (CIDR): <input type="text" name="clone_ip_${i}" required><br>
            Memory (MB): <input type="number" name="clone_memory_${i}" value="4096"><br>
            CPU cores: <input type="number" name="clone_cores_${i}" value="2"><br>
            Additional Disk (GB): <input type="number" name="clone_disksize_${i}" value="20"><br>
        `;
        container.appendChild(div);
    }
}
</script>
</head>
<body>
<h2>Proxmox VM Creator</h2>
<form method="post">
    VMID: <input type="number" name="vmid" required><br>
    VM Name: <input type="text" name="vmname" value="ubuntu-ci"><br>
    Memory (MB): <input type="number" name="memory" value="4096"><br>
    CPU cores: <input type="number" name="cores" value="2"><br>
    Storage: <input type="text" name="storage" value="local-lvm"><br>
    VLAN ID: <input type="text" name="vlan_id" value="0"><br>
    Image: <input type="text" name="image" value="ubuntu-22.04.iso"><br>
    IP Address (CIDR): <input type="text" name="ipaddr" required><br>
    Gateway: <input type="text" name="gateway" value="10.10.10.1"><br>
    SSH Port: <input type="number" name="ssh_port" value="22"><br>
    Disk Size (GB): <input type="number" name="disksize" value="20"><br><br>

    Number of Clones: <input type="number" id="clone_count" name="clone_count" value="0" onchange="generateClones()"><br>
    <div id="clones-container"></div>

    <button type="submit">Create VM(s)</button>
</form>
</body>
</html>
EOF

echo "Setup complete!"
echo "To start the GUI:"
echo "1. cd $PROJECT_DIR"
echo "2. source venv/bin/activate"
echo "3. flask run"
