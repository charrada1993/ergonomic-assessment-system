# data/session_manager.py
import os
import csv
from datetime import datetime
from config import Config

class SessionManager:
    def __init__(self):
        self.current_session = None
        self.current_file = None
        self.writer = None
        self.start_time = None

    def new_session(self):
        """Create a new CSV file for the session and return its path."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"session_{timestamp}.csv"
        filepath = os.path.join(Config.SESSION_DIR, filename)
        self.current_file = open(filepath, 'w', newline='')
        self.writer = csv.writer(self.current_file)
        self.writer.writerow([
            "timestamp", "neck_deg", "trunk_deg", "upper_arm_left_deg",
            "elbow_left_deg", "wrist_left_deg", "RULA_score", "REBA_score",
            "risk_prediction", "anomalies"
        ])
        self.start_time = datetime.now()
        self.current_session = filepath
        return filepath

    def log_data(self, angles, rula_result, reba_result, anomalies):
        """Write one row of data."""
        if self.writer is None:
            return
        elapsed = (datetime.now() - self.start_time).total_seconds()
        row = [
            elapsed,
            angles.get('neck', 0),
            angles.get('trunk', 0),
            angles.get('upper_arm_left', 0),
            angles.get('elbow_left', 0),
            angles.get('wrist_left', 0),
            rula_result.get('RULA_score', 0),
            reba_result.get('REBA_score', 0),
            rula_result.get('risk_level', ''),
            "; ".join(anomalies) if anomalies else ""
        ]
        self.writer.writerow(row)
        self.current_file.flush()

    def end_session(self):
        if self.current_file:
            self.current_file.close()
            self.current_session = None
            self.writer = None