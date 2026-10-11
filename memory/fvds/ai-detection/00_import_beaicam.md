# ai-detection — đưa beaicam vào monorepo (fvds/aicam/beaicam)

Nguồn: repo riêng `khanhlong247/Fall-And-Violent-Detection-System`, commit `f1fa27e` cộng các thay đổi chưa commit lúc copy (chế độ local `USE_CLOUD_STORAGE`, fallback codec `mp4v`, `docs/`). Copy `app/`, `docs/`, `requirements.txt`, `README.md`; không copy `.venv`, `.env`, `data/`, `models/`, `credentials/`.

## Thay đổi so với repo gốc
- `.gitignore` riêng (bỏ qua `.env`, `.venv`, `/data`, `/models`, `/credentials`) và `.env.example` mặc định chế độ local.
- `app/core/config.py`: URL nhận sự kiện mặc định đổi từ một ngrok bên ngoài sang mock local `localhost:9001/9002`.
- README: chạy ở port **8001** (8000 là besus), hướng dẫn `cp .env.example .env`.
- Model không commit (`best.pt` 6MB, MoveNet `.bin` 19MB); lệnh tải ở README mục 0.3.

## Đã kiểm chứng
Chạy local bằng Python 3.10, `person_walk.mp4` (139s, 10fps): `/health` OK, `POST /api/v1/analysis/video` mất ~4 phút trên CPU, ra 7 clip violence (báo nhầm do model YOLO công khai), mock server nhận 7 notification. Log `h264_v4l2m2m ... Failed to initialize VideoWriter` là bình thường: `avc1` không có nên fallback sang `mp4v`.

## Việc còn mở (bước tiếp theo)
- Nối với besus: request chưa có `camera_code`; `EventNotifier._to_camera_id` lấy tên file đổi ra số, không phải số thì mặc định camera 5. Cần tra `GET /cameras/by-code/{code}`, kiểm tra `enabled`, không tra được thì không gửi.
- Chưa có gửi email (chỉ POST tới events API). Chỉ nên gửi sau khi clip đã upload.
- `analysis_orchestrator.py`: `all_frames_cache` giữ mọi frame (hết RAM với video dài/stream); stream chạy đồng bộ trong request và chỉ thông báo khi stream kết thúc; model chạy 2 lần mỗi frame (`annotate_frame` + `detect`); model nạp lại mỗi request.
- Lần thông báo sau khi có clip dùng `entity_id = "<type>_clip_final"`, mất `track_id`.
