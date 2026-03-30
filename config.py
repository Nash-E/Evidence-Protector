"""
config.py — Loads settings from config.toml (if present) and exposes
            flat constants used throughout the app and CLI.

Priority:  config.toml  >  built-in defaults below
"""

import os
import tomllib  # stdlib since Python 3.11

# ── Built-in defaults ────────────────────────────────────────────────────────
APP_VERSION               = '1.0.0'
DEFAULT_SENSITIVITY       = 5.0   # MAD z-score threshold
MIN_GAP_ABSOLUTE_SECONDS  = 30    # hard floor — never flag shorter gaps
SERVER_PORT               = 5000
SERVER_DEBUG              = False
UPLOAD_FOLDER             = 'uploads'

# ── Load config.toml if it exists ────────────────────────────────────────────
_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.toml')

def _load_toml(path: str) -> dict:
    try:
        with open(path, 'rb') as f:
            return tomllib.load(f)
    except FileNotFoundError:
        return {}
    except tomllib.TOMLDecodeError as e:
        print(f"[config] WARNING: Could not parse {path}: {e}")
        return {}

def load_config(path: str = _CONFIG_PATH) -> None:
    """Re-read a TOML file and update module-level constants in-place."""
    global DEFAULT_SENSITIVITY, MIN_GAP_ABSOLUTE_SECONDS
    global SERVER_PORT, SERVER_DEBUG, UPLOAD_FOLDER

    data = _load_toml(path)

    analysis = data.get('analysis', {})
    server   = data.get('server',   {})

    DEFAULT_SENSITIVITY      = float(analysis.get('default_sensitivity',  DEFAULT_SENSITIVITY))
    MIN_GAP_ABSOLUTE_SECONDS = int(analysis.get('min_gap_seconds',        MIN_GAP_ABSOLUTE_SECONDS))
    SERVER_PORT              = int(server.get('port',                     SERVER_PORT))
    SERVER_DEBUG             = bool(server.get('debug',                   SERVER_DEBUG))
    UPLOAD_FOLDER            = str(server.get('upload_folder',            UPLOAD_FOLDER))

# Apply config.toml on import (if it exists next to this file)
load_config()
