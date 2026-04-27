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
    def compute_euler(v):
        """
        Compute Pitch (sagittal plane: flexion/extension) and 
        Roll (coronal plane: abduction/adduction) using atan2.
        MediaPipe coordinate system: X is right, Y is down, Z is forward.
        """
        vx, vy, vz = v
        # Pitch (Flexion/Extension): Angle in Y-Z plane relative to vertical (Y)
        pitch = np.degrees(np.arctan2(vz, vy))
        # Roll (Abduction/Adduction): Angle in X-Y plane relative to vertical (Y)
        roll = np.degrees(np.arctan2(vx, vy))
        return pitch, roll

    def compute_angles(self, landmarks_3d):
        """Compute signed joint angles from 33x3 MediaPipe landmarks."""
        if landmarks_3d is None or len(landmarks_3d) < 29:
            return {}
        angles = {}
        
        # Neck angle (shoulder to nose)
        neck_vec = landmarks_3d[NOSE] - landmarks_3d[LEFT_SHOULDER]
        # Nose is above shoulder, so vy is negative. Invert to make down positive for math consistency, 
        # or just use -neck_vec so it points down.
        neck_pitch, neck_roll = self.compute_euler(-neck_vec)
        angles['neck'] = neck_pitch
        angles['neck_mod'] = 1 if abs(neck_roll) > 10 else 0  # Lateral bend/twist

        # Trunk angle (hip to shoulder)
        trunk_vec = landmarks_3d[LEFT_SHOULDER] - landmarks_3d[LEFT_HIP]
        trunk_pitch, trunk_roll = self.compute_euler(-trunk_vec)
        angles['trunk'] = trunk_pitch
        angles['trunk_mod'] = 1 if abs(trunk_roll) > 10 else 0

        # Upper arm (left) (shoulder to elbow)
        upper_arm_vec = landmarks_3d[LEFT_ELBOW] - landmarks_3d[LEFT_SHOULDER]
        arm_pitch, arm_roll = self.compute_euler(upper_arm_vec)
        angles['upper_arm_left'] = arm_pitch
        angles['shoulder_mod'] = 1 if abs(arm_roll) > 20 else 0  # Abduction

        # Elbow (left)
        forearm_vec = landmarks_3d[LEFT_WRIST] - landmarks_3d[LEFT_ELBOW]
        # Elbow flexion is the angle between upper arm and forearm. 
        # We can use the generic angle between them for flexion:
        cos = np.dot(upper_arm_vec, forearm_vec) / (np.linalg.norm(upper_arm_vec) * np.linalg.norm(forearm_vec) + 1e-6)
        angles['elbow_left'] = np.degrees(np.arccos(np.clip(cos, -1.0, 1.0)))

        # Wrist (left)
        # Flexion is roughly the angle of the hand relative to forearm.
        # Since we only have wrist, we'll approximate with forearm pitch for now or 0.
        angles['wrist_left'] = 0  # Vision model lacks hand joints unless using hands model

        # Legs stability (assume stable if standing)
        angles['legs_stable'] = True
        
        # Knee (left) - hip to knee, knee to ankle
        thigh_vec = landmarks_3d[LEFT_KNEE] - landmarks_3d[LEFT_HIP]
        shank_vec = landmarks_3d[LEFT_ANKLE] - landmarks_3d[LEFT_KNEE]
        cos_knee = np.dot(thigh_vec, shank_vec) / (np.linalg.norm(thigh_vec) * np.linalg.norm(shank_vec) + 1e-6)
        angles['knee_left'] = np.degrees(np.arccos(np.clip(cos_knee, -1.0, 1.0)))

        # Optional: right side angles
        upper_arm_vec_r = landmarks_3d[RIGHT_ELBOW] - landmarks_3d[RIGHT_SHOULDER]
        arm_pitch_r, arm_roll_r = self.compute_euler(upper_arm_vec_r)
        angles['upper_arm_right'] = arm_pitch_r
        
        forearm_vec_r = landmarks_3d[RIGHT_WRIST] - landmarks_3d[RIGHT_ELBOW]
        cos_r = np.dot(upper_arm_vec_r, forearm_vec_r) / (np.linalg.norm(upper_arm_vec_r) * np.linalg.norm(forearm_vec_r) + 1e-6)
        angles['elbow_right'] = np.degrees(np.arccos(np.clip(cos_r, -1.0, 1.0)))
        angles['wrist_right'] = 0

        return angles