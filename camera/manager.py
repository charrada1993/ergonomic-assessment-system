# camera/manager.py
import depthai as dai
import threading
import time
import cv2

class CameraManager:
    def __init__(self, pipeline=None, device=None):
        self.pipeline = pipeline      # shared pipeline from app.py
        self.device = device          # shared device from app.py
        self.q = None
        self.frame = None
        self.running = False
        self.preview_size = (640, 480)

    def setup(self):
        """Add RGB camera to the pipeline and create queue."""
        if self.pipeline is None:
            return False
        cam_rgb = self.pipeline.create(dai.node.ColorCamera)
        xout_rgb = self.pipeline.create(dai.node.XLinkOut)
        xout_rgb.setStreamName("rgb")
        cam_rgb.setPreviewSize(self.preview_size[0], self.preview_size[1])
        cam_rgb.setInterleaved(False)
        cam_rgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
        cam_rgb.preview.link(xout_rgb.input)
        return True

    def start_streams(self):
        """Start reading frames after device is started."""
        if self.device is None:
            return
        self.running = True
        self.q = self.device.getOutputQueue(name="rgb", maxSize=2, blocking=False)
        threading.Thread(target=self._reader, daemon=True).start()
        print(f"[Camera] Streaming at {self.preview_size}")

    def _reader(self):
        while self.running:
            try:
                in_frame = self.q.get()
                if in_frame:
                    self.frame = in_frame.getCvFrame()
            except:
                pass
            time.sleep(0.01)

    def get_latest_frames(self):
        if self.frame is not None:
            return [(time.time(), self.frame)]
        return [(0, None)]

    def stop(self):
        self.running = False