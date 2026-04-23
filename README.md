# Ergonomic Assessment System

Real‑time human posture analysis using OAK‑D Lite camera + IMU, RULA/REBA scoring, and web dashboard. Runs on NVIDIA Orin (Ubuntu).

## Features
- Auto‑detect 1–3 OAK‑D Lite cameras
- MediaPipe pose estimation + skeleton angles
- RULA & REBA scoring (exact table implementation)
- IMU (accelerometer/gyroscope) integration for movement risk
- Live web dashboard with video feed and real‑time charts
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
