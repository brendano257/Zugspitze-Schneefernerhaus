"""
Project-wide settings, currently limited to directories needed accross the project.
"""

import os
import json
from pathlib import Path

CORE_DIR = Path(os.getcwd())  # assign the project directory as the one that this was run in
PATHS_DATA = json.loads((CORE_DIR / 'data/json/private/paths.json').read_text())  # path data from json file, consider temporary
REMOTE_BASE_PATH = PATHS_DATA.get('lightsail_base')  # base path for files on the remote AWS Lightsail instance
BOULDAIR_BASE_PATH = PATHS_DATA.get('bouldair_base')  # base path on remote Bouldair website

__all__ = [CORE_DIR, PATHS_DATA, REMOTE_BASE_PATH, BOULDAIR_BASE_PATH]
