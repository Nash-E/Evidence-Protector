import os
import uuid
import time
from flask import Blueprint, request, jsonify, current_app
upload_bp = Blueprint('upload', __name__)
CHUNK_SIZE = 64 * 1024
def _cleanup_old_uploads(folder: str, max_age_seconds: int = 3600):
    now = time.time()
    if not os.path.exists(folder):
        return
        
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if os.path.isfile(file_path):
            file_age = os.path.getmtime(file_path)
            if now - file_age > max_age_seconds:
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")
