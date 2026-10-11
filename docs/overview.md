# Tổng quan Guardian Care: hiện trạng

_Cập nhật: 11/10/2026, nhánh `feature/ai-backend`._

Guardian Care là nền tảng cảnh báo an toàn hai lớp cho người cao tuổi, người suy giảm nhận thức và người cần chăm sóc:

- **Module 1, Lost Alert System (LAS):** cảnh báo đi lạc ngoài trời bằng GPS và vùng an toàn. **Đang tạm dừng**, chưa có code.
- **Module 2, Fall & Violent Detection System (FVDS):** camera AI trong nhà, phát hiện té ngã và bạo lực rồi báo cho người thân. **Đang tập trung làm module này.**

## Luồng FVDS

FVDS gồm hai luồng:

1. **Thiết lập:** người quản lý khai báo mỗi camera (mã camera, địa chỉ luồng video, bật/tắt) và các email sẽ nhận cảnh báo. Thông tin này do **SUS** lưu vào MySQL.
2. **Cảnh báo:** **AICAM** phân tích video. Khi xác nhận có té ngã hoặc bạo lực, nó cắt clip bằng chứng, lưu lên S3, tra email theo mã camera từ SUS, rồi gửi email kèm link clip.

```
Camera ──video──▶ beaicam ──clip──▶ S3
                     │
                     ├── tra email theo mã camera ──▶ besus (MySQL)   [chưa nối]
                     └── gửi email cảnh báo ──▶ người thân             [chưa có]

fesus (Vue) ──CRUD camera/email──▶ besus                              [chưa có fesus]
```

## Hiện trạng từng phần

| Thành phần | Thư mục | Công nghệ | Hiện trạng |
|---|---|---|---|
| besus | [fvds/sus/besus](../fvds/sus/besus/) | FastAPI, SQLAlchemy 2, MySQL | **Chạy được.** CRUD camera và email, có endpoint tra theo mã camera cho beaicam. Port 8000. |
| fesus | [fvds/sus/fesus](../fvds/sus/fesus/) | Vue.js | **Chưa có code.** besus đã mở CORS cho `localhost:5173`. |
| beaicam | [fvds/aicam/beaicam](../fvds/aicam/beaicam/) | FastAPI, OpenCV, OpenVINO, YOLOv8, boto3 | **Chạy được ở chế độ local.** Phát hiện, cắt clip, upload S3 đã có. Chưa nối với besus, chưa gửi email. Port 8001. |
| LAS (Module 1) | — | — | Tạm dừng. |

### besus: thiết lập camera và email

- Hai bảng `cameras` (mã `code` duy nhất, `url`, `enabled`) và `camera_emails`. Một camera có từ 1 đến 20 email.
- API:

  | Method | Đường dẫn | Mục đích |
  |---|---|---|
  | POST | `/cameras` | Tạo camera |
  | GET | `/cameras` | Danh sách camera |
  | GET | `/cameras/{id}` | Lấy camera theo id |
  | GET | `/cameras/by-code/{code}` | Tra email theo mã camera (dành cho beaicam) |
  | PUT | `/cameras/{id}` | Sửa email, url, enabled |
  | DELETE | `/cameras/{id}` | Xóa camera |

- `by-code` trả cả camera đang tắt, nên phía gọi phải tự kiểm tra `enabled`.
- Chi tiết: [besus/README.md](../fvds/sus/besus/README.md).

### beaicam: phát hiện té ngã và bạo lực

- Code được đưa vào từ repo riêng `Fall-And-Violent-Detection-System` (commit `f1fa27e` cùng các thay đổi chưa commit lúc copy).
- **Té ngã:** MoveNet Multipose chạy trên OpenVINO lấy khung xương, rồi đánh giá góc thân và tỷ lệ khung hình của từng người.
- **Bạo lực:** YOLOv8. Model hiện dùng là model công khai tạm thời, **báo nhầm nhiều** (video người đi bộ cũng bị nhận là bạo lực). Cần thay bằng model tự huấn luyện.
- Sự kiện chỉ được xác nhận khi đủ số frame dương tính liên tiếp và kéo dài quá ngưỡng thời gian, để tránh báo theo một frame lẻ.
- Khi có sự kiện, beaicam cắt clip có vẽ khung xương hoặc bbox. Nếu `USE_CLOUD_STORAGE=true` thì upload clip lên S3, sau đó POST sự kiện tới một API nhận sự kiện.
- API:
  - `POST /api/v1/analysis/video`: phân tích một video có sẵn.
  - `POST /api/v1/analysis/stream`: phân tích luồng camera.
- Model không nằm trong git. Lệnh tải có trong [beaicam/README.md](../fvds/aicam/beaicam/README.md) mục 0.3.
- Tài liệu thiết kế Agentic AI và Responsible AI: [beaicam/docs/agentic-ai-responsible-ai.md](../fvds/aicam/beaicam/docs/agentic-ai-responsible-ai.md).

## Chạy thử

Mỗi service có venv và file `.env` riêng (copy từ `.env.example`), chạy trong thư mục của nó.

| Service | Chuẩn bị | Lệnh chạy | Địa chỉ |
|---|---|---|---|
| besus | Tạo database `camera_db` trong MySQL | `uvicorn app.main:app --reload` | http://localhost:8000/docs |
| beaicam | Python 3.10, tải model vào `models/`, đặt video vào `data/input_videos/` | `uvicorn app.main:app --reload --port 8001` | http://localhost:8001/docs |

Ở chế độ local (`USE_CLOUD_STORAGE=false`), beaicam không cần tài khoản AWS hay Google Drive. Trên CPU, một video dài 139 giây mất khoảng 4 phút để phân tích.

## Việc còn thiếu

**Để luồng cảnh báo chạy trọn vẹn:**

1. **Nối beaicam với besus.** Request phân tích chưa có mã camera. beaicam đang đoán mã camera từ tên file video, và nếu tên không phải số thì mặc định là camera 5. Cần truyền mã camera vào, tra `GET /cameras/by-code/{code}`, kiểm tra `enabled`, và không gửi nếu không tra được.
2. **Gửi email.** Chưa có code gửi email. Chỉ nên gửi sau khi clip đã lưu lên S3.
3. **Làm fesus** để quản lý camera và email qua giao diện.

**Để chạy được với camera thật:**

4. beaicam giữ mọi frame đã xử lý trong RAM, nên video dài hoặc stream sẽ làm tràn bộ nhớ.
5. Phân tích stream chạy luôn trong một HTTP request và chỉ gửi thông báo khi stream kết thúc. Cần chuyển sang worker chạy nền cho từng camera đang bật.
6. Mỗi frame chạy model hai lần, và model được nạp lại ở mỗi request.

**Chung:**

7. Chưa có test tự động. besus mới thử tay trên SQLite, chưa chạy trên MySQL thật.
8. API của cả hai service chưa có xác thực, nên ai cũng có thể đổi email nhận cảnh báo của một camera.

## Tài liệu liên quan

- [README.md](../README.md): mô tả bài toán và hai module.
- [CLAUDE.md](../CLAUDE.md): kiến trúc và lệnh chạy, dành cho AI agent.
- [memory/fvds/](../memory/fvds/): lịch sử từng tính năng đã làm.
