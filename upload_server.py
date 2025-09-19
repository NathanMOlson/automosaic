from flask import Flask, request, jsonify
from tempfile import mkstemp
import os
from batcher import Batcher

app = Flask(__name__)
batcher = Batcher()

@app.route("/")
def hello():
    return "Lab 308 Upload Server"

@app.route('/image', methods = ['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    fd, filepath = mkstemp(os.path.splitext(file.filename)[1])
    with os.fdopen(fd, 'wb') as f:
        file.save(f)
    batcher.on_new_image(filepath)

    return jsonify({'message': f'File {file.filename} saved to {filepath}'}), 200