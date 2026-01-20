# Copyright (c) 2025-2026 Lab 308, LLC.

# This file is part of automosaic
# (see ${https://github.com/NathanMOlson/automosaic}).

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from flask import Flask, request, jsonify
from tempfile import mkstemp
import os
import time
from batcher import Batcher
from keepalive import KeepAlive

app = Flask(__name__)
batcher = Batcher()
watchdog = KeepAlive("https://batcher-436396529778.us-west1.run.app", float(os.environ["KEEPALIVE_SECONDS"]))

@app.route("/")
def hello():
    return "Lab 308 Upload Server"

@app.route("/keepalive")
def keepalive():
    print("keepalive")
    time.sleep(2)
    return ""

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
    batcher.on_new_file(filepath)
    watchdog.poke()

    return jsonify({'message': f'File {file.filename} saved to {filepath}'}), 200