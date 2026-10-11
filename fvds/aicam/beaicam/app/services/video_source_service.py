from __future__ import annotations

from pathlib import Path

import cv2

from app.core.config import Settings
from app.infrastructure.google_drive import GoogleDriveStorage
from app.utils.file_utils import normalize_filename


class VideoSourceService:
    def __init__(self, settings: Settings, storage: GoogleDriveStorage | None):
        self.settings = settings
        self.storage = storage

    def download_video_from_cloud(self, video_name: str) -> Path:
        if self.storage is None:
            # Chế độ local (use_cloud_storage=False): không tải từ Google Drive,
            # chỉ tìm video đã có sẵn trong local_input_videos_dir hoặc theo đường
            # dẫn tuyệt đối/tương đối được truyền thẳng vào video_name.
            candidate = Path(video_name)
            if not candidate.is_absolute():
                candidate = self.settings.local_input_videos_dir / video_name

            if not candidate.exists():
                raise FileNotFoundError(
                    f"Local video not found: {candidate}. "
                    f"Đặt file video vào {self.settings.local_input_videos_dir} "
                    "hoặc bật use_cloud_storage=true để dùng Google Drive."
                )
            return candidate

        safe_name = normalize_filename(video_name)
        destination = self.settings.downloaded_videos_dir / safe_name
        return self.storage.download_file_by_name(
            video_name=video_name,
            destination_path=destination,
            folder_id=self.settings.google_drive_source_folder_id,
        )

    def open_capture(self, source: str | Path):
        cap = cv2.VideoCapture(str(source))
        if not cap.isOpened():
            raise ValueError(f"Cannot open source: {source}")
        return cap
