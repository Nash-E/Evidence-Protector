import os
import uuid
import time
from flask import Blueprint, request, jsonify, current_app
upload_bp = Blueprint('upload', __name__)
CHUNK_SIZE = 64 * 1024
def _cleanup_old_uploads(folder: str, max_age_seconds: int = 3600):