from flask import Flask, Response, render_template, request, flash, redirect, url_for
import os
import subprocess
import re
from werkzeug.utils import secure_filename
from threading import Timer
import argparse

SSL = False
VERSION = subprocess.run('cat /root/WallController/version', shell=True, check=True, stdout=subprocess.PIPE, universal_newlines=True).stdout

DHCP_STATIC = "selected = \"selected\""
#NIC = "apcli0"
NIC = "eth0"

#INTERFACE = "wwan"
INTERFACE = "wan"

HOSTNAME = "WallController"
output = subprocess.run('ifconfig '+ NIC, shell=True, check=True, stdout=subprocess.PIPE, universal_newlines=True).stdout
#output = process.stdout

IP = re.search("addr:\d*.\d*.\d*.\d*",output).group(0)[5:]
SN = re.search("Mask:\d*.\d*.\d*.\d*",output).group(0)[5:]
output = subprocess.run('ip r', shell=True, check=True, stdout=subprocess.PIPE, universal_newlines=True).stdout
#output = process.stdout
GW = re.search("via \d*.\d*.\d*.\d*",output).group(0)[4:]
print(IP,SN,GW)

output = subprocess.run('cat /etc/config/network', shell=True, check=True, stdout=subprocess.PIPE, universal_newlines=True).stdout
lines = output.split('\n\n')
print(len(lines))
for line in lines:
    if re.search(INTERFACE,line) != None:
        sublines = line.split('\n')
        for subline in sublines:
            if re.search("option proto 'dhcp'",subline):
                pass
                DHCP_STATIC = ""


app = Flask(__name__, template_folder="/root/Webserver/templates")
app.config['UPLOAD_FOLDER'] = "/tmp"


def reboot_system():
    print("Triggering Reboot")
    subprocess.run("reboot")

def update_firmware():
    print("updating firmware")
    subprocess.run(["sysupgrade","/tmp/openwrt-ramips-mt76x8-onion_omega2p-squashfs-sysupgrade.bin"])

ALLOWED_EXTENSIONS = {"bin"}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/firmware', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            print("no file")
            return "No File",200
        file = request.files['file']
        if not allowed_file(file.filename):
            print("invalid file format")
            return "Invalid File Format",200
        if file.filename != 'openwrt-ramips-mt76x8-onion_omega2p-squashfs-sysupgrade.bin':
            print("Invaild File")
            return "Invalid File",200
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            t = Timer(5.0, update_firmware)
            t.start()
            return "Upload Successful, Updating and Rebooting Device\n Do not disconnect Power!",200 #redirect(url_for('download_file', name=filename))
    return "invalid",404

@app.route("/reboot", methods=["POST"])
def reboot():
    t = Timer(5.0, reboot_system)
    t.start()
    return "Device is Rebooting", 200

@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "GET":
        return render_template("index.html", IP=IP, SN=SN, GW=GW, DHCP_STATIC = DHCP_STATIC, VERSION = VERSION)
    else:
        return "what are you doing?"

@app.before_request #redirect to https 
def before_request():
    if not request.is_secure and SSL:
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)
        

@app.route("/network_settings", methods=["POST"])
def set_network():
    global NIC
    global INTERFACE    
    if request.method == "POST":
        new_settings = request.get_json()
        output_file = ""
        for line in lines:
            if re.search("'"+INTERFACE+"'",line):
                new_iface = ""
                if new_settings["mode"] == "static":
                    pass
                    new_iface = f"config interface '{INTERFACE}'\n\toption ifname '{NIC}'\n\toption proto 'static'\n\toption hostname '{HOSTNAME}'"
                    new_iface += f"\n\toption ipaddr '{new_settings['ip']}'\n\toption netmask '{new_settings['subnet']}'\n\toption gateway '{new_settings['gateway']}'\n"
                else:
                    new_iface = f"config interface '{INTERFACE}'\n\toption ifname '{NIC}'\n\toption proto 'dhcp'\n\toption hostname '{HOSTNAME}'"
                output_file += "\n" + new_iface + "\n\n"
            else:
                output_file += "\n" + line + "\n\n"
        file = open("/etc/config/network","w")
        file.write(output_file)    
        file.close()
        t = Timer(5.0, reboot_system)
        t.start()
        return "Network Settings Changed. Device will reboot now"

if __name__ == '__main__':

    ap = argparse.ArgumentParser()
    ap.add_argument("--http", type=bool, default=False,
                    help="use HTTP 80 instead of HTTPS 443")
    args = ap.parse_args()

    if not args.http:
        SSL = True
        app.run(host="0.0.0.0", port=443, debug=False,
                threaded=True, use_reloader=False,ssl_context='adhoc')
    else:
        SSL = False
        app.run(host="0.0.0.0", port=80, debug=False,
                threaded=True, use_reloader=False)
