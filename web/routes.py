# web/routes.py
from flask import Flask, render_template, jsonify, Response
from flask_socketio import SocketIO
from config import Config
import os
import cv2
import time

def create_app():
    app = Flask(__name__,
                template_folder=os.path.join(Config.BASE_DIR, 'web', 'templates'),
                static_folder=os.path.join(Config.BASE_DIR, 'web', 'static'))
    app.config['SECRET_KEY'] = 'secret!'
    socketio = SocketIO(app, cors_allowed_origins="*")

    # ------------------- Page Routes -------------------
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

    # ------------------- API Routes -------------------
    @app.route('/api/config')
    def api_config():
        mode = app.config.get('CAMERA_MODE', 0)
        return jsonify({"mode": mode})

    # ------------------- Video Feed (MJPEG) -------------------
    @app.route('/video_feed')
    def video_feed():
        cam_mgr = app.config.get('CAMERA_MANAGER')
        if not cam_mgr:
            return "Camera not available", 404

        def generate():
            while True:
                frames = cam_mgr.get_latest_frames()
                if frames and len(frames) > 0 and frames[0][1] is not None:
                    frame = frames[0][1]
                    # Resize for faster streaming (optional)
                    h, w = frame.shape[:2]
                    if w > 800:
                        scale = 800 / w
                        new_w = 800
                        new_h = int(h * scale)
                        frame = cv2.resize(frame, (new_w, new_h))
                    ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    if ret:
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
                time.sleep(0.033)  # ~30 fps

        return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

    return app, socketio