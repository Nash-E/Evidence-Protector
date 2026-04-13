import os
import uuid
import time
from flask import Blueprint, request, jsonify, current_app

upload_bp = Blueprint('upload', __name__)

CHUNK_SIZE = 64 * 1024

def _cleanup_old_uploads(folder: str, max_age_seconds: int = 3600):
    try:
        now = time.time()
        for fname in os.listdir(folder):
            fpath = os.path.join(folder, fname)
            if os.path.isfile(fpath) and (now - os.path.getmtime(fpath)) > max_age_seconds:
                os.remove(fpath)
    except Exception:
        pass

@upload_bp.route('/api/upload', methods=['POST'])
def upload():
    folder = current_app.config['UPLOAD_FOLDER']
    _cleanup_old_uploads(folder)

    filename = request.args.get('filename', 'upload.log')
    file_id = str(uuid.uuid4())
    dest = os.path.join(folder, file_id)

    size = 0
    with open(dest, 'wb') as out:
        while True:
            chunk = request.stream.read(CHUNK_SIZE)
            if not chunk:
                break
            out.write(chunk)
            size += len(chunk)

    return jsonify({
        'file_id': file_id,
        'filename': filename,
        'size_bytes': size,
    })
