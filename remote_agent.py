import pyautogui
import mss
import mss.tools
import os
import sys
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

# Cấu hình ID căn bản
BASE_PROJECT_ID = "antigravity-gui"
ID_FILE = "agent_id.txt"

app = FastAPI()
pyautogui.FAILSAFE = True

class ClickRequest(BaseModel):
    x: int
    y: int

class TypeRequest(BaseModel):
    text: str

class PressRequest(BaseModel):
    key: str

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
    return {"width": width, "height": height, "status": "online"}

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

def get_persistent_id():
    """Lấy ID cố định từ file, nếu không có thì tạo mới"""
    if os.path.exists(ID_FILE):
        with open(ID_FILE, "r") as f:
            return f.read().strip()
    else:
        new_id = f"{BASE_PROJECT_ID}-{socket.gethostname()}-{str(uuid.uuid4())[:4]}"
        with open(ID_FILE, "w") as f:
            f.write(new_id)
        return new_id

FINAL_ID = get_persistent_id()

def add_to_startup():
    """Thêm file EXE vào mục khởi động cùng Windows (Registry)"""
    # Chỉ thực hiện nếu đang chạy dạng file EXE
    if getattr(sys, 'frozen', False):
        exe_path = sys.executable
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, "AntigravityRemoteAgent", 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(key)
            print(f"[AGENT] Added to Startup: {exe_path}")
        except Exception as e:
            print(f"[AGENT] Failed to add to Startup: {e}")

def ensure_cloudflared():
    cf_path = "cloudflared.exe"
    if not os.path.exists(cf_path):
        print("Cloudflared not found. Downloading...")
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
        r = requests.get(url, stream=True)
        with open(cf_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Download complete.")
    return os.path.abspath(cf_path)

def start_tunnel_and_report():
    cf_path = ensure_cloudflared()
    print("Starting Cloudflare Tunnel...")
    
    cmd = [cf_path, "tunnel", "--url", "http://localhost:8000"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    found_url = None
    for line in proc.stdout:
        print(line, end="")
        match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
        if match:
            found_url = match.group(0)
            print(f"\n[AGENT] SUCCESS! Tunnel URL: {found_url}\n")
            
            try:
                requests.post(f"https://ntfy.sh/{FINAL_ID}", 
                             data=f"PC Remote Agent is LIVE at: {found_url}".encode('utf-8'))
                print(f"[AGENT] Reported URL to channel: {FINAL_ID}")
                show_popup(FINAL_ID)
            except Exception as e:
                print(f"Error reporting: {e}")
            break

def show_popup(msg_id):
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("Antigravity Persistent Agent", 
                        f"KẾT NỐI BẤT TỬ THÀNH CÔNG!\n\nMã định danh (Cố định): {msg_id}\n\nMáy tính này sẽ tự động kết nối mỗi khi khởi động.\nHãy gửi mã này cho Antigravity để bắt đầu.")
    root.destroy()

def run_server():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    # Đăng ký khởi động cùng Windows
    add_to_startup()
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    time.sleep(2)
    start_tunnel_and_report()
    
    while True:
        time.sleep(1)
