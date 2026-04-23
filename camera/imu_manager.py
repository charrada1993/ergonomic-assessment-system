# camera/imu_manager.py
import depthai as dai
import threading
import time
import math

class IMUManager:
    def __init__(self, pipeline=None, device=None):
        self.pipeline = pipeline
        self.device = device
        self.running = False
        self.latest = {
            'accel': (0.0, 0.0, 0.0),
            'gyro': (0.0, 0.0, 0.0),
            'rotation_vector': (0.0, 0.0, 0.0, 0.0),
            'accuracy': 0.0,
            'timestamp': 0.0
        }
        self.callback = None

    def setup(self):
        """Add IMU node to the shared pipeline."""
        if self.pipeline is None:
            return False
        imu = self.pipeline.create(dai.node.IMU)
        xout = self.pipeline.create(dai.node.XLinkOut)
        xout.setStreamName("imu")
        imu.enableIMUSensor(dai.IMUSensor.ACCELEROMETER_RAW, 200)
        imu.enableIMUSensor(dai.IMUSensor.GYROSCOPE_RAW, 200)
        imu.setBatchReportThreshold(1)
        imu.setMaxBatchReports(10)
        imu.out.link(xout.input)
        return True

    def start(self, callback=None):
        if self.device is None:
            print("[IMU] No device available")
            return
        self.callback = callback
        self.q = self.device.getOutputQueue(name="imu", maxSize=50, blocking=False)
        self.running = True
        threading.Thread(target=self._reader, daemon=True).start()
        print("[IMU] Streaming started")

    def _reader(self):
        while self.running:
            try:
                imu_data = self.q.get()
                for p in imu_data.packets:
                    acc = p.acceleroMeter
                    self.latest['accel'] = (acc.x, acc.y, acc.z)
                    gyr = p.gyroscope
                    self.latest['gyro'] = (gyr.x, gyr.y, gyr.z)
                    if hasattr(p, 'rotationVector'):
                        rv = p.rotationVector
                        self.latest['rotation_vector'] = (rv.i, rv.j, rv.k, rv.real)
                        self.latest['accuracy'] = rv.rotationVectorAccuracy
                    self.latest['timestamp'] = time.time()
                    if self.callback:
                        self.callback(self.latest)
            except:
                pass
            time.sleep(0.005)

    def stop(self):
        self.running = False

    def get_data(self):
        return self.latest