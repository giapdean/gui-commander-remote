# GUI Commander - Remote AI Control

Dự án này cho phép điều khiển máy tính từ xa (GUI Automation) thông qua một AI Assistant (Antigravity).

## ✨ Tính năng chính
- **Zero-Touch Setup**: Tự động tải `cloudflared`, tự thiết lập Tunnel Internet.
- **Persistent Access**: Tự động ghi nhớ ID và khởi động cùng Windows.
- **Human-like Control**: Điều khiển chuột, bàn phím y như con người.
- **Unique Identification**: Mỗi máy tính có mã định danh riêng để đảm bảo an toàn.

## 🚀 Cách sử dụng (Dành cho Máy bị điều khiển)
1. Tải file `remote_agent.exe` từ thư mục `dist/`.
2. Chạy file (Nhấp đúp chuột).
3. Copy **Mã định danh** hiện lên màn hình và gửi cho Antigravity.

## 🛠️ Cấu trúc dự án
- `remote_agent.py`: Script chạy trên máy mục tiêu (Target PC).
- `controller.py`: Thư viện điều khiển dành cho AI (Controller Side).
- `requirements.txt`: Các thư viện cần thiết.

## ⚠️ Lưu ý bảo mật
Hãy chỉ chia sẻ Mã định danh cho người mà bạn tin tưởng vì họ sẽ có quyền điều khiển chuột/bàn phím trên máy tính của bạn.
