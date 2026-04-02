import sys
import os
import io

# === FIX: Redirect stdout/stderr khi chạy --noconsole ===
if getattr(sys, 'frozen', False):
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
import json
import base64
from fastapi import FastAPI, Response
from pydantic import BaseModel
import uvicorn

# === CẤU HÌNH ===
BASE_PROJECT_ID = "antigravity-gui"

def _load_config():
    """Load config from config.json next to exe, or from .env"""
    cfg_path = os.path.join(get_exe_dir(), "config.json")
    if os.path.exists(cfg_path):
        with open(cfg_path, "r") as f:
            cfg = json.load(f)
        return cfg.get("gist_id", ""), base64.b64decode(cfg.get("token_b64", "")).decode()
    # Fallback: read from .env
    env_path = os.path.join(get_exe_dir(), ".env")
    gist_id, token = "", ""
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("GIST_ID="): gist_id = line.strip().split("=", 1)[1]
                if line.startswith("GITHUB_TOKEN="): token = line.strip().split("=", 1)[1]
    return gist_id, token

def get_exe_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

GIST_ID, GITHUB_TOKEN = _load_config()

app = FastAPI()
pyautogui.FAILSAFE = True

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
    try:
        print(f"[AGENT] {msg}", flush=True)
    except Exception:
        pass

def report_url_to_gist(tunnel_url):
    """Ghi link tunnel vào GitHub Gist để Máy 1 tự động đọc"""
    try:
        # Đọc Gist hiện tại
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        r = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=headers, timeout=10)
        
        if r.status_code == 200:
            current_data = {}
            try:
                current_content = r.json()["files"]["tunnel_urls.json"]["content"]
                current_data = json.loads(current_content)
            except:
                current_data = {}
            
            # Cập nhật link cho agent này
            current_data[FINAL_ID] = {
                "url": tunnel_url,
                "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
                "hostname": socket.gethostname()
            }
            
            # Ghi lại Gist
            update_data = {
                "files": {
                    "tunnel_urls.json": {
                        "content": json.dumps(current_data, indent=2, ensure_ascii=False)
                    }
                }
            }
            r2 = requests.patch(
                f"https://api.github.com/gists/{GIST_ID}",
                headers=headers,
                json=update_data,
                timeout=10
            )
            if r2.status_code == 200:
                log(f"URL reported to GitHub Gist OK!")
            else:
                log(f"Gist update failed: {r2.status_code}")
        else:
            log(f"Gist read failed: {r.status_code}")
    except Exception as e:
        log(f"Gist error: {e}")

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

# === Popup ===
def show_popup(msg_id, url="Dang khoi tao..."):
    def run_popup():
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo("Antigravity Remote Agent V5",
                                f"KET NOI THANH CONG!\n\n"
                                f"Ma ID: {msg_id}\n\n"
                                f"Link dieu khien:\n{url}\n\n"
                                f"Link da duoc tu dong gui len GitHub.")
            root.destroy()
        except Exception:
            pass
    threading.Thread(target=run_popup, daemon=True).start()

# === Tunnel ===
def start_tunnel_and_report():
    try:
        cf_path = ensure_cloudflared()
        log("Starting Cloudflare Tunnel...")
        
        cmd = [cf_path, "tunnel", "--url", "http://localhost:8000"]
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        start_time = time.time()
        
        for line in iter(proc.stdout.readline, ""):
            log(line.strip())
            match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
            if match:
                found_url = match.group(0)
                log(f"Tunnel URL: {found_url}")
                
                # Gửi link lên GitHub Gist (thay thế ntfy.sh)
                report_url_to_gist(found_url)
                
                show_popup(FINAL_ID, found_url)
                break
            
            if time.time() - start_time > 120:
                show_popup(FINAL_ID, "TIMEOUT")
                break
                
    except Exception as e:
        log(f"Tunnel error: {e}")
        show_popup(FINAL_ID, f"ERROR: {str(e)}")

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
    log(f"Agent V5 starting... ID: {FINAL_ID}")
    add_to_startup()
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    log("FastAPI server started on port 8000")
    
    time.sleep(2)
    start_tunnel_and_report()
    
    while True:
        time.sleep(1)
