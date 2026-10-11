# beaicam: Fall Detection + Violent Detection

Dịch vụ AI lõi của FVDS (Guardian Care), nằm tại `fvds/aicam/beaicam`. Mọi lệnh bên dưới chạy trong thư mục này. Server chạy ở port **8001** (port 8000 dành cho `besus`).

Backend FastAPI hỗ trợ phân tích video và stream realtime để phát hiện:

- **Té ngã (Fall Detection)**
- **Bạo lực / đánh nhau (Violent Detection)**

Hệ thống được thiết kế theo hướng backend AI độc lập, có thể tích hợp với web frontend, camera system, hoặc các dịch vụ backend khác.

---

# 0. Quickstart: Chạy Local (Dev/Demo, không cần Google Drive / AWS S3)

Phần này dành cho việc dựng nhanh backend trên máy cá nhân để test/demo, không cần tài khoản Google Drive hay AWS. Muốn dùng cloud thật (production) thì xem tiếp mục 9 và mục 12.

## 0.1 Yêu cầu

- Python 3.10 (khuyến nghị dùng [uv](https://github.com/astral-sh/uv) để tự tải đúng bản Python và quản lý venv, không bắt buộc dùng Python hệ thống).
- CPU là đủ, không cần GPU (các model mặc định chạy CPU: OpenVINO `device=CPU`, YOLO `device=cpu`).

## 0.2 Tạo virtual environment và cài dependencies

```bash
uv venv .venv --python 3.10
source .venv/bin/activate      # Windows: .venv\Scripts\activate
uv pip install -p .venv -r requirements.txt
```

Nếu không có `uv`, dùng cách thông thường:

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 0.3 Tải model

Model **không** nằm trong repo (bị `.gitignore`), phải tải/đặt thủ công vào thư mục `models/`.

**Fall Detection — MoveNet Multipose Lightning (OpenVINO IR):**

```bash
mkdir -p models
curl -fSL -o models/movenet_multipose_lightning_256x256_FP32.xml \
  https://raw.githubusercontent.com/geaxgx/openvino_movenet_multipose/main/models/movenet_multipose_lightning_256x256_FP32.xml
curl -fSL -o models/movenet_multipose_lightning_256x256_FP32.bin \
  https://raw.githubusercontent.com/geaxgx/openvino_movenet_multipose/main/models/movenet_multipose_lightning_256x256_FP32.bin
```

Nguồn: [geaxgx/openvino_movenet_multipose](https://github.com/geaxgx/openvino_movenet_multipose) (model gốc từ TensorFlow Hub, được PINTO convert sang OpenVINO IR).

**Violent Detection — YOLOv8:**

Nếu bạn đã có `best.pt` tự train (khuyến nghị dùng bản này vì độ chính xác cao hơn nhiều), chỉ cần copy vào `models/best.pt`.

Nếu **chưa có** model riêng, có thể dùng tạm một model YOLOv8-nano huấn luyện sẵn công khai để test luồng xử lý:

```bash
curl -fSL -o models/best.pt \
  "https://huggingface.co/Musawer14/fight_detection_yolov8/resolve/main/Yolo_nano_weights.pt"
```

⚠️ Model thay thế này **không** phải model tự train cho hệ thống, chỉ có 2 lớp `violence` / `non_violence`, độ chính xác không cao và có thể báo nhầm (false positive) trên các video không liên quan (ví dụ người đi bộ bình thường). Chỉ dùng để kiểm tra pipeline chạy được, cần thay bằng model tự train khi triển khai thật.

## 0.4 Tạo file `.env` cho chế độ local

Copy file mẫu (đã đặt sẵn chế độ local, không cần Google Drive/AWS):

```bash
cp .env.example .env
```

Các biến tối thiểu cho chế độ local:

```
USE_CLOUD_STORAGE=false
LOCAL_INPUT_VIDEOS_DIR=./data/input_videos

FALL_MODEL_XML=./models/movenet_multipose_lightning_256x256_FP32.xml
FALL_DEVICE=CPU
VIOLENCE_MODEL_PT=./models/best.pt
VIOLENCE_DEVICE=cpu

FALL_EVENT_API_URL=http://localhost:9001/fall-events
VIOLENCE_EVENT_API_URL=http://localhost:9002/violence-events

DEFAULT_PRE_EVENT_SECONDS=3
DEFAULT_POST_EVENT_SECONDS=5
```

`USE_CLOUD_STORAGE=false` là cờ quan trọng nhất: khi tắt, backend **không** khởi tạo Google Drive/S3 client (nên không cần OAuth credentials hay AWS key), video được đọc trực tiếp từ thư mục local, và clip sự kiện chỉ được lưu local (không upload đi đâu).

## 0.5 Đặt video test và chạy server

```bash
mkdir -p data/input_videos
cp /đường/dẫn/video_cua_ban.mp4 data/input_videos/test.mp4

uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

Kiểm tra:

- Health check: `curl http://localhost:8001/health`
- Swagger UI: `http://localhost:8001/docs`

## 0.6 Gọi thử API với video local

```bash
curl -X POST http://localhost:8001/api/v1/analysis/video \
  -H "Content-Type: application/json" \
  -d '{
    "video_name": "test.mp4",
    "run_fall_detection": true,
    "run_violence_detection": true,
    "pre_event_seconds": 3,
    "post_event_seconds": 5
  }'
```

`video_name` ở chế độ local là tên file (hoặc đường dẫn) bên trong `LOCAL_INPUT_VIDEOS_DIR`, **không phải** tên file trên Google Drive.

## 0.7 (Tuỳ chọn) Mock server nhận notification

Để xem backend gọi API thông báo té ngã/bạo lực như thế nào mà không cần dựng server chính thật, chạy một mock server đơn giản (port 9001/9002, khớp với `FALL_EVENT_API_URL` / `VIOLENCE_EVENT_API_URL` ở trên):

```python
# mock_notify_server.py
from fastapi import FastAPI, Request
import uvicorn, threading

fall_app = FastAPI()
violence_app = FastAPI()

@fall_app.post("/fall-events")
async def fall(req: Request):
    print("FALL EVENT:", await req.json())
    return {"ok": True}

@violence_app.post("/violence-events")
async def violence(req: Request):
    print("VIOLENCE EVENT:", await req.json())
    return {"ok": True}

if __name__ == "__main__":
    threading.Thread(target=lambda: uvicorn.run(fall_app, host="0.0.0.0", port=9001), daemon=True).start()
    threading.Thread(target=lambda: uvicorn.run(violence_app, host="0.0.0.0", port=9002)).start()
```

```bash
python mock_notify_server.py
```

## 0.8 Lưu ý khi chạy trên Linux không có GPU/hardware encoder

Một số bản OpenCV/FFmpeg trên Linux (đặc biệt server/container không có `libopenh264`/`x264`) **không hỗ trợ encoder `avc1` (H.264)**. `ClipManager` đã được sửa để tự động fallback sang codec `mp4v` nếu `avc1` không mở được, nên clip vẫn được ghi ra bình thường, chỉ là chất lượng nén/kích thước file có thể khác so với H.264.

---

# 1. Mục tiêu của hệ thống

Backend này cung cấp các khả năng chính:

- Phân tích **video theo request**
- Phân tích **stream camera realtime**
- Chạy **fall detection** và **violent detection** độc lập
- Gọi **2 API riêng** cho 2 loại sự kiện:
  - fall event
  - violence event
- Tự động cắt và lưu **clip sự kiện**
- Upload clip sự kiện lên **Google Drive**
- Trả về kết quả để frontend hoặc hệ thống ngoài hiển thị

---

# 2. Các chức năng chính

## 2.1 Fall Detection
Sử dụng pipeline pose estimation với MoveNet và OpenVINO để:

- phát hiện người trong frame
- trích xuất keypoints / skeleton
- đánh giá tư thế có phải té ngã hay không
- theo dõi state theo thời gian để tránh nhiễu

Hệ thống hỗ trợ:

- anti-jitter
- trigger theo thời lượng
- tracking theo entity
- vẽ skeleton + bbox lên clip output

---

## 2.2 Violent Detection
Sử dụng YOLOv8 để:

- detect đối tượng / vùng bạo lực trên từng frame
- xác định event violence dựa trên class name / confidence
- gom tín hiệu theo thời gian thành event
- vẽ bbox + label lên clip output

---

## 2.3 Event Clip Extraction
Khi có event xảy ra, backend sẽ tạo clip chứa event với logic:

- lấy **padding trước** sự kiện
- lấy **padding sau** sự kiện
- nếu video không đủ độ dài để padding thì lấy đến đầu/cuối video
- mỗi clip có tên riêng và duy nhất
- mỗi clip có metadata:
  - event type
  - start frame
  - end frame
  - fps
  - local path
  - remote file id
  - remote link

---

## 2.4 Upload Cloud
Hiện tại backend hỗ trợ lưu clip lên **Google Drive**:

- tải video nguồn từ Google Drive theo `video_name`
- upload clip sự kiện lên Google Drive
- trả về link file sau upload

---

## 2.5 Notification API
Hệ thống có thể gọi 2 API riêng:

- API thông báo té ngã
- API thông báo bạo lực

Mỗi event có thể có logic trigger riêng theo thời gian, số frame dương tính, anti-jitter...

---

# 3. Kiến trúc tổng quan

Luồng xử lý chính:

1. Nhận request từ frontend / hệ thống ngoài
2. Lấy video từ cloud hoặc mở stream
3. Chạy các detector được bật:
   - fall detector
   - violence detector
4. Cập nhật state event theo thời gian
5. Gửi notification nếu đủ điều kiện
6. Cắt clip sự kiện
7. Upload clip lên Google Drive
8. Trả response kết quả

---

# 4. Cấu trúc thư mục dự án

```text
ai_backend/
├── app/
│   ├── api/
│   │   └── routes/
│   │       └── analysis.py
│   │
│   ├── core/
│   │   └── config.py
│   │
│   ├── domain/
│   │   ├── entities.py
│   │   ├── enums.py
│   │   └── schemas.py
│   │
│   ├── infrastructure/
│   │   ├── google_drive.py
│   │   ├── openvino_fall.py
│   │   ├── trackers.py
│   │   └── yolo_violence.py
│   │
│   ├── services/
│   │   ├── analysis_orchestrator.py
│   │   ├── base_detector.py
│   │   ├── clip_manager.py
│   │   ├── cloud_clip_service.py
│   │   ├── event_notifier.py
│   │   ├── event_state_service.py
│   │   ├── fall_detector.py
│   │   ├── video_source_service.py
│   │   └── violence_detector.py
│   │
│   ├── utils/
│   │   └── file_utils.py
│   │
│   └── main.py
│
├── credentials/
│   ├── oauth_client.json
│   └── token.json
│
├── data/
│   ├── temp/
│   │   └── videos/
│   └── output/
│       └── event_clips/
│
├── models/
│   ├── movenet_multipose_lightning_256x256_FP32.xml
│   ├── movenet_multipose_lightning_256x256_FP32.bin
│   └── best.pt
│
├── .env
├── requirements.txt
└── README.md
```

# 5. Vai trò của từng nhóm thư mục

### app/api/routes

Chứa các endpoint FastAPI mà frontend hoặc hệ thống ngoài gọi vào.

Ví dụ:

```
/api/v1/analysis/video
/api/v1/analysis/stream
```

### app/core

Chứa cấu hình hệ thống, đọc biến môi trường từ .env.

### app/domain

Chứa các kiểu dữ liệu nghiệp vụ chính:

```
entity
enum
schema request / response
```

Đây là phần giúp code sạch và rõ ràng hơn theo hướng OOP / SOLID.

### app/infrastructure

Chứa các thành phần tích hợp công nghệ cụ thể:

```
OpenVINO
MoveNet
YOLO
Google Drive
tracker
```

Đây là lớp “hạ tầng”, tách khỏi business logic.

### data/temp

Nơi lưu tạm video được tải về từ cloud.

### data/output/event_clips

Nơi lưu clip sự kiện được cắt ra trước khi upload.

### models

Chứa model AI:

```
model fall detection
model violent detection
credentials
```

Chứa credential để truy cập Google Drive.

# 6. Yêu cầu môi trường

Khuyến nghị:

```
Python 3.10
Windows / Linux
CPU hoặc GPU tùy cấu hình model
Internet nếu cần truy cập Google Drive
```

# 7. Cài đặt nhanh

## 7.1 Tạo virtual environment

### Windows PowerShell

```
uv venv venv --python 3.10
venv\Scripts\activate
```

### Linux / macOS

```
uv venv venv --python 3.10
source venv/bin/activate
```

## 7.2 Cài dependencies

```
uv pip install -r requirements.txt
```

# 8. Chuẩn bị model

## 8.1 Fall Detection

Đặt model OpenVINO vào thư mục models/:

```
models/movenet_multipose_lightning_256x256_FP32.xml
models/movenet_multipose_lightning_256x256_FP32.bin
```

## 8.2 Violent Detection

Đặt model YOLO vào:

```
models/best.pt
```

# 9. Cấu hình Google Drive

Backend hiện hỗ trợ Google Drive để:

```
tải video nguồn
lưu clip sự kiện
```

## 9.1 Nếu dùng OAuth Client

Đặt file:

```
credentials/oauth_client.json
```

Sau lần chạy đầu, hệ thống có thể tạo:

```
credentials/token.json
```

## 9.2 Folder Google Drive

Bạn nên tạo 2 folder riêng:

```
Source Folder: chứa video nguồn
Event Folder: chứa clip sự kiện output
```

Ví dụ:

```
AI_Input_Videos
AI_Event_Clips
```

# 10. Biến môi trường mẫu

Tạo file .env ở root project:

```
APP_NAME=AI Event Detection Backend
DEBUG=true

TEMP_DIR=./data/temp
OUTPUT_DIR=./data/output

GOOGLE_DRIVE_CREDENTIALS_JSON=./credentials/oauth_client.json
GOOGLE_DRIVE_TOKEN_JSON=./credentials/token.json
GOOGLE_DRIVE_SOURCE_FOLDER_ID=
GOOGLE_DRIVE_EVENT_FOLDER_ID=

FALL_EVENT_API_URL=http://localhost:9001/fall-events
VIOLENCE_EVENT_API_URL=http://localhost:9002/violence-events
EVENT_API_TIMEOUT_SECONDS=2.0

DEFAULT_PRE_EVENT_SECONDS=120
DEFAULT_POST_EVENT_SECONDS=120

FALL_MODEL_XML=./models/movenet_multipose_lightning_256x256_FP32.xml
FALL_DEVICE=CPU
FALL_SCORE_THRESH=0.2
FALL_TRIGGER_SECONDS=2
FALL_MIN_POSITIVE_FRAMES=2
FALL_MAX_NEGATIVE_FRAMES=8

VIOLENCE_MODEL_PT=./models/best.pt
VIOLENCE_CONF=0.25
VIOLENCE_IMGSZ=416
VIOLENCE_DEVICE=cpu
VIOLENCE_TRIGGER_SECONDS=2
VIOLENCE_MIN_POSITIVE_FRAMES=2
VIOLENCE_MAX_NEGATIVE_FRAMES=8

DEFAULT_VIDEO_FPS_FALLBACK=25.0
```

# 11. Giải thích một số biến quan trọng

```
Fall Detection
FALL_TRIGGER_SECONDS: số giây fall phải kéo dài để trigger event
FALL_MIN_POSITIVE_FRAMES: số frame fall liên tiếp tối thiểu để xác nhận ban đầu
FALL_MAX_NEGATIVE_FRAMES: số frame không-fall liên tiếp cho phép trước khi reset state
Violence Detection
VIOLENCE_TRIGGER_SECONDS: số giây violence phải kéo dài để trigger event
VIOLENCE_MIN_POSITIVE_FRAMES: số frame violence liên tiếp tối thiểu
VIOLENCE_MAX_NEGATIVE_FRAMES: số frame không-violence liên tiếp cho phép trước khi reset
Clip Padding
DEFAULT_PRE_EVENT_SECONDS: số giây lấy trước event
DEFAULT_POST_EVENT_SECONDS: số giây lấy sau event
```

# 12. Chạy server

```
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

Sau khi chạy thành công:

```
Swagger UI: http://localhost:8001/docs
OpenAPI JSON: http://localhost:8001/openapi.json
```

# 13. API chính

## 13.1 Phân tích video từ cloud

### Endpoint:

```
POST /api/v1/analysis/video
```

### Ý nghĩa

Dùng khi frontend hoặc hệ thống ngoài muốn phân tích một video có sẵn trên cloud theo video_name.

### Body mẫu

```
{
  "video_name": "camera_01_2026_04_02.mp4",
  "run_fall_detection": true,
  "run_violence_detection": true,
  "pre_event_seconds": 120,
  "post_event_seconds": 120
}
```

### Curl mẫu

```
curl -X POST http://localhost:8001/api/v1/analysis/video \
  -H "Content-Type: application/json" \
  -d '{
    "video_name": "camera_01_2026_04_02.mp4",
    "run_fall_detection": true,
    "run_violence_detection": true,
    "pre_event_seconds": 120,
    "post_event_seconds": 120
  }'
```

## 13.2 Phân tích stream realtime

### Endpoint:

```
POST /api/v1/analysis/stream
```

### Ý nghĩa

Dùng khi hệ thống muốn phân tích luồng camera realtime.

### Body mẫu

```
{
  "stream_source": "rtsp://user:pass@camera/stream",
  "run_fall_detection": true,
  "run_violence_detection": true,
  "pre_event_seconds": 120,
  "post_event_seconds": 120
}
```

### Curl mẫu

```
curl -X POST http://localhost:8001/api/v1/analysis/stream \
  -H "Content-Type: application/json" \
  -d '{
    "stream_source": "rtsp://user:pass@camera/stream",
    "run_fall_detection": true,
    "run_violence_detection": true,
    "pre_event_seconds": 120,
    "post_event_seconds": 120
  }'
```

# 14. Response mẫu

Ví dụ response sau khi phân tích video:

```
{
  "job_id": "aede2f2213cf4ddaa2e19bb61e956e60",
  "status": "completed",
  "mode": "video",
  "source_name": "falldown.mp4",
  "clips": [
    {
      "event_type": "fall",
      "local_path": "data/output/event_clips/falldown_fall_0_1616_xxx.mp4",
      "remote_file_id": "1b8h7oa2ONXJGpanPevhxmtY_3rLRO89U",
      "remote_link": "https://drive.google.com/file/d/xxx/view",
      "start_frame": 0,
      "end_frame": 1616,
      "fps": 59.94
    }
  ],
  "summary": {
    "frames_processed": 1617,
    "events_detected": {
      "fall": 33,
      "violence": 0
    },
    "notifications_sent": {
      "fall": 0,
      "violence": 0
    }
  },
  "started_at": "2026-04-02T17:11:50.000358",
  "finished_at": "2026-04-02T17:13:30.659868"
}
```

## 14.1 Giải thích chi tiết các trường trong response

**Cấp job:**

| Trường | Ý nghĩa |
|---|---|
| `job_id` | ID duy nhất cho lần phân tích này (uuid hex), dùng để tra cứu/log. |
| `status` | Trạng thái job: `running` trong lúc xử lý, `completed` khi xong. Job chạy đồng bộ trong request nên khi client nhận được response nghĩa là job đã `completed`. |
| `mode` | `video` (phân tích file/video cloud) hoặc `stream` (RTSP/webcam/luồng realtime). |
| `source_name` | Tên video hoặc chuỗi nguồn stream đã phân tích. |
| `started_at` / `finished_at` | Thời điểm bắt đầu/kết thúc xử lý (UTC), dùng để tính thời gian xử lý = `finished_at - started_at`. |

**`clips[]`** — danh sách clip sự kiện đã cắt ra, mỗi clip ứng với một khoảng thời gian có fall hoặc violence được xác nhận (đã qua ngưỡng `*_TRIGGER_SECONDS` / `*_MIN_POSITIVE_FRAMES`, không phải mọi frame dương tính đều tạo clip riêng):

| Trường | Ý nghĩa |
|---|---|
| `event_type` | `fall` hoặc `violence`. |
| `local_path` | Đường dẫn file `.mp4` clip trên đĩa local (luôn có, kể cả khi có upload cloud). Mở trực tiếp bằng VLC/ffplay để xem lại sự kiện. |
| `remote_file_id`, `remote_link` | ID và link file trên cloud storage (Google Drive file id, hoặc S3 object key + presigned URL). Chỉ có giá trị khi `USE_CLOUD_STORAGE=true`; ở chế độ local (`USE_CLOUD_STORAGE=false`) hai trường này luôn là `null` vì không upload đi đâu. |
| `start_frame`, `end_frame` | Chỉ số frame bắt đầu/kết thúc của clip trong video gốc, đã gồm padding trước/sau (`pre_event_seconds`/`post_event_seconds`). |
| `fps` | Frame rate dùng để ghi clip (lấy từ video gốc, hoặc `DEFAULT_VIDEO_FPS_FALLBACK` nếu video không đọc được fps). |

Nếu không có sự kiện nào đủ điều kiện trigger, `clips` sẽ là mảng rỗng `[]`, kể cả khi `events_detected` > 0 (frame dương tính lẻ tẻ không đủ để confirm một event).

**`summary`:**

| Trường | Ý nghĩa |
|---|---|
| `frames_processed` | Tổng số frame đã xử lý qua cả hai detector. |
| `events_detected.fall` / `.violence` | Số **frame** (không phải số clip) mà detector tương ứng trả về `event_detected=true` — tức là số lần phát hiện dương tính thô, trước khi gộp theo thời gian thành clip. Một clip thường tương ứng với nhiều frame dương tính liên tiếp trong `events_detected`. |
| `notifications_sent.fall` / `.violence` | Số lần gọi thành công tới `FALL_EVENT_API_URL` / `VIOLENCE_EVENT_API_URL` sau khi clip được xử lý xong (không tính lần gọi "thông báo tức thời" khi vừa phát hiện event, xem mục 17.4 bên dưới). Nếu server nhận thông báo bị lỗi/không phản hồi, số này sẽ thấp hơn số clip. |

**Lưu ý về độ chính xác khi dùng model thay thế (mục 0.3):** nếu bạn đang dùng model YOLOv8 công khai tạm thời thay vì model tự train, `events_detected.violence` và số clip `violence` có thể cao bất thường ngay cả trên video không có bạo lực thật (đã quan sát thực tế: video người đi bộ bình thường vẫn bị báo violence). Đây là hạn chế của model thay thế, không phải lỗi pipeline — cần thay `models/best.pt` bằng model tự train để có kết quả đáng tin cậy.

# 15. Cách thử nghiệm

## 15.1 Test fall detection với video ngắn

Nếu video test ngắn chỉ khoảng vài chục giây, bạn nên giảm padding:

```
{
  "video_name": "falldown.mp4",
  "run_fall_detection": true,
  "run_violence_detection": false,
  "pre_event_seconds": 3,
  "post_event_seconds": 5
}
```

## 15.2 Test violent detection

Gửi request:

```
{
  "video_name": "fight_scene.mp4",
  "run_fall_detection": false,
  "run_violence_detection": true,
  "pre_event_seconds": 3,
  "post_event_seconds": 5
}
```

## 15.3 Test cả hai detector cùng lúc

```
{
  "video_name": "multi_event.mp4",
  "run_fall_detection": true,
  "run_violence_detection": true,
  "pre_event_seconds": 3,
  "post_event_seconds": 5
}
```

## 15.4 Test notification API

Bạn có thể dựng mock server đơn giản để nhận event:

```
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/fall-events")
async def fall(req: Request):
    print("FALL:", await req.json())
    return {"ok": True}

@app.post("/violence-events")
async def violence(req: Request):
    print("VIOLENCE:", await req.json())
    return {"ok": True}
```

# 16. Ghi chú về annotation trên clip output

Clip output hiện được thêm các thông tin:

```
Fall clip
bounding box
skeleton
keypoints
fall confidence
fall angle

Violence clip
bounding box
class name
confidence
label VIOLENCE
```

# 17. Một số lưu ý khi vận hành

## 17.1 Video ngắn và padding dài

Nếu video ngắn hơn tổng padding yêu cầu, clip event có thể chiếm toàn bộ video. Đây là hành vi bình thường.

## 17.2 Stream analysis

Endpoint `/api/v1/analysis/stream` hiện phù hợp để:

```
test stream
demo camera realtime
```

Nếu muốn production lâu dài, nên cân nhắc kiến trúc job-based:

```
start stream job
stop stream job
query stream job status
```

## 17.3 Google Drive

Nếu dùng My Drive cá nhân để upload clip, nên dùng OAuth.
Service account có thể gặp lỗi quota khi upload file mới vào My Drive.

## 17.4 Notification được gửi 2 lần cho mỗi event

Backend gọi API thông báo (`FALL_EVENT_API_URL` / `VIOLENCE_EVENT_API_URL`) hai lần cho cùng một entity:

1. **Thông báo tức thời**: ngay khi frame đầu tiên đủ điều kiện trigger (qua `*_TRIGGER_SECONDS`/`*_MIN_POSITIVE_FRAMES`) trong lúc đang xử lý video, payload có `url: null` vì clip chưa được cắt/upload xong.
2. **Thông báo sau khi có clip**: sau khi video xử lý xong và clip đã được ghi ra (và upload cloud nếu `USE_CLOUD_STORAGE=true`), backend gọi lại API với `event_clip_link`/`event_clip_file_id` đính kèm.

Vì vậy hệ thống nhận thông báo (frontend hoặc server chính) nên xử lý theo `entity_id` để gộp 2 lần gọi này thành 1 sự kiện, thay vì coi mỗi lần gọi là một event riêng biệt. Trường `notifications_sent` trong response chỉ đếm lần gọi thứ 2 (sau khi có clip).

# 18. Các lỗi thường gặp

## 18.1: Lỗi 422 Unprocessable Entity

### Nguyên nhân:

gửi sai JSON body

route yêu cầu body nhưng request gửi query params

## 18.2: Lỗi ModuleNotFoundError: openvino.inference_engine

### Nguyên nhân:

code đang dùng API OpenVINO cũ

môi trường cài OpenVINO mới

### Cách xử lý:

dùng `from openvino import Core`

## 18.3 Google Drive quota error với service account

### Nguyên nhân:

service account không có storage quota của My Drive

### Cách xử lý:

chuyển sang OAuth hoặc dùng Shared Drive

# 19. Hướng mở rộng

Các hướng nâng cấp tiếp theo:

```
lưu metadata job vào database
thêm background queue cho job dài
thêm WebSocket / progress tracking
lưu event timeline chi tiết
hỗ trợ nhiều cloud storage hơn
dashboard quản lý clip sự kiện
Docker / Docker Compose
role-based authentication cho API
```

# 20. Tóm tắt

Backend này phù hợp để:

```
làm AI backend cho web app
tích hợp với camera system
phân tích video theo yêu cầu
lưu clip event để kiểm tra lại
mở rộng thành hệ thống giám sát thông minh
```

Nếu bạn muốn triển khai tiếp, nên bắt đầu theo hướng:

```
hoàn thiện detector threshold
chuẩn hóa notification API
thêm DB/job tracking
container hóa hệ thống
```
