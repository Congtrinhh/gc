# set-up-send-noti — backend (fvds/sus/besus)

Mục đích: map camera → danh sách email để beaicam biết gửi thông báo cho ai khi phát hiện té ngã/bạo lực.

## Stack & cấu trúc
FastAPI + SQLAlchemy 2 + PyMySQL. `app/{config,database,main}.py`, `models/`, `schemas/`, `crud/`, `routers/cameras.py`. Cấu hình DB qua `.env` (xem `.env.example`). Bảng tạo bằng `Base.metadata.create_all` khi khởi động (database `camera_db` phải tạo tay; `create_all` chỉ tạo bảng còn thiếu, không sửa bảng đã có nên đổi cấu trúc bảng sau này phải ALTER tay hoặc dùng migration). Hướng dẫn cài đặt/chạy đầy đủ nằm trong `besus/README.md`.

## Bảng
- `cameras`: `id` (PK, auto), `code` (unique, ≤50, = "camera id" trong diagram), `url` (≤500, str để nhận rtsp://), `enabled` (default true), `created_at`, `updated_at`.
- `camera_emails`: `id`, `camera_id` (FK → cameras.id, ON DELETE CASCADE), `email` (≤255), unique `(camera_id, email)`. Quan hệ 1 camera – nhiều email; `Camera.emails` là property trả `list[str]`.

## Endpoint
- `POST /cameras` — `code, emails, url, enabled` → 201; 409 nếu trùng `code` (check trước + bắt `IntegrityError` khi race).
- `GET /cameras` (`skip`, `limit`), `GET /cameras/{id}`.
- `GET /cameras/by-code/{code}` — cho aicam tra email theo mã camera; trả cả camera `enabled=false` (phía gọi tự kiểm tra `enabled`); 404 nếu không có.
- `PUT /cameras/{id}` — `emails, url, enabled`; `emails` thay toàn bộ danh sách (update theo diff: giữ email cũ còn lại, chỉ xóa/thêm phần chênh để không vướng unique). Không đổi `code`.
- `DELETE /cameras/{id}` — 204, xóa luôn email liên quan.

`emails`: 1–20 phần tử, dedupe không phân biệt hoa thường (giữ bản đầu tiên). Schema strip whitespace. `{id}` = id số của DB, không phải `code`.

## Việc còn mở
- Chưa có test tự động (đã smoke test tay bằng SQLite in-memory: create/dup/422/by-code/update/delete+cascade đều đúng; chưa chạy trên MySQL thật).
- Chưa có xác thực cho API (aicam và fesus đều gọi tự do).
