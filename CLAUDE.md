# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Guardian Care is a two-layer safety monitoring platform for elderly people, people with cognitive decline (e.g. Alzheimer's), and others who need care. It was built by a 3-person team during a hackathon. Everything lives in one git repo (a monorepo).

- **Module 1: Lost Alert System (LAS).** Outdoor GPS geofencing (FastAPI, Haversine distance, a webhook alert that repeats until the person is back inside the safe zone). **Out of scope for now: do not work on Module 1 until told otherwise.**
- **Module 2: Fall & Violent Detection System (FVDS).** Indoor AI camera. This is the current focus.

## Commands

There is no lint setup or automated test suite yet. Each Python service has its own venv and `.env` (copy from `.env.example`) and is run from its own folder:

- **besus** (`fvds/sus/besus`, port 8000): `pip install -r requirements.txt`, then `uvicorn app.main:app --reload`. Needs a MySQL database `camera_db` created by hand.
- **beaicam** (`fvds/aicam/beaicam`, port 8001, Python 3.10): `uv venv .venv --python 3.10 && uv pip install -p .venv -r requirements.txt`, then `uvicorn app.main:app --reload --port 8001`. Model files go in `models/` (git-ignored, download commands are in its README section 0.3). `USE_CLOUD_STORAGE=false` runs fully local with videos from `data/input_videos/`.
- fesus has not been scaffolded yet.

## FVDS architecture (planned)

```
fvds/
  sus/          # Set-Up System: maps each camera to the email(s) that get notified
    fesus/      # Vue.js frontend
    besus/      # FastAPI + MySQL backend
  aicam/
    beaicam/    # Core fall/violence detection service (FastAPI, clean architecture)
memory/
  fvds/         # Feature history notes for AI agents (see below)
```

**beaicam pipeline:** video input (on-demand upload or realtime stream, OpenCV), then detection:
- Fall detection: MoveNet pose estimation on OpenVINO extracts the skeleton, then the posture is evaluated.
- Violence detection: Ultralytics YOLOv8.

When an event is detected: cut a clip, draw the skeleton or bounding boxes on it, upload it to S3 (boto3; Google Drive API is also in the stack), then call an API to notify the family members mapped to that camera. That camera-to-email mapping comes from SUS, and the notification differs by event type.

## Memory folder convention

`memory/` is the project's long-term record of what has been built, so future agent sessions can pick up the history. Organize it by feature, with one folder per feature containing numbered `.md` files, e.g.:

```
memory/fvds/set-up-camera-mapping/00_backend.md
memory/fvds/set-up-camera-mapping/01_frontend.md
```

Features can also be split into smaller files (e.g. `00_mapping_creation.md`, `00_mapping_deletion.md`). Read the relevant `memory/` notes before working on a feature, and add or update them after building one.
