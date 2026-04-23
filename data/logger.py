# data/logger.py
import csv
import time
import os
from datetime import datetime
from config import Config

class DataLogger:
    def __init__(self):
        self.file = None
        self.writer = None
        self.start_time = None
        self.session_path = None

    def start_session(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"session_{timestamp}.csv"
        self.session_path = os.path.join(Config.SESSION_DIR, filename)
        self.file = open(self.session_path, 'w', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow(["timestamp", "neck_deg", "trunk_deg", "upper_arm_deg",
                              "elbow_deg", "wrist_deg", "RULA_score", "REBA_score",
                              "risk_prediction"])
        self.start_time = time.time()

    def log(self, angles, rula_result, reba_result, anomalies):
        elapsed = time.time() - self.start_time
        row = [
            elapsed,
            angles.get('neck', 0),
            angles.get('trunk', 0),
            angles.get('upper_arm_left', 0),
            angles.get('elbow_left', 0),
            angles.get('wrist_left', 0),
            rula_result.get('RULA_score', 0),
            reba_result.get('REBA_score', 0),
            ", ".join(anomalies) if anomalies else "None"
        ]
        self.writer.writerow(row)
        self.file.flush()

    def end_session(self):
        if self.file:
            self.file.close()