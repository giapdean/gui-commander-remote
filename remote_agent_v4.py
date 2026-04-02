import sys
import os
import io

# === FIX CRITICAL: Redirect stdout/stderr khi chạy --noconsole ===
# PyInstaller --noconsole gây crash uvicorn/FastAPI vì stdout/stderr = None
# Fix bằng cách redirect sang file log hoặc devnull
if getattr(sys, 'frozen', False):
    # Lấy thư mục chứa file EXE
    exe_dir = os.path.dirname(sys.executable)
    log_file = os.path.join(exe_dir, "agent_log.txt")
    try:
        log_handle = open(log_file, "w", encoding="utf-8", buffering=1)
        sys.stdout = log_handle
        sys.stderr = log_handle
    except Exception:
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()

import pyautogui
import mss
import mss.tools
import subprocess
import requests
import re
import threading
import time
import tkinter as tk
from tkinter import messagebox
import uuid
import socket
import winreg
from fastapi import FastAPI, Response
from pydantic import BaseModel
import uvicorn

# Cấu hình
BASE_PROJECT_ID = "antigravity-gui"
app = FastAPI()
pyautogui.FAILSAFE = True

# === ID Management ===
def get_exe_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

ID_FILE = os.path.join(get_exe_dir(), "agent_id.txt")

def get_persistent_id():
    if os.path.exists(ID_FILE):
        with open(ID_FILE, "r") as f:
            return f.read().strip()
    else:
        new_id = f"{BASE_PROJECT_ID}-{socket.gethostname()}-{str(uuid.uuid4())[:4]}"
        with open(ID_FILE, "w") as f:
            f.write(new_id)
        return new_id

FINAL_ID = get_persistent_id()

# === API Models ===
class ClickRequest(BaseModel):
    x: int
    y: int

class TypeRequest(BaseModel):
    text: str

class PressRequest(BaseModel):
    key: str

# === API Endpoints ===
@app.get("/screenshot")
def get_screenshot():
    with mss.mss() as sct:
        monitor = sct.monitors[0]
        sct_img = sct.grab(monitor)
        img_bytes = mss.tools.to_png(sct_img.rgb, sct_img.size)
        return Response(content=img_bytes, media_type="image/png")

@app.get("/info")
def get_info():
    width, height = pyautogui.size()
    return {"width": width, "height": height, "status": "online", "id": FINAL_ID}

@app.post("/click")
def do_click(req: ClickRequest):
    pyautogui.click(req.x, req.y)
    return {"status": "success", "pos": [req.x, req.y]}

@app.post("/type")
def do_type(req: TypeRequest):
    pyautogui.write(req.text, interval=0.05)
    return {"status": "success"}

@app.post("/press")
def do_press(req: PressRequest):
    pyautogui.press(req.key)
    return {"status": "success", "key": req.key}

# === Helper Functions ===
def log(msg):
    """Safe print that won't crash even if stdout is broken"""
    try:
        print(f"[AGENT] {msg}", flush=True)
    except Exception:
        pass

def report_to_ntfy(message):
    try:
        requests.post(f"https://ntfy.sh/{FINAL_ID}", 
                     data=message.encode('utf-8'),
                     timeout=5)
        log(f"Reported to ntfy: {message}")
    except Exception as e:
        log(f"ntfy failed (not critical): {e}")

def add_to_startup():
    if getattr(sys, 'frozen', False):
        exe_path = sys.executable
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, "AntigravityRemoteAgent", 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(key)
            log(f"Added to Startup: {exe_path}")
        except Exception as e:
            log(f"Failed to add to Startup: {e}")

def ensure_cloudflared():
    cf_path = os.path.join(get_exe_dir(), "cloudflared.exe")
    if not os.path.exists(cf_path):
        log("Downloading cloudflared.exe...")
        report_to_ntfy("Downloading cloudflared.exe...")
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
        try:
            r = requests.get(url, stream=True, timeout=60)
            with open(cf_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            log("Download complete.")
        except Exception as e:
            log(f"Download failed: {e}")
            raise e
    return cf_path

# === Popup (hiển thị link backup) ===
def show_popup(msg_id, url="Đang khởi tạo..."):
    def run_popup():
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo("Antigravity Remote Agent V4", 
                                f"KẾT NỐI THÀNH CÔNG!\n\n"
                                f"Mã ID: {msg_id}\n\n"
                                f"Link điều khiển:\n{url}\n\n"
                                f"Hãy gửi link này cho người điều khiển.")
            root.destroy()
        except Exception:
            pass
    threading.Thread(target=run_popup, daemon=True).start()

# === Tunnel ===
def start_tunnel_and_report():
    try:
        cf_path = ensure_cloudflared()
        log("Starting Cloudflare Tunnel...")
        report_to_ntfy("Starting Cloudflare Tunnel...")
        
        cmd = [cf_path, "tunnel", "--url", "http://localhost:8000"]
        proc = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True, 
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW  # Ẩn cửa sổ cloudflared
        )
        
        found_url = None
        start_time = time.time()
        
        for line in iter(proc.stdout.readline, ""):
            log(line.strip())
            match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
            if match:
                found_url = match.group(0)
                report_to_ntfy(f"CONNECTED! URL: {found_url}")
                show_popup(FINAL_ID, found_url)
                log(f"SUCCESS! Tunnel URL: {found_url}")
                break
            
            if time.time() - start_time > 120:
                report_to_ntfy("Tunnel timeout (2 min)")
                show_popup(FINAL_ID, "TIMEOUT - Không lấy được URL")
                break
                
    except Exception as e:
        log(f"Tunnel error: {e}")
        report_to_ntfy(f"Error: {str(e)}")
        show_popup(FINAL_ID, f"LỖI: {str(e)}")

# === Server ===
def run_server():
    try:
        config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="error")
        server = uvicorn.Server(config)
        server.run()
    except Exception as e:
        log(f"Server error: {e}")

# === Main ===
if __name__ == "__main__":
    log(f"Agent V4 starting... ID: {FINAL_ID}")
    add_to_startup()
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    log("FastAPI server started on port 8000")
    
    time.sleep(2)
    start_tunnel_and_report()
    
    # Keep alive
    while True:
        time.sleep(1)
