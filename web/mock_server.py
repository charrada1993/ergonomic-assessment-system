import os
from flask import Flask, render_template

app = Flask(__name__, template_folder='templates', static_folder='static')

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

if __name__ == '__main__':
    app.run(port=5000)
