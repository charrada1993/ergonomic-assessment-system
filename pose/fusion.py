# pose/fusion.py
import numpy as np
from camera.calibration import CameraCalibration

class PoseFusion:
    def __init__(self, num_cameras):
        self.num_cameras = num_cameras
        self.calib = CameraCalibration()

    def fuse(self, landmarks_list):
        """
        landmarks_list: list of 33x3 arrays (x,y,z) or None per camera.
        Returns a single 33x3 array (3D skeleton) or None.
        """
        if self.num_cameras == 1:
            return landmarks_list[0] if landmarks_list[0] is not None else None
        else:
            # Simple average of available 3D points (for demo).
            # For a real system, implement multi‑view triangulation.
            valid = [lm for lm in landmarks_list if lm is not None]
            if not valid:
                return None
            return np.mean(valid, axis=0)