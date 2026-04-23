# camera/imu_manager.py
# Improved: ROTATION_VECTOR (BNO086) + ACCELEROMETER + GYROSCOPE
# Ref: examples/IMU/imu_rotation_vector.py
# Ref: examples/IMU/imu_gyroscope_accelerometer.py

import depthai as dai
import threading
import time
import math


class IMUManager:
    """
    Manages the OAK-D IMU, streaming:
      • ROTATION_VECTOR  @ 400 Hz  (BNO086 only – quaternion orientation)
      • ACCELEROMETER_RAW @ 500 Hz  (m/s²)
      • GYROSCOPE_RAW     @ 400 Hz  (rad/s)

    All three sensors share a single 'imu' XLink stream in packet batches,
    keeping USB bandwidth low while providing high temporal resolution.
    """

    def __init__(self, pipeline=None, device=None):
        self.pipeline = pipeline
        self.device   = device
        self.running  = False
        self._lock    = threading.Lock()

        # Populated once device type is confirmed
        self._has_rotation_vector = False

        # Latest fused reading – always valid after first IMU packet
        self.latest = {
            'accel':             (0.0, 0.0, 0.0),   # (x, y, z) m/s²
            'gyro':              (0.0, 0.0, 0.0),   # (x, y, z) rad/s
            'rotation_vector':   (0.0, 0.0, 0.0, 1.0),  # (i, j, k, real) quaternion
            'accuracy':          0.0,                # rotation vector accuracy (rad)
            'accel_ts_ms':       0.0,                # device timestamp ms
            'gyro_ts_ms':        0.0,
            'rv_ts_ms':          0.0,
            'timestamp':         0.0,                # host Unix time
        }
        self._base_ts = None   # first device timestamp for relative display
        self.callback = None

    # ------------------------------------------------------------------
    # Pipeline setup (called BEFORE device is started)
    # ------------------------------------------------------------------
    def setup(self):
        """
        Add the IMU node to the shared pipeline.
        Enables all three sensor types; ROTATION_VECTOR is conditionally
        activated at start_streams() once we know the device's IMU type.
        """
        if self.pipeline is None:
            print("[IMU] ERROR – no pipeline provided")
            return False

        imu  = self.pipeline.create(dai.node.IMU)
        xout = self.pipeline.create(dai.node.XLinkOut)
        xout.setStreamName("imu")

        # High-rate raw sensors (always available on OAK-D)
        imu.enableIMUSensor(dai.IMUSensor.ACCELEROMETER_RAW, 500)  # 500 Hz
        imu.enableIMUSensor(dai.IMUSensor.GYROSCOPE_RAW,     400)  # 400 Hz

        # ROTATION_VECTOR at 400 Hz – only supported on BNO086.
        # We add it unconditionally here; if the device doesn't support it
        # the pipeline will raise at device.startPipeline() and we catch it
        # gracefully in app.py / start_streams().
        # NOTE: If you know your device does NOT have BNO086, comment out
        # the next line; ACCEL + GYRO alone will still work.
        imu.enableIMUSensor(dai.IMUSensor.ROTATION_VECTOR, 400)    # 400 Hz
        self._has_rotation_vector = True

        # Recommended batch settings when sharing pipeline with many nodes
        # (ref: imu_gyroscope_accelerometer.py and imu_rotation_vector.py)
        imu.setBatchReportThreshold(1)    # send as soon as 1 packet is ready
        imu.setMaxBatchReports(20)        # cap batch at 20 to limit latency

        imu.out.link(xout.input)

        print("[IMU] Pipeline configured: ACCEL@500Hz + GYRO@400Hz + ROTATION_VECTOR@400Hz")
        return True

    # ------------------------------------------------------------------
    # Streaming (called AFTER device is started)
    # ------------------------------------------------------------------
    def start(self, callback=None):
        """
        Open the IMU output queue and launch the background reader thread.
        `callback` (optional): called with the latest dict on every packet.
        """
        if self.device is None:
            print("[IMU] ERROR – no device provided")
            return

        # Confirm IMU chip type at runtime
        imu_type = self.device.getConnectedIMU()
        fw_ver   = self.device.getIMUFirmwareVersion()
        print(f"[IMU] Chip: {imu_type}  Firmware: {fw_ver}")

        if imu_type != "BNO086":
            print("[IMU] WARNING – ROTATION_VECTOR requires BNO086; "
                  "falling back to ACCEL + GYRO only.")
            self._has_rotation_vector = False
            # Note: the pipeline was already started with ROTATION_VECTOR enabled.
            # If the device rejected it, the queue will simply carry no RV packets.

        self.callback = callback

        # Large maxSize buffer so we never drop packets at high rates
        self._q = self.device.getOutputQueue(name="imu", maxSize=100, blocking=False)
        self.running = True
        t = threading.Thread(target=self._reader, daemon=True)
        t.start()
        print("[IMU] Streaming started")

    # ------------------------------------------------------------------
    # Background reader thread
    # ------------------------------------------------------------------
    def _reader(self):
        """
        Drain the IMU queue continuously.  Uses .get() (blocking) so the
        thread sleeps on the OS and consumes zero CPU while idle –
        identical to the pattern in the official Luxonis examples.
        """
        def ts_to_ms(delta):
            return delta.total_seconds() * 1000.0

        while self.running:
            try:
                imu_data    = self._q.get()          # blocks until data arrives
                imu_packets = imu_data.packets

                for pkt in imu_packets:
                    update = {}

                    # ── Accelerometer ────────────────────────────────────
                    if hasattr(pkt, 'acceleroMeter'):
                        acc = pkt.acceleroMeter
                        ts  = acc.getTimestampDevice()
                        if self._base_ts is None:
                            self._base_ts = ts
                        update['accel']        = (acc.x, acc.y, acc.z)
                        update['accel_ts_ms']  = ts_to_ms(ts - self._base_ts)

                    # ── Gyroscope ────────────────────────────────────────
                    if hasattr(pkt, 'gyroscope'):
                        gyr = pkt.gyroscope
                        ts  = gyr.getTimestampDevice()
                        if self._base_ts is None:
                            self._base_ts = ts
                        update['gyro']       = (gyr.x, gyr.y, gyr.z)
                        update['gyro_ts_ms'] = ts_to_ms(ts - self._base_ts)

                    # ── Rotation Vector (quaternion) ──────────────────────
                    if self._has_rotation_vector and hasattr(pkt, 'rotationVector'):
                        rv = pkt.rotationVector
                        ts = rv.getTimestampDevice()
                        if self._base_ts is None:
                            self._base_ts = ts
                        update['rotation_vector'] = (rv.i, rv.j, rv.k, rv.real)
                        update['accuracy']        = rv.rotationVectorAccuracy
                        update['rv_ts_ms']        = ts_to_ms(ts - self._base_ts)

                    # Commit the update atomically
                    update['timestamp'] = time.time()
                    with self._lock:
                        self.latest.update(update)

                    if self.callback:
                        self.callback(self.get_data())

            except Exception as e:
                if self.running:
                    print(f"[IMU] Reader error: {e}")

    # ------------------------------------------------------------------
    # Public accessors
    # ------------------------------------------------------------------
    def get_data(self) -> dict:
        """
        Returns a copy of the latest IMU readings:
            {
              'accel':           (x, y, z) m/s²
              'gyro':            (x, y, z) rad/s
              'rotation_vector': (i, j, k, real) unit quaternion
              'accuracy':        float  rotation accuracy in radians
              'accel_ts_ms':     float  device timestamp (ms from start)
              'gyro_ts_ms':      float
              'rv_ts_ms':        float
              'timestamp':       float  host Unix time
              'euler':           (roll_deg, pitch_deg, yaw_deg)
            }
        """
        with self._lock:
            data = dict(self.latest)

        # Derive Euler angles from quaternion for easy consumption downstream
        i, j, k, r = data['rotation_vector']
        roll, pitch, yaw = self._quat_to_euler(r, i, j, k)
        data['euler'] = (roll, pitch, yaw)
        return data

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------
    @staticmethod
    def _quat_to_euler(w: float, x: float, y: float, z: float):
        """Convert unit quaternion (w, x, y, z) to Euler angles in degrees."""
        # Roll (X-axis rotation)
        sinr_cosp = 2.0 * (w * x + y * z)
        cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
        roll = math.degrees(math.atan2(sinr_cosp, cosr_cosp))

        # Pitch (Y-axis rotation) – clamped to avoid NaN at poles
        sinp = 2.0 * (w * y - z * x)
        sinp = max(-1.0, min(1.0, sinp))
        pitch = math.degrees(math.asin(sinp))

        # Yaw (Z-axis rotation)
        siny_cosp = 2.0 * (w * z + x * y)
        cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
        yaw = math.degrees(math.atan2(siny_cosp, cosy_cosp))

        return roll, pitch, yaw

    def stop(self):
        self.running = False