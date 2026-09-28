# Guardian Care - security supervior system for elderly, intelligent-downgraded and care-needing people

## Problems to solve:

Elderly people living alone, Alzheimer/intelligent-downgraded people who are easy to get out of safe zone. in hospital or Nursing home, falling down or colliding between patients is a risk that is hard to detect immediately only relying on security camera staff. 2 systems combines together to be a 2-layered warning platform: outdoor with GPS/geofence, indoor with AI camera.

## Module 1 - Lost Alert System (LAS)

Backend FastAPI uses Haversine Algorithm to calculate distance between setup position of on-body device (GPS) and a safe zone (geofance) set up by family member/healthcare staff. When a user gets out of allowed zone, system automatically calls webhook to warn to main server, and repeat periodically until they come back the safe zone.

Techstack: FastAPI, SQLAlchemy, Pydantic, httpx, scheduled background task , pytest for testing.

## Module 2 - Fall & Violent Detection System (FVDS)

- Core Fall & Violent Detection - (AI camera) (AICAM): Backend FastAPI analyses video on demand or realtime video stream to detect falling down or violent actions. Fall detection uses pose estimation MoveNet running on OpenVINO to extract scheleton, bones and evaluating postures. violent detection uses YOLOv8 to detect violent actions. When actions are detected, the system cuts clip, labels scheleton/bounding box, save to S3, then call API to notify to family member according to different events.
- Set up system (SUS) is needed to declare which camera maps to which email to send notification.

Techstack:

- SUS: Vue.js, FastAPI, MySQL.
- AICAM: FastAPI, OpenCV, Ultralytics YOLOv8, OpenVINO, NumPy, Google Drive API, boto3 (S3), clean architecture.

## Notice

until having further notice, ignore Module 1 and only focus on developing Module 2.

## Project structure (v1 - for Module 2)

- fvds:
    - sus:
        - fesus
        - besus
    - aicam:
        - beaicam (core business logic for Fall & Violent Detection)
- memory: the brain of the project so AI coding agent know the history of what has been built in future conversations. storing in folder per feature, containing .md files. eg: set-up-camera-mapping (folder) / 00_backend.md ; 01_frontend.md or can be broken into smaller features files, such as 00_mapping_creation.md, 00_mapping_deletion.md
    - fvds:

## Version Control

the project is monoethnic (one github repo only)

## Other context

Our project is developed by 3 members, in a hackathon
