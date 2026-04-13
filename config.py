import os
import tomllib

APP_VERSION               = '1.0.0'
DEFAULT_SENSITIVITY       = 5.0
MIN_GAP_ABSOLUTE_SECONDS  = 30
SERVER_PORT               = 5000
SERVER_DEBUG              = False
UPLOAD_FOLDER             = 'uploads'

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

load_config()
