import os
import json
from flask import Blueprint, request, jsonify, current_app
from core.detector import run_analysis
from config import DEFAULT_SENSITIVITY
analyze_bp = Blueprint('analyze', __name__)
@analyze_bp.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    if not data or 'file_id' not in data:
        return jsonify({'error': 'Missing file_id'}), 400
    file_id = data['file_id']
    sensitivity = float(data.get('sensitivity', DEFAULT_SENSITIVITY))
    folder = current_app.config['UPLOAD_FOLDER']
    path = os.path.join(folder, file_id)
    if not os.path.isfile(path):
        return jsonify({'error': 'File not found. It may have expired.'}), 404
    try:
        result = run_analysis(path, sensitivity=sensitivity)
    except ValueError as e:
        return jsonify({'error': str(e)}), 422
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {e}'}), 500

    cache_path = path + '.result.json'
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(result, f)
    return jsonify(result)