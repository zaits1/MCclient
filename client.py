import shutil
import tempfile
import time

import socket
import tkinter as tk
import threading
import os
from tkinter import messagebox

import requests  # Requires `pip install requests` if not already installed
import sys

CLIENT_VERSION = "1.0.3"  # Update this on each release
UPDATE_URL = "https://raw.githubusercontent.com/zaits1/MCclient/main/client.py"
VERSION_URL = "https://raw.githubusercontent.com/zaits1/MCclient/main/version.txt"

SERVER_IP = "84.229.9.85"  # Change this to the server's actual IP
CONTROL_PORT = 25566 # Must match the port in `server_control.py`
listen_thread = None

def listen_for_broadcasts():
    """Listen for broadcast messages from the server."""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((SERVER_IP, CONTROL_PORT))
        while True:
            message = client.recv(1024).decode()
            if("Users" in message):
                users_status.config(text=message, fg="black")
            else:
                lbl_status.config(text=message, fg="green" if "started" in message or "running" in message else "red")
    except (socket.timeout, ConnectionRefusedError):
        lbl_status.config(text="Server not reachable", fg="red")
        listening = False

def send_command(command):
    """Send a command to the server (start/stop)."""
    global listen_thread
    try:
        if listen_thread is None or not listen_thread.is_alive():
            start_listen_to_user_changes()
            time.sleep(1)
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(2)
        lbl_status.config(text="Connecting...", fg="orange")
        client.connect((SERVER_IP, CONTROL_PORT))
        client.sendall(command.encode())

        response = client.recv(1024).decode()
        client.close()
        if("Users" not in response):
            lbl_status.config(text=response, fg="green" if "started" in response or "running" in response else "red")
    except (socket.timeout, ConnectionRefusedError):
        lbl_status.config(text="Server not reachable", fg="red")

def start_server():
    send_command("start")

def stop_server():
    send_command("stop")

def start_listen_to_user_changes():
    global listen_thread
    listen_thread = threading.Thread(target=listen_for_broadcasts)
    listen_thread.daemon = True
    listen_thread.start()

app = tk.Tk()
app.title("Server Control Client")
app.geometry("300x200")


users_status = tk.Label(app, text="Users: 0", fg="black", font=("Arial", 12))
users_status.pack(pady=10)

lbl_status = tk.Label(app, text="Checking server...", fg="orange", font=("Arial", 12))
lbl_status.pack(pady=10)

btn_start = tk.Button(app, text="Start Server", command=start_server)
btn_start.pack(pady=10)

btn_stop = tk.Button(app, text="Stop Server", command=stop_server)
btn_stop.pack(pady=10)

def check_for_update():
    try:
        # Check for latest version
        response = requests.get(VERSION_URL, timeout=3)
        latest_version = response.text.strip()

        if latest_version > CLIENT_VERSION:
            # Update available
            lbl_status.config(text="Updating...", fg="orange")

            # Get the new version of the script
            update_response = requests.get(UPDATE_URL, timeout=5)

            # Save the updated script to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.py') as temp_file:
                temp_file.write(update_response.content)
                temp_script_path = temp_file.name

            # Inform the user about the update
            lbl_status.config(text="Updated to latest version", fg="green")
            time.sleep(1)

            # Close the GUI window or perform any cleanup
            # Replace the old executable with the new one
            exe_path = sys.executable

            # Perform the update: move the new version to the original exe path
            shutil.move(temp_script_path, exe_path)

            # Restart the executable with the updated script
            os.execv(exe_path, ['python'] + sys.argv)  # Restart the script
    except Exception as e:
        print(f"Update check failed: {e}")
        messagebox.showerror("Error", "Update failed. Please try again later.")

check_for_update()

start_listen_to_user_changes()  # Run the check when the client starts

app.mainloop()
