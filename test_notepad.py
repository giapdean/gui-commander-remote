import pyautogui
import time
import os
import sys

# Thêm đường dẫn để import agent nếu cần, hoặc copy các hàm cần thiết
# Ở đây tôi sẽ viết trực tiếp để đảm bảo tính độc lập cho bài test

def run_trial():
    print("Starting Notepad trial...")
    
    # 1. Nhấn phím Windows
    pyautogui.press('win')
    time.sleep(1)
    
    # 2. Gõ tìm kiếm notepad
    pyautogui.write('notepad', interval=0.1)
    time.sleep(1)
    
    # 3. Nhấn Enter để mở
    pyautogui.press('enter')
    time.sleep(2) # Chờ Notepad mở hẳn
    
    # 4. Gõ nội dung
    text = "Hello from Antigravity! \nToi dang dieu khien may tinh cua ban y nhu mot con nguoi thuc thu.\nCam on ban da tin tuong!"
    pyautogui.write(text, interval=0.05)
    
    print("Đã gõ xong văn bản.")
    time.sleep(1)

if __name__ == "__main__":
    run_trial()
