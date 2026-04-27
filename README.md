# Ergonomic Assessment System

Real‑time multi-view human posture analysis using 1-3 OAK‑D Lite cameras, RULA/REBA scoring, and web dashboard. Runs on NVIDIA Orin (Ubuntu).

## Features
- Auto‑detect 1–3 OAK‑D Lite cameras
- Pure vision-based MediaPipe pose estimation + skeleton angles
- RULA & REBA scoring (exact table implementation)
- Live web dashboard with 3D multi-view reconstruction, video feed, and real‑time charts
- Data logging to CSV and automated PDF report generation

## Requirements
- Ubuntu 22.04 (NVIDIA Orin recommended)
- Python 3.10+
- DepthAI 2.24.0.0
- MediaPipe

## Quick Start
```bash
git clone https://github.com/YOUR_USERNAME/ergonomic-assessment-system.git
cd ergonomic-assessment-system
python3 -m venv oak_env
source oak_env/bin/activate
pip install -r requirements.txt
python3 app.py
