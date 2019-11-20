"""
Project-wide settings, currently limited to directories needed accross the project.

TODO:
    # Notes about what general things should be done in the future
    1) Factor out some non-dynamic directory creation to here, eg the location of specific sheets
    2) Address plotting code; roll into classes and subclasses
    3) Address duplicate code snippets from db checking; can be factored out into 'check dates of type in sets of n'
    4) Change database name to a constant
    5) Clean up Local/Remote files in processors.../sftp. Local/Remote classes need updating as well.
"""
import os
import json
from pathlib import Path

__all__ = ['CORE_DIR', 'PATHS_DATA', 'REMOTE_BASE_PATH', 'BOULDAIR_BASE_PATH', 'PROCESSOR_LOGS_DIR',
           'log_dir', 'gcms_dir', 'daily_dir']

CORE_DIR = Path(os.getcwd())  # assign the project directory as the one that this was run in

# path data from json file, consider temporary
PATHS_DATA = json.loads((CORE_DIR / 'data/json/private/paths.json').read_text())
REMOTE_BASE_PATH = PATHS_DATA.get('lightsail_base')  # base path for files on the remote AWS Lightsail instance
BOULDAIR_BASE_PATH = PATHS_DATA.get('bouldair_base')  # base path on remote Bouldair website

log_dir = CORE_DIR / 'data/log'  # TODO: REFACTOR_TO_CONSTANTS (after connected everywhere)
gcms_dir = CORE_DIR / 'data/GCMS'
daily_dir = CORE_DIR / 'data/daily'

PROCESSOR_LOGS_DIR = CORE_DIR / 'processing/processors/processor_logs'
