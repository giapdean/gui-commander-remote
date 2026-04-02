"""
Antigravity Remote Controller V4
- Tự động lắng nghe ntfy.sh để nhận link tunnel mới từ các máy remote.
- Lưu trữ danh sách máy và link hiện tại.
- Cung cấp API điều khiển: screenshot, click, type, press.
"""
import requests
import os
import json
import threading
import time
import re

MACHINES_FILE = "machines.json"

class MachineManager:
    """Quản lý danh sách các máy remote và link tunnel hiện tại"""
    
    def __init__(self):
        self.machines = {}  # {agent_id: {"url": "...", "last_seen": "..."}}
        self.load()
    
    def load(self):
        if os.path.exists(MACHINES_FILE):
            with open(MACHINES_FILE, "r", encoding="utf-8") as f:
                self.machines = json.load(f)
    
    def save(self):
        with open(MACHINES_FILE, "w", encoding="utf-8") as f:
            json.dump(self.machines, f, indent=2, ensure_ascii=False)
    
    def update(self, agent_id, url):
        self.machines[agent_id] = {
            "url": url,
            "last_seen": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.save()
        print(f"[UPDATED] {agent_id} -> {url}")
    
    def get_url(self, agent_id):
        if agent_id in self.machines:
            return self.machines[agent_id]["url"]
        return None
    
    def list_all(self):
        return self.machines


class NtfyListener:
    """Lắng nghe ntfy.sh để tự động nhận link tunnel mới"""
    
    def __init__(self, agent_id, manager):
        self.agent_id = agent_id
        self.manager = manager
        self.running = False
    
    def start(self):
        self.running = True
        thread = threading.Thread(target=self._listen, daemon=True)
        thread.start()
        print(f"[LISTENER] Đang lắng nghe ntfy.sh/{self.agent_id}...")
    
    def stop(self):
        self.running = False
    
    def _listen(self):
        """Long-polling ntfy.sh để nhận tin nhắn real-time"""
        while self.running:
            try:
                # SSE stream - tự động nhận tin nhắn mới
                response = requests.get(
                    f"https://ntfy.sh/{self.agent_id}/json",
                    stream=True,
                    timeout=90,
                    headers={"Accept": "application/x-ndjson"}
                )
                for line in response.iter_lines(decode_unicode=True):
                    if not self.running:
                        break
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        if data.get("event") == "message":
                            message = data.get("message", "")
                            print(f"[NTFY] Nhận: {message}")
                            # Tự động trích xuất URL tunnel
                            match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", message)
                            if match:
                                new_url = match.group(0)
                                self.manager.update(self.agent_id, new_url)
                    except json.JSONDecodeError:
                        pass
            except requests.exceptions.Timeout:
                # Timeout bình thường, reconnect
                continue
            except Exception as e:
                print(f"[LISTENER] Lỗi: {e}, thử lại sau 5s...")
                time.sleep(5)
    
    def check_once(self):
        """Kiểm tra 1 lần (poll) để lấy tin nhắn gần nhất"""
        try:
            response = requests.get(
                f"https://ntfy.sh/{self.agent_id}/json?poll=1",
                timeout=10
            )
            latest_url = None
            for line in response.text.strip().split("\n"):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if data.get("event") == "message":
                        message = data.get("message", "")
                        match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", message)
                        if match:
                            latest_url = match.group(0)
                except json.JSONDecodeError:
                    pass
            if latest_url:
                self.manager.update(self.agent_id, latest_url)
                return latest_url
            return None
        except Exception as e:
            print(f"[ERROR] Poll failed: {e}")
            return None


class RemoteController:
    """Điều khiển máy remote qua tunnel URL"""
    
    def __init__(self, base_url=None, agent_id=None, manager=None):
        self.base_url = base_url.rstrip('/') if base_url else None
        self.agent_id = agent_id
        self.manager = manager
    
    def _get_url(self):
        """Lấy URL hiện tại: ưu tiên base_url, nếu không thì lấy từ manager"""
        if self.base_url:
            return self.base_url
        if self.agent_id and self.manager:
            url = self.manager.get_url(self.agent_id)
            if url:
                return url.rstrip('/')
        raise Exception("Không có URL! Hãy chờ máy remote gửi link tunnel.")

    def get_info(self):
        try:
            url = self._get_url()
            return requests.get(f"{url}/info", timeout=10).json()
        except Exception as e:
            return {"error": str(e)}

    def take_screenshot(self, save_path="remote_screen.png"):
        try:
            url = self._get_url()
            response = requests.get(f"{url}/screenshot", timeout=15)
            if response.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(response.content)
                return os.path.abspath(save_path)
            else:
                return f"Error: {response.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"

    def click(self, x, y):
        try:
            url = self._get_url()
            return requests.post(f"{url}/click", json={"x": x, "y": y}, timeout=10).json()
        except Exception as e:
            return {"error": str(e)}

    def type_text(self, text):
        try:
            url = self._get_url()
            return requests.post(f"{url}/type", json={"text": text}, timeout=10).json()
        except Exception as e:
            return {"error": str(e)}

    def press_key(self, key):
        try:
            url = self._get_url()
            return requests.post(f"{url}/press", json={"key": key}, timeout=10).json()
        except Exception as e:
            return {"error": str(e)}


# === Hàm tiện ích để dùng nhanh ===

def connect(agent_id):
    """
    Kết nối đến máy remote bằng agent_id.
    Tự động lắng nghe ntfy.sh để nhận link tunnel.
    
    Ví dụ:
        ctrl = connect("antigravity-gui-DESKTOP-OTH6L0T-ee70")
        ctrl.take_screenshot()
        ctrl.click(500, 300)
    """
    manager = MachineManager()
    listener = NtfyListener(agent_id, manager)
    
    # Kiểm tra link đã lưu
    saved_url = manager.get_url(agent_id)
    if saved_url:
        print(f"[INFO] Link đã lưu: {saved_url}")
        # Kiểm tra link còn sống không
        try:
            r = requests.get(f"{saved_url}/info", timeout=5)
            if r.status_code == 200:
                print(f"[OK] Máy đang online!")
                listener.start()  # Vẫn lắng nghe để cập nhật link mới
                return RemoteController(agent_id=agent_id, manager=manager)
        except:
            print(f"[WARN] Link cũ đã hết hạn, đang tìm link mới...")
    
    # Poll ntfy để lấy link mới nhất
    print(f"[INFO] Đang kiểm tra ntfy.sh/{agent_id}...")
    new_url = listener.check_once()
    if new_url:
        print(f"[OK] Tìm thấy link: {new_url}")
    else:
        print(f"[WAIT] Chưa có link. Đang lắng nghe... (chờ máy remote khởi động)")
    
    # Bật listener chạy nền
    listener.start()
    return RemoteController(agent_id=agent_id, manager=manager)


if __name__ == "__main__":
    print("=" * 50)
    print("  Antigravity Remote Controller V4")
    print("=" * 50)
    print()
    print("Cách dùng:")
    print('  from controller import connect')
    print('  ctrl = connect("antigravity-gui-DESKTOP-xxx-xxxx")')
    print('  ctrl.take_screenshot("screen.png")')
    print('  ctrl.click(500, 300)')
    print('  ctrl.type_text("Hello")')
    print('  ctrl.press_key("enter")')
