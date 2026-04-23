# web/socket_events.py
import time
import math
import traceback
from flask_socketio import emit

class SocketEvents:
    def __init__(self, socketio, cam_mgr, pose_est, pose_fusion,
                 skeleton, rula_calc, reba_calc, logger, app):
        self.socketio = socketio
        self.cam_mgr = cam_mgr
        self.pose_est = pose_est
        self.pose_fusion = pose_fusion
        self.skeleton = skeleton
        self.rula_calc = rula_calc
        self.reba_calc = reba_calc
        self.logger = logger
        self.app = app
        self.running = True

        @socketio.on('connect')
        def handle_connect():
            print("[Socket] Client connected")
            emit('config', {'mode': self.cam_mgr.mode})

    def process_loop(self):
        """Background thread: get frames, run pose estimation, compute RULA/REBA, emit via Socket.IO."""
        print("[Processing] Thread started")
        last_log = 0
        frame_count = 0

        while self.running:
            try:
                frames = self.cam_mgr.get_latest_frames()
                if frames and len(frames) > 0 and frames[0][1] is not None:
                    frame_count += 1
                    if frame_count % 30 == 0:
                        print(f"[Processing] Received {frame_count} frames")

                    # Get landmarks from first camera (single‑view mode)
                    landmarks_2d = self.pose_est.get_landmarks(frames[0][1])
                    if landmarks_2d is not None:
                        if frame_count % 30 == 0:
                            print(f"[Processing] Landmarks detected, shape {landmarks_2d.shape}")

                        # For single camera, fusion just returns the 2D landmarks
                        skeleton_3d = self.pose_fusion.fuse([landmarks_2d])
                        angles = self.skeleton.compute_angles(skeleton_3d)

                        # RULA & REBA scores
                        rula_res = self.rula_calc.compute(angles)
                        reba_res = self.reba_calc.compute(angles)

                        # --- IMU Data Integration (risk enhancement) ---
                        anomalies = []
                        imu_mgr = self.app.config.get('IMU_MANAGER')
                        if imu_mgr:
                            imu_data = imu_mgr.get_data()
                            # Accelerometer magnitude (m/s^2)
                            accel_mag = math.sqrt(imu_data['accel'][0]**2 +
                                                 imu_data['accel'][1]**2 +
                                                 imu_data['accel'][2]**2)
                            if accel_mag > 25.0:   # > 2.5 g
                                anomalies.append("Sudden jerk detected")
                            # Gyroscope rotation speed (rad/s)
                            gyro_speed = max(abs(imu_data['gyro'][0]),
                                           abs(imu_data['gyro'][1]),
                                           abs(imu_data['gyro'][2]))
                            if gyro_speed > 3.0:
                                anomalies.append("Rapid twisting motion")
                            # (Optional) rotation vector stability check

                        # Send real‑time update to all connected clients
                        self.socketio.emit('pose_update', {
                            'angles': angles,
                            'rula': rula_res['RULA_score'],
                            'reba': reba_res['REBA_score'],
                            'risk_level': rula_res['risk_level'],
                            'anomalies': anomalies
                        })

                        # Log data periodically (every 0.5 seconds)
                        now = time.time()
                        if now - last_log >= 0.5:
                            from ergonomics.risk import RiskAnalyzer
                            # Combine vision-based anomalies with IMU anomalies
                            vision_anomalies = RiskAnalyzer.detect_anomalies(
                                angles, rula_res['RULA_score'], reba_res['REBA_score'])
                            all_anomalies = vision_anomalies + anomalies
                            self.logger.log(angles, rula_res, reba_res, all_anomalies)
                            last_log = now

                    else:
                        if frame_count % 60 == 0:
                            print("[Processing] No landmarks detected (person not visible?)")
                else:
                    if frame_count % 60 == 0:
                        print("[Processing] No camera frame received")
            except Exception as e:
                print(f"[Processing] ERROR: {e}")
                traceback.print_exc()
            time.sleep(1.0 / 10)   # 10 Hz processing