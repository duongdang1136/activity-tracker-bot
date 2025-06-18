**Generated markdown**

```
# Bot Tracking Activity & Management

Hệ thống bot đa nền tảng (Discord, Zalo) để theo dõi hoạt động thành viên, tính điểm, và tự động quản lý nhóm. Dữ liệu được lưu trữ trên Supabase và có API để hiển thị leaderboard trên web.

## Cấu trúc dự án

Dự án được xây dựng theo kiến trúc phân lớp:

- **`config/`**: Quản lý cấu hình và kết nối database.
- **`api/`**: Giao tiếp với các API bên ngoài (Zalo, Discord).
- **`services/`**: Chứa toàn bộ logic nghiệp vụ.
- **`bot/`**: Các listener lắng nghe sự kiện từ các nền tảng chat.
- **`web/`**: API server (Flask) để cung cấp dữ liệu cho frontend.
- **`logs/`**: Nơi lưu trữ file log (đã được ignore bởi Git).

## Hướng dẫn cài đặt

1. Clone repository:
   ```bash
   git clone <URL_repository_của_bạn>
   cd activity-bot-project
```

**content_copy**download

Use code [with caution](https://support.google.com/legal/answer/13505487).**Markdown**

* **Tạo và kích hoạt môi trường ảo:**

  Generated bash

  ```
  python -m venv venv
  source venv/bin/activate  # Trên macOS/Linux
  .\venv\Scripts\activate   # Trên Windows
  ```

  **content_copy**download

  Use code [with caution](https://support.google.com/legal/answer/13505487).**Bash**
* **Cài đặt các thư viện cần thiết:**

  Generated bash

  ```
  pip install -r requirements.txt
  ```

  **content_copy**download

  Use code [with caution](https://support.google.com/legal/answer/13505487).**Bash**
* **Tạo file** **.env** **từ file** **.env.example** **(bạn nên tạo file này) và điền các thông tin cần thiết (Supabase URL/Key, Bot tokens,...).**
* **Chạy ứng dụng:**

  Generated bash

  ```
  python main.py
  ```
