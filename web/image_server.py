from flask import Flask, request, jsonify
from tempfile import mkstemp
import os
app = Flask(__name__)

@app.route("/")
def hello():
    return "Lab 308 Image Server"

@app.route('/image', methods = ['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filepath = os.path.join("/images", mkstemp(os.path.splitext(file.filename)[1])[1])
    file.save(filepath)

    return jsonify({'message': f'File {file.filename} saved to {filepath}'}), 200