# app.py
import threading
import depthai as dai
from config import Config
Config.ensure_dirs()

from camera.manager import CameraManager
from camera.calibration import CameraCalibration
from pose.estimator import PoseEstimator
from pose.fusion import PoseFusion
from pose.skeleton import SkeletonBuilder
from ergonomics.rula import RULACalculator
from ergonomics.reba import REBACalculator
from data.logger import DataLogger
from web.routes import create_app
from web.socket_events import SocketEvents


def main():
    # ── 1. Detect devices ─────────────────────────────────────────────────
    devices_info = dai.Device.getAllAvailableDevices()
    if not devices_info:
        print("[Main] No OAK-D device found. Exiting.")
        return
    
    # Limit to max 3 cameras
    devices_info = devices_info[:3]
    num_cams = len(devices_info)
    print(f"[Main] Detected {num_cams} OAK-D device(s)")

    cam_managers = []
    devices = []
    calibrations = []

    # ── 2. Create pipelines and initialize cameras ───────────────────────
    for idx, dev_info in enumerate(devices_info):
        print(f"[Main] Initializing device {idx+1}/{num_cams}: {dev_info.getMxId()}")
        pipeline = dai.Pipeline()
        cam_mgr = CameraManager(pipeline=pipeline)
        
        cam_mgr.setup()   # RGB + StereoDepth (aligned)
        # Note: IMU logic removed per vision-only mode requirement
        
        try:
            device = dai.Device(pipeline, dev_info)
        except Exception as e:
            print(f"[Main] Pipeline start failed for device {dev_info.getMxId()}: {e}")
            continue

        calib = CameraCalibration.from_device(device)
        cam_mgr.device = device
        cam_mgr.start_streams()
        
        devices.append(device)
        cam_managers.append(cam_mgr)
        calibrations.append(calib)

    if not cam_managers:
        print("[Main] Failed to initialize any devices. Exiting.")
        return

    # Update num_cams based on successfully initialized devices
    num_cams = len(cam_managers)
    print(f"[Main] {num_cams} device(s) successfully started and streaming")

    # ── 3. Pose components ────────────────────────────────────────────────
    pose_est   = PoseEstimator()
    pose_fusion = PoseFusion(num_cams)
    skeleton   = SkeletonBuilder()

    # ── 4. Ergonomic calculators ──────────────────────────────────────────
    rula_calc = RULACalculator()
    reba_calc = REBACalculator()

    # ── 5. Data logger ────────────────────────────────────────────────────
    logger = DataLogger()
    logger.start_session()

    # ── 6. Flask app and SocketIO ────────────────────────────────────────
    app, socketio = create_app()

    # ── 7. Store shared objects in app config ────────────────────────────
    # In multi-camera mode, we store the list of managers.
    app.config['CAMERA_MANAGERS'] = cam_managers
    app.config['CAMERA_MANAGER']  = cam_managers[0] # Primary camera for video feed compatibility
    app.config['CAMERA_MODE']     = num_cams
    app.config['CALIBRATION']     = calibrations[0] if calibrations else None
    app.config['IMU_MANAGER']     = None # Disabled

    # ── 8. Socket event handler ──────────────────────────────────────────
    socket_events = SocketEvents(
        socketio, cam_managers, pose_est, pose_fusion,
        skeleton, rula_calc, reba_calc, logger, app
    )

    # ── 9. Background processing thread ─────────────────────────────────
    processing_thread = threading.Thread(
        target=socket_events.process_loop, daemon=True
    )
    processing_thread.start()

    # ── 10. Run web server ────────────────────────────────────────────────
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    finally:
        print("[Main] Shutting down …")
        for cam_mgr in cam_managers:
            cam_mgr.stop()
        for device in devices:
            device.close()
        print("[Main] Done.")


if __name__ == '__main__':
    main()