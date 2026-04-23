# config.py
import os

class Config:
    # Camera
    MAX_CAMERAS = 3
    PROCESSING_FPS = 10          # Target pose estimation frequency (Hz)
    LOG_INTERVAL = 0.5           # Log data every 0.5 seconds
    
    # Paths (absolute or relative to project root)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SESSION_DIR = os.path.join(BASE_DIR, "sessions")
    REPORT_DIR = os.path.join(BASE_DIR, "reports")
    STATIC_DIR = os.path.join(BASE_DIR, "web", "static")
    TEMPLATE_DIR = os.path.join(BASE_DIR, "web", "templates")
    
    # Ergonomic thresholds
    LOAD_KG_DEFAULT = 0          # Default load if not entered by user
    REPETITIVE_DEFAULT = False
    PROLONGED_DEFAULT = False
    GRIP_QUALITY_DEFAULT = 0     # 0=good, 1=average, 2=poor
    
    @staticmethod
    def ensure_dirs():
        os.makedirs(Config.SESSION_DIR, exist_ok=True)
        os.makedirs(Config.REPORT_DIR, exist_ok=True)
        os.makedirs(Config.STATIC_DIR, exist_ok=True)
        os.makedirs(Config.TEMPLATE_DIR, exist_ok=True)