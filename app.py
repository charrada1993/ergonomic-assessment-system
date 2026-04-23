# app.py
import threading
import depthai as dai
from config import Config
Config.ensure_dirs()

from camera.manager import CameraManager
from camera.imu_manager import IMUManager
from pose.estimator import PoseEstimator
from pose.fusion import PoseFusion
from pose.skeleton import SkeletonBuilder
from ergonomics.rula import RULACalculator
from ergonomics.reba import REBACalculator
from data.logger import DataLogger
from web.routes import create_app
from web.socket_events import SocketEvents

def main():
    # 1. Detect device
    devices = dai.Device.getAllAvailableDevices()
    if not devices:
        print("No OAK-D device found. Exiting.")
        return
    device_info = devices[0]
    print(f"[Main] Using device: {device_info.getMxId()}")

    # 2. Create a single pipeline
    pipeline = dai.Pipeline()

    # 3. Create managers and let them add their nodes to the pipeline
    cam_mgr = CameraManager(pipeline=pipeline)
    imu_mgr = IMUManager(pipeline=pipeline)

    cam_mgr.setup()
    imu_mgr.setup()

    # 4. Start device with the combined pipeline
    device = dai.Device(pipeline, device_info)
    print("[Main] Device started with combined pipeline")

    # 5. Give managers access to the running device and start their queues
    cam_mgr.device = device
    cam_mgr.start_streams()

    imu_mgr.device = device
    imu_mgr.start()

    # 6. Pose components
    pose_est = PoseEstimator()
    num_cams = 1   # we only use one camera
    pose_fusion = PoseFusion(num_cams)
    skeleton = SkeletonBuilder()

    # 7. Ergonomic calculators
    rula_calc = RULACalculator()
    reba_calc = REBACalculator()

    # 8. Data logger
    logger = DataLogger()
    logger.start_session()

    # 9. Flask app and SocketIO
    app, socketio = create_app()

    # 10. Store objects in app config
    app.config['CAMERA_MANAGER'] = cam_mgr
    app.config['CAMERA_MODE'] = num_cams
    app.config['IMU_MANAGER'] = imu_mgr

    # 11. Socket event handler
    socket_events = SocketEvents(socketio, cam_mgr, pose_est, pose_fusion,
                                 skeleton, rula_calc, reba_calc, logger, app)

    # 12. Background processing thread
    processing_thread = threading.Thread(target=socket_events.process_loop, daemon=True)
    processing_thread.start()

    # 13. Run web server
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    finally:
        cam_mgr.stop()
        imu_mgr.stop()
        device.close()

if __name__ == '__main__':
    main()