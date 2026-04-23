# pose/estimator.py
import mediapipe as mp
import cv2
import numpy as np

mp_pose = mp.solutions.pose
pose_model = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    smooth_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

class PoseEstimator:
    @staticmethod
    def get_landmarks(frame):
        if frame is None:
            return None
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose_model.process(rgb)
        if results.pose_landmarks:
            landmarks = []
            for lm in results.pose_landmarks.landmark:
                landmarks.append([lm.x, lm.y, lm.z])
            return np.array(landmarks)
        return None