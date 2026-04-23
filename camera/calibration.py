# camera/calibration.py
# Updated: Reads real intrinsics/extrinsics from OAK-D device calibration.
# Falls back to hardcoded values when no device is connected.

import numpy as np


class CameraCalibration:
    """
    Wraps the OAK-D calibration data for use by the pose estimation pipeline.

    Usage with a live device:
        calib = CameraCalibration.from_device(device)
        K     = calib.rgb_intrinsics      # 3×3
        D     = calib.rgb_distortion      # (k1,k2,p1,p2,k3)

    Usage without a device (testing / CI):
        calib = CameraCalibration.default()
    """

    def __init__(self):
        # ── RGB intrinsics ─────────────────────────────────────────────
        self.rgb_intrinsics  = np.array([[800, 0, 640],
                                          [0, 800, 360],
                                          [0,   0,   1]], dtype=np.float64)
        self.rgb_distortion  = np.zeros(5, dtype=np.float64)

        # ── Left mono intrinsics ────────────────────────────────────────
        self.left_intrinsics = np.array([[800, 0, 640],
                                          [0, 800, 360],
                                          [0,   0,   1]], dtype=np.float64)
        self.left_distortion = np.zeros(5, dtype=np.float64)

        # ── Stereo extrinsics (left→RGB) ────────────────────────────────
        self.R = np.eye(3, dtype=np.float64)
        self.T = np.zeros(3, dtype=np.float64)

        # ── Baseline (m) ────────────────────────────────────────────────
        self.baseline_m = 0.075   # 75 mm typical for OAK-D

    # ------------------------------------------------------------------
    @classmethod
    def from_device(cls, device) -> "CameraCalibration":
        """
        Build a CameraCalibration instance from a live DepthAI device.
        Reads the factory calibration stored on the device's EEPROM.
        """
        import depthai as dai
        obj = cls()
        try:
            cal = device.readCalibration2()

            # RGB intrinsics (1280×720 resolution)
            M_rgb = cal.getCameraIntrinsics(dai.CameraBoardSocket.CAM_A, 1280, 720)
            obj.rgb_intrinsics = np.array(M_rgb, dtype=np.float64)

            d_rgb = cal.getDistortionCoefficients(dai.CameraBoardSocket.CAM_A)
            obj.rgb_distortion = np.array(d_rgb, dtype=np.float64)

            # Left mono intrinsics (1280×720 equivalent)
            M_left = cal.getCameraIntrinsics(dai.CameraBoardSocket.CAM_B, 1280, 720)
            obj.left_intrinsics = np.array(M_left, dtype=np.float64)

            d_left = cal.getDistortionCoefficients(dai.CameraBoardSocket.CAM_B)
            obj.left_distortion = np.array(d_left, dtype=np.float64)

            # Stereo extrinsics
            R_list, T_list = cal.getCameraExtrinsics(
                dai.CameraBoardSocket.CAM_B,
                dai.CameraBoardSocket.CAM_A
            )
            obj.R = np.array(R_list, dtype=np.float64)
            obj.T = np.array(T_list, dtype=np.float64).flatten()

            # Baseline from translation norm (convert cm → m)
            obj.baseline_m = float(np.linalg.norm(obj.T)) / 100.0

            print(f"[Calibration] Loaded from device. Baseline: {obj.baseline_m*100:.1f} cm")

        except Exception as e:
            print(f"[Calibration] WARNING – Could not read device calibration: {e}")
            print("[Calibration] Using default placeholder values.")

        return obj

    @classmethod
    def default(cls) -> "CameraCalibration":
        """Return a calibration object with sensible placeholder values."""
        print("[Calibration] Using default placeholder calibration.")
        return cls()

    # ------------------------------------------------------------------
    # Legacy helper kept for backward compatibility
    # ------------------------------------------------------------------
    @staticmethod
    def get_projection_matrix(cam_idx: int) -> np.ndarray:
        """
        Returns a 3×4 projection matrix for camera `cam_idx`.
        cam_idx 0 → RGB (no translation)
        cam_idx 1 → left mono (~75 mm baseline)
        """
        fx, fy = 800.0, 800.0
        cx, cy = 640.0, 360.0
        K = np.array([[fx, 0, cx],
                      [0, fy, cy],
                      [0,  0,  1]], dtype=np.float64)
        if cam_idx == 0:
            RT = np.hstack((np.eye(3), np.zeros((3, 1))))
        else:
            t = np.array([[0.075 * cam_idx], [0.0], [0.0]])   # 75 mm per step
            RT = np.hstack((np.eye(3), t))
        return K @ RT