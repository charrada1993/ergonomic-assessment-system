# app.py
import threading
import depthai as dai
from config import Config
Config.ensure_dirs()

from camera.manager import CameraManager
from camera.imu_manager import IMUManager
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
    # ── 1. Detect device ─────────────────────────────────────────────────
    devices = dai.Device.getAllAvailableDevices()
    if not devices:
        print("[Main] No OAK-D device found. Exiting.")
        return
    device_info = devices[0]
    print(f"[Main] Using device: {device_info.getMxId()}")

    # ── 2. Create a single shared pipeline ───────────────────────────────
    pipeline = dai.Pipeline()

    # ── 3. Build sub-system nodes into the pipeline ───────────────────────
    cam_mgr = CameraManager(pipeline=pipeline)
    imu_mgr = IMUManager(pipeline=pipeline)

    cam_mgr.setup()   # RGB + StereoDepth (aligned)
    imu_mgr.setup()   # ACCEL + GYRO + ROTATION_VECTOR

    # ── 4. Start the device with the combined pipeline ────────────────────
    try:
        device = dai.Device(pipeline, device_info)
    except Exception as e:
        print(f"[Main] Pipeline start failed: {e}")
        print("[Main] Retrying without ROTATION_VECTOR …")
        # If BNO086 is absent the pipeline may fail; rebuild without RV
        pipeline2 = dai.Pipeline()
        cam_mgr2  = CameraManager(pipeline=pipeline2)
        imu_mgr2  = IMUManager(pipeline=pipeline2)
        cam_mgr2.setup()
        # Rebuild IMU without ROTATION_VECTOR by monkey-patching the flag
        imu_node = pipeline2.create(dai.node.IMU)
        xout_imu = pipeline2.create(dai.node.XLinkOut)
        xout_imu.setStreamName("imu")
        imu_node.enableIMUSensor(dai.IMUSensor.ACCELEROMETER_RAW, 500)
        imu_node.enableIMUSensor(dai.IMUSensor.GYROSCOPE_RAW, 400)
        imu_node.setBatchReportThreshold(1)
        imu_node.setMaxBatchReports(20)
        imu_node.out.link(xout_imu.input)
        imu_mgr2._has_rotation_vector = False
        device   = dai.Device(pipeline2, device_info)
        cam_mgr  = cam_mgr2
        imu_mgr  = imu_mgr2

    print("[Main] Device started with combined pipeline")

    # ── 5. Read factory calibration from device ───────────────────────────
    calib = CameraCalibration.from_device(device)

    # ── 6. Give managers their device handle and start queues ─────────────
    cam_mgr.device = device
    cam_mgr.start_streams()

    imu_mgr.device = device
    imu_mgr.start()

    # ── 7. Pose components ────────────────────────────────────────────────
    pose_est   = PoseEstimator()
    num_cams   = 1   # single OAK-D camera
    pose_fusion = PoseFusion(num_cams)
    skeleton   = SkeletonBuilder()

    # ── 8. Ergonomic calculators ──────────────────────────────────────────
    rula_calc = RULACalculator()
    reba_calc = REBACalculator()

    # ── 9. Data logger ────────────────────────────────────────────────────
    logger = DataLogger()
    logger.start_session()

    # ── 10. Flask app and SocketIO ────────────────────────────────────────
    app, socketio = create_app()

    # ── 11. Store shared objects in app config ────────────────────────────
    app.config['CAMERA_MANAGER'] = cam_mgr
    app.config['CAMERA_MODE']    = num_cams
    app.config['IMU_MANAGER']    = imu_mgr
    app.config['CALIBRATION']    = calib

    # ── 12. Socket event handler ──────────────────────────────────────────
    socket_events = SocketEvents(
        socketio, cam_mgr, pose_est, pose_fusion,
        skeleton, rula_calc, reba_calc, logger, app
    )

    # ── 13. Background processing thread ─────────────────────────────────
    processing_thread = threading.Thread(
        target=socket_events.process_loop, daemon=True
    )
    processing_thread.start()

    # ── 14. Run web server ────────────────────────────────────────────────
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    finally:
        print("[Main] Shutting down …")
        cam_mgr.stop()
        imu_mgr.stop()
        device.close()
        print("[Main] Done.")


if __name__ == '__main__':
    main()