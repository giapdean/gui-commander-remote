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
- `remote_agent_v2.py`: Phiên bản mới nhất (khuyên dùng), hỗ trợ báo cáo trạng thái chi tiết qua ntfy.sh.
- `remote_agent.py`: Phiên bản cơ bản.
- `controller.py`: Thư viện điều khiển dành cho AI (Controller Side).
- `requirements.txt`: Các thư viện cần thiết.
- `test_ntfy.py`: Công cụ kiểm tra kết nối ntfy.sh.

## ⚠️ Lưu ý bảo mật
Hãy chỉ chia sẻ Mã định danh cho người mà bạn tin tưởng vì họ sẽ có quyền điều khiển chuột/bàn phím trên máy tính của bạn.
