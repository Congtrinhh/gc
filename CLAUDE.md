# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Guardian Care is a two-layer safety monitoring platform for elderly people, people with cognitive decline (e.g. Alzheimer's), and others who need care. It was built by a 3-person team during a hackathon. Everything lives in one git repo (a monorepo).

- **Module 1: Lost Alert System (LAS).** Outdoor GPS geofencing (FastAPI, Haversine distance, a webhook alert that repeats until the person is back inside the safe zone). **Out of scope for now: do not work on Module 1 until told otherwise.**
- **Module 2: Fall & Violent Detection System (FVDS).** Indoor AI camera. This is the current focus.

No code has been written yet, so there are no build, lint or test commands. Add them here once each sub-project is scaffolded.

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
