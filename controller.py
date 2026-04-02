"""
Antigravity Remote Controller V5
- Tự động đọc link tunnel từ GitHub Gist.
- Cache link trong machines.json.
- Cung cấp API điều khiển: screenshot, click, type, press.
"""
import requests
import os
import json
import threading
import time

MACHINES_FILE = "machines.json"

def _load_env():
    gist_id, token = "", ""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("GIST_ID="): gist_id = line.strip().split("=", 1)[1]
                if line.startswith("GITHUB_TOKEN="): token = line.strip().split("=", 1)[1]
    return gist_id, token

GIST_ID, GITHUB_TOKEN = _load_env()


class MachineManager:
    def __init__(self):
        self.machines = {}
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


class GistWatcher:
    """Doc link tunnel tu GitHub Gist"""
    
    def __init__(self, manager):
        self.manager = manager
        self.running = False
    
    def fetch_all(self):
        """Doc tat ca URLs tu Gist"""
        try:
            headers = {
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json"
            }
            r = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=headers, timeout=10)
            if r.status_code == 200:
                content = r.json()["files"]["tunnel_urls.json"]["content"]
                data = json.loads(content)
                for agent_id, info in data.items():
                    url = info.get("url", "")
                    if url:
                        self.manager.update(agent_id, url)
                return data
            else:
                print(f"[ERROR] Gist read failed: {r.status_code}")
                return {}
        except Exception as e:
            print(f"[ERROR] Gist fetch error: {e}")
            return {}
    
    def fetch_one(self, agent_id):
        """Doc URL cua 1 agent cu the"""
        data = self.fetch_all()
        if agent_id in data:
            return data[agent_id].get("url")
        return None
    
    def start_watching(self, interval=30):
        """Polling Gist moi 30 giay de cap nhat link moi"""
        self.running = True
        thread = threading.Thread(target=self._watch_loop, args=(interval,), daemon=True)
        thread.start()
        print(f"[WATCHER] Dang theo doi GitHub Gist moi {interval}s...")
    
    def stop(self):
        self.running = False
    
    def _watch_loop(self, interval):
        while self.running:
            time.sleep(interval)
            try:
                self.fetch_all()
            except:
                pass


class RemoteController:
    def __init__(self, base_url=None, agent_id=None, manager=None):
        self.base_url = base_url.rstrip('/') if base_url else None
        self.agent_id = agent_id
        self.manager = manager
    
    def _get_url(self):
        if self.base_url:
            return self.base_url
        if self.agent_id and self.manager:
            url = self.manager.get_url(self.agent_id)
            if url:
                return url.rstrip('/')
        raise Exception("Khong co URL! May remote chua gui link tunnel.")

    def get_info(self):
        try:
            return requests.get(f"{self._get_url()}/info", timeout=10).json()
        except Exception as e:
            return {"error": str(e)}

    def take_screenshot(self, save_path="remote_screen.png"):
        try:
            response = requests.get(f"{self._get_url()}/screenshot", timeout=15)
            if response.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(response.content)
                return os.path.abspath(save_path)
            return f"Error: {response.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"

    def click(self, x, y):
        try:
            return requests.post(f"{self._get_url()}/click", json={"x": x, "y": y}, timeout=10).json()
        except Exception as e:
            return {"error": str(e)}

    def type_text(self, text):
        try:
            return requests.post(f"{self._get_url()}/type", json={"text": text}, timeout=10).json()
        except Exception as e:
            return {"error": str(e)}

    def press_key(self, key):
        try:
            return requests.post(f"{self._get_url()}/press", json={"key": key}, timeout=10).json()
        except Exception as e:
            return {"error": str(e)}


def connect(agent_id):
    """
    Ket noi den may remote bang agent_id.
    Tu dong doc link tunnel tu GitHub Gist.
    
    Vi du:
        ctrl = connect("antigravity-gui-DESKTOP-OTH6L0T-ee70")
        ctrl.take_screenshot()
        ctrl.click(500, 300)
    """
    manager = MachineManager()
    watcher = GistWatcher(manager)
    
    # Kiem tra link da luu
    saved_url = manager.get_url(agent_id)
    if saved_url:
        print(f"[INFO] Link da luu: {saved_url}")
        try:
            r = requests.get(f"{saved_url}/info", timeout=5)
            if r.status_code == 200:
                print(f"[OK] May dang online!")
                watcher.start_watching()
                return RemoteController(agent_id=agent_id, manager=manager)
        except:
            print(f"[WARN] Link cu het han, dang tim link moi tu GitHub Gist...")
    
    # Doc tu Gist
    print(f"[INFO] Dang doc tu GitHub Gist...")
    new_url = watcher.fetch_one(agent_id)
    if new_url:
        print(f"[OK] Tim thay link: {new_url}")
        # Kiem tra link con song khong
        try:
            r = requests.get(f"{new_url}/info", timeout=5)
            if r.status_code == 200:
                print(f"[OK] May dang online!")
            else:
                print(f"[WARN] Link co nhung may chua online (status: {r.status_code})")
        except:
            print(f"[WARN] Link co nhung may chua online")
    else:
        print(f"[WAIT] Chua co link. Dang cho may remote khoi dong...")
    
    watcher.start_watching()
    return RemoteController(agent_id=agent_id, manager=manager)


def list_machines():
    """Liet ke tat ca cac may da ket noi"""
    manager = MachineManager()
    watcher = GistWatcher(manager)
    data = watcher.fetch_all()
    
    print(f"\n{'='*60}")
    print(f"  Danh sach may remote ({len(data)} may)")
    print(f"{'='*60}")
    for agent_id, info in data.items():
        url = info.get("url", "N/A")
        updated = info.get("updated", "N/A")
        hostname = info.get("hostname", "N/A")
        # Check online
        status = "OFFLINE"
        try:
            r = requests.get(f"{url}/info", timeout=3)
            if r.status_code == 200:
                status = "ONLINE"
        except:
            pass
        print(f"  [{status}] {agent_id}")
        print(f"           Host: {hostname} | Updated: {updated}")
        print(f"           URL: {url}")
        print()
    return data


if __name__ == "__main__":
    print("=" * 50)
    print("  Antigravity Remote Controller V5")
    print("=" * 50)
    print()
    list_machines()
