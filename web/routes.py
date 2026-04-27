# web/routes.py
from flask import Flask, render_template, jsonify, Response
from flask_socketio import SocketIO
from config import Config
import os
import cv2
import time
import numpy as np


def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(Config.BASE_DIR, 'web', 'templates'),
        static_folder=os.path.join(Config.BASE_DIR, 'web', 'static')
    )
    app.config['SECRET_KEY'] = 'ergosecret!'
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

    # ─── Page routes ─────────────────────────────────────────────────
    @app.route('/')
    def dashboard():
        return render_template('dashboard.html')

    @app.route('/camera')
    def camera_page():
        return render_template('camera.html')

    @app.route('/rula')
    def rula_page():
        return render_template('rula.html')

    @app.route('/reba')
    def reba_page():
        return render_template('reba.html')

    @app.route('/3d')
    def threed_page():
        return render_template('3d.html')

    # ─── API routes ───────────────────────────────────────────────────
    @app.route('/api/config')
    def api_config():
        mode     = app.config.get('CAMERA_MODE', 0)
        return jsonify({
            'mode':    mode,
            'usb3':    True,
            'imu':     False,
            'has_rv':  False,
        })

    # ─── RGB MJPEG stream ─────────────────────────────────────────────
    @app.route('/video_feed')
    def video_feed():
        cam_mgr = app.config.get('CAMERA_MANAGER')
        if not cam_mgr:
            return "Camera not available", 404

        def generate():
            while True:
                frames = cam_mgr.get_latest_frames()
                frame  = frames.get('rgb') if frames else None
                if frame is not None:
                    # Resize to 960px wide for fluid streaming
                    h, w = frame.shape[:2]
                    if w > 960:
                        scale = 960 / w
                        frame = cv2.resize(frame, (960, int(h * scale)),
                                           interpolation=cv2.INTER_LINEAR)
                    ret, jpeg = cv2.imencode(
                        '.jpg', frame,
                        [cv2.IMWRITE_JPEG_QUALITY, 82]
                    )
                    if ret:
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n'
                               + jpeg.tobytes() + b'\r\n\r\n')
                time.sleep(1.0 / 30)   # 30 fps cap

        return Response(generate(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    # ─── Depth colourmap MJPEG stream ────────────────────────────────
    @app.route('/depth_feed')
    def depth_feed():
        cam_mgr = app.config.get('CAMERA_MANAGER')
        if not cam_mgr:
            return "Camera not available", 404

        def generate():
            while True:
                frames = cam_mgr.get_latest_frames()
                # Prefer the pre-colourised disparity; fallback: raw depth
                frame = frames.get('disp') if frames else None
                if frame is None:
                    raw = frames.get('depth') if frames else None
                    if raw is not None:
                        # Normalise uint16 depth to uint8 for display
                        norm = cv2.normalize(raw, None, 0, 255,
                                             cv2.NORM_MINMAX, dtype=cv2.CV_8U)
                        frame = cv2.applyColorMap(norm, cv2.COLORMAP_HOT)

                if frame is not None:
                    h, w = frame.shape[:2]
                    if w > 480:
                        frame = cv2.resize(frame, (480, int(h * 480 / w)),
                                           interpolation=cv2.INTER_LINEAR)
                    ret, jpeg = cv2.imencode(
                        '.jpg', frame,
                        [cv2.IMWRITE_JPEG_QUALITY, 75]
                    )
                    if ret:
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n'
                               + jpeg.tobytes() + b'\r\n\r\n')
                time.sleep(1.0 / 15)   # 15 fps — depth is slower

        return Response(generate(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    return app, socketio