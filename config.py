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