import requests
import os

class RemoteController:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')

    def get_info(self):
        try:
            return requests.get(f"{self.base_url}/info").json()
        except Exception as e:
            return {"error": str(e)}

    def take_screenshot(self, save_path="remote_screen.png"):
        """Lấy ảnh màn hình từ PC 2 và lưu lại PC 1"""
        try:
            print(f"Bắt đầu lấy ảnh từ {self.base_url}...")
            response = requests.get(f"{self.base_url}/screenshot", timeout=10)
            if response.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(response.content)
                return os.path.abspath(save_path)
            else:
                return f"Error: {response.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"

    def click(self, x, y):
        """Gửi lệnh click tọa độ x, y cho PC 2"""
        try:
            return requests.post(f"{self.base_url}/click", json={"x": x, "y": y}).json()
        except Exception as e:
            return {"error": str(e)}

    def type_text(self, text):
        """Gửi lệnh gõ văn bản cho PC 2"""
        try:
            return requests.post(f"{self.base_url}/type", json={"text": text}).json()
        except Exception as e:
            return {"error": str(e)}

    def press_key(self, key):
        """Gửi lệnh nhấn phím cho PC 2"""
        try:
            return requests.post(f"{self.base_url}/press", json={"key": key}).json()
        except Exception as e:
            return {"error": str(e)}

if __name__ == "__main__":
    # Ví dụ hướng dẫn sử dụng
    print("Remote Controller script is ready.")
    print("Usage: controller = RemoteController('http://IP_OF_PC2:8000')")
