# besus

Backend của **SUS (Set-Up System)** trong FVDS: quản lý việc camera nào gửi thông báo cho những email nào.

- `fesus` (Vue) dùng API này để thêm / sửa / xóa cấu hình camera.
- `beaicam` (AI camera) tra cứu theo mã camera để biết cần gửi video, ảnh và thông tin sự kiện tới những email nào.

**Công nghệ:** Python, FastAPI, SQLAlchemy 2, PyMySQL, MySQL.

## Cấu trúc

```
besus/
  app/
    main.py          # khởi tạo FastAPI, CORS, tự tạo bảng khi khởi động
    config.py        # đọc cấu hình DB từ .env
    database.py      # engine, session, Base, get_db
    models/camera.py     # bảng cameras, camera_emails
    schemas/camera.py    # request/response (Pydantic)
    crud/camera.py       # truy vấn DB
    routers/cameras.py   # các endpoint /cameras
  .env.example
  requirements.txt
```

## Yêu cầu

- Python 3.10+
- MySQL đang chạy trên máy

## Cài đặt và chạy

Các lệnh dưới đây chạy trong PowerShell, tại thư mục `fvds/sus/besus`.

1. Tạo database (chỉ làm một lần). App tự tạo bảng khi khởi động nhưng **không** tạo database:

   ```sql
   CREATE DATABASE camera_db;
   ```

2. Tạo file cấu hình rồi sửa user/password MySQL cho đúng với máy bạn:

   ```powershell
   copy .env.example .env
   ```

   | Biến | Mặc định | Ý nghĩa |
   |---|---|---|
   | `DB_HOST` | `localhost` | Địa chỉ MySQL |
   | `DB_PORT` | `3306` | Cổng MySQL |
   | `DB_USER` | `root` | User MySQL |
   | `DB_PASSWORD` | (trống) | Mật khẩu MySQL |
   | `DB_NAME` | `camera_db` | Tên database |

3. Tạo và bật môi trường ảo, cài thư viện:

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

   Nếu PowerShell báo scripts bị chặn, chạy `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` rồi bật venv lại.

4. Chạy server:

   ```powershell
   uvicorn app.main:app --reload
   ```

   Server chạy ở http://localhost:8000, tài liệu API tương tác (Swagger) ở http://localhost:8000/docs.

Lần chạy đầu tiên app tự tạo hai bảng `cameras` và `camera_emails`.

## Mô hình dữ liệu

Một camera có thể gửi thông báo cho nhiều email.

**`cameras`**

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `id` | int, PK, tự tăng | Dùng trong đường dẫn `/cameras/{id}` |
| `code` | varchar(50), unique | Mã camera, không đổi được sau khi tạo |
| `url` | varchar(500) | Địa chỉ luồng camera (http, rtsp, ...) |
| `enabled` | boolean | Mặc định `true` |
| `created_at`, `updated_at` | datetime | Tự cập nhật |

**`camera_emails`**

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `id` | int, PK, tự tăng | |
| `camera_id` | int, FK → `cameras.id` | Xóa camera thì xóa luôn email của nó (`ON DELETE CASCADE`) |
| `email` | varchar(255) | Unique theo cặp `(camera_id, email)` |

## API

| Method | Đường dẫn | Mục đích | Kết quả |
|---|---|---|---|
| POST | `/cameras` | Tạo camera | 201; 409 nếu `code` đã tồn tại |
| GET | `/cameras` | Danh sách camera (`skip`, `limit`, mặc định 0 và 100) | 200 |
| GET | `/cameras/{id}` | Lấy camera theo `id` | 200; 404 |
| GET | `/cameras/by-code/{code}` | Lấy camera theo `code` (dành cho aicam) | 200; 404 |
| PUT | `/cameras/{id}` | Cập nhật camera | 200; 404 |
| DELETE | `/cameras/{id}` | Xóa camera | 204; 404 |

Dữ liệu sai định dạng (email không hợp lệ, danh sách email rỗng, ...) trả về 422.

### Body của POST và PUT

```json
{
  "code": "cam-living-room",
  "emails": ["son@example.com", "daughter@example.com"],
  "url": "rtsp://192.168.1.10:554/stream",
  "enabled": true
}
```

- `PUT` không nhận `code`, chỉ nhận `emails`, `url`, `enabled`.
- `emails`: từ 1 đến 20 địa chỉ. Địa chỉ trùng nhau (không phân biệt hoa thường) tự được bỏ bớt. Khi `PUT`, danh sách này **thay thế toàn bộ** danh sách email hiện có.
- Khoảng trắng đầu/cuối của các chuỗi được tự cắt bỏ.

### Response

```json
{
  "id": 1,
  "code": "cam-living-room",
  "emails": ["son@example.com", "daughter@example.com"],
  "url": "rtsp://192.168.1.10:554/stream",
  "enabled": true,
  "created_at": "2026-10-09T08:53:23",
  "updated_at": "2026-10-09T08:53:23"
}
```

### Dành cho aicam

Khi phát hiện sự kiện, gọi `GET /cameras/by-code/{code}` để lấy danh sách `emails`. Endpoint này trả về cả camera có `enabled = false`, nên phía gọi cần tự kiểm tra `enabled` trước khi gửi thông báo.

### Lưu ý

- `{id}` trong đường dẫn là `id` số của database, không phải `code`. Frontend dùng `id` lấy từ danh sách để gọi `PUT` và `DELETE`.
- CORS đang cho phép `http://localhost:5173` và `http://127.0.0.1:5173` (Vite dev server của fesus). Muốn thêm origin khác thì sửa trong `app/main.py`.
- API hiện chưa có xác thực.
