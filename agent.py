import pyautogui
import mss
import mss.tools
import os
from PIL import Image

# Thiết lập an toàn cho PyAutoGUI (Dừng lại khi di chuyển chuột vào góc trái trên màn hình)
pyautogui.FAILSAFE = True

def take_screenshot(filename="screenshot.png"):
    """Chụp ảnh màn hình và lưu lại"""
    with mss.mss() as sct:
        # Chụp toàn màn hình
        monitor = sct.monitors[0]  # monitor 0 là toàn bộ màn hình (all-in-one)
        sct_img = sct.grab(monitor)
        # Chuyển đổi sang file ảnh để tôi có thể xem được
        mss.tools.to_png(sct_img.rgb, sct_img.size, output=filename)
    return os.path.abspath(filename)

def get_screen_info():
    """Lấy thông tin kích thước màn hình"""
    width, height = pyautogui.size()
    return {"width": width, "height": height}

def click(x, y):
    """Click chuột tại tọa độ x, y"""
    pyautogui.click(x, y)

def type_text(text):
    """Gõ văn bản"""
    pyautogui.write(text, interval=0.1)

def press_key(key):
    """Nhấn một phím"""
    pyautogui.press(key)

if __name__ == "__main__":
    # Test nhanh khi chạy trực tiếp
    print(f"Screen size: {get_screen_info()}")
    path = take_screenshot("test_screen.png")
    print(f"Screenshot saved at: {path}")
