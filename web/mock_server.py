import time
import threading
import math
from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__, template_folder='templates', static_folder='static')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/3d')
def threed_page():
    return render_template('3d.html')

def background_thread():
    t = 0
    while True:
        time.sleep(0.05)
        t += 0.1
        landmarks = [[0.5, 0.5, 0.0] for _ in range(33)]
        # Hips
        landmarks[23] = [0.4, 0.5, 0]
        landmarks[24] = [0.6, 0.5, 0]
        # Shoulders
        landmarks[11] = [0.3, 0.2, 0]
        landmarks[12] = [0.7, 0.2, 0]
        # Arms
        landmarks[13] = [0.2, 0.4, 0]
        landmarks[14] = [0.8, 0.4, 0]
        landmarks[15] = [0.1, 0.6 + math.sin(t)*0.2, 0]
        landmarks[16] = [0.9, 0.6 + math.cos(t)*0.2, 0]
        # Legs
        landmarks[25] = [0.4, 0.7, 0]
        landmarks[26] = [0.6, 0.7, 0]
        landmarks[27] = [0.4, 0.9, 0]
        landmarks[28] = [0.6, 0.9, 0]
        
        socketio.emit('skeleton_3d', {'landmarks': landmarks})

if __name__ == '__main__':
    threading.Thread(target=background_thread, daemon=True).start()
    socketio.run(app, port=5000, allow_unsafe_werkzeug=True)
