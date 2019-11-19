import json
from pathlib import Path

CORE_DIR = Path(os.getcwd())  # assign the project directory as the one that this was run in
PATHS_DATA = json.loads((CORE_DIR / 'paths.json').read_text())  # path data from json file, consider temporary
REMOTE_BASE_PATH = PATHS_DATA.get('lightsail_base')  # base path for files on the remote AWS Lightsail instance
BOULDAIR_BASE_PATH = PATHS_DATA.get('bouldair_base')  # base path on remote Bouldair website
