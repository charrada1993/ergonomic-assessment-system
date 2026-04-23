# pose/skeleton.py
import numpy as np

# MediaPipe Pose landmark indices
NOSE = 0
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_ELBOW = 13
RIGHT_ELBOW = 14
LEFT_WRIST = 15
RIGHT_WRIST = 16
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_KNEE = 25
RIGHT_KNEE = 26
LEFT_ANKLE = 27
RIGHT_ANKLE = 28

class SkeletonBuilder:
    @staticmethod
    def angle_between(v1, v2):
        cos = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
        cos = np.clip(cos, -1.0, 1.0)
        return np.degrees(np.arccos(cos))

    def compute_angles(self, landmarks_3d):
        """Compute joint angles from 33x3 MediaPipe landmarks."""
        if landmarks_3d is None or len(landmarks_3d) < 29:
            return {}
        angles = {}
        # Neck angle (vertical: nose to shoulder)
        neck_vec = landmarks_3d[NOSE] - landmarks_3d[LEFT_SHOULDER]
        vertical = np.array([0, -1, 0])
        angles['neck'] = self.angle_between(neck_vec, vertical)

        # Trunk angle (vertical: shoulder to hip)
        trunk_vec = landmarks_3d[LEFT_SHOULDER] - landmarks_3d[LEFT_HIP]
        angles['trunk'] = self.angle_between(trunk_vec, vertical)

        # Upper arm (left) - angle from vertical
        upper_arm_vec = landmarks_3d[LEFT_ELBOW] - landmarks_3d[LEFT_SHOULDER]
        angles['upper_arm_left'] = self.angle_between(upper_arm_vec, vertical)

        # Elbow (left) - angle between upper arm and forearm
        forearm_vec = landmarks_3d[LEFT_WRIST] - landmarks_3d[LEFT_ELBOW]
        upper_rev = landmarks_3d[LEFT_SHOULDER] - landmarks_3d[LEFT_ELBOW]
        angles['elbow_left'] = self.angle_between(forearm_vec, upper_rev)

        # Wrist (left) - simplified flexion (forearm to hand)
        wrist_vec = landmarks_3d[LEFT_WRIST] - landmarks_3d[LEFT_ELBOW]
        angles['wrist_left'] = self.angle_between(wrist_vec, forearm_vec)

        # Legs stability (assume stable if standing)
        angles['legs_stable'] = True

        # Optional: right side angles (mirror)
        upper_arm_vec_r = landmarks_3d[RIGHT_ELBOW] - landmarks_3d[RIGHT_SHOULDER]
        angles['upper_arm_right'] = self.angle_between(upper_arm_vec_r, vertical)
        forearm_vec_r = landmarks_3d[RIGHT_WRIST] - landmarks_3d[RIGHT_ELBOW]
        upper_rev_r = landmarks_3d[RIGHT_SHOULDER] - landmarks_3d[RIGHT_ELBOW]
        angles['elbow_right'] = self.angle_between(forearm_vec_r, upper_rev_r)
        angles['wrist_right'] = self.angle_between(forearm_vec_r, forearm_vec_r)  # placeholder

        return angles