"""
Project-wide settings, currently limited to directories needed accross the project.

TODO:
    # Notes about what general things should be done in the future
        .
    1) Factor out some non-dynamic directory creation to here, eg the location of specific sheets
        1.1) Make all directories if not exist .mkdir()
            A fresh git clone should be able to run (with required JSON files)
    2) Address plotting code; roll into classes and subclasses
    3) Address duplicate code snippets from db checking; can be factored out into 'check dates of type in sets of n'
    XXXXXX 4) Change database name to a constant
    5) Clean up Local/Remote files in processors.../sftp. Local/Remote classes need updating as well.
    6) Clean up blank_subtract and make it a method of GcRuns and SampleQuants
    7) Standardize .quantify() and make it a method shared by GcRuns and SampleQuants (it should call blank_subtract)
    8) Address sorting in args for run-one in the argparser
    9) Add checker for processor logs dir. Alert if over LOG_DIR_SIZE and allow for shrinking...
"""
import os
import json
from pathlib import Path

__all__ = ['CORE_DIR', 'PATHS_DATA', 'REMOTE_BASE_PATH', 'BOULDAIR_BASE_PATH', 'PROCESSOR_LOGS_DIR',
           'LOG_DIR', 'GCMS_DIR', 'DAILY_DIR', 'DB_NAME', 'MR_PLOT_DIR', 'FULL_PLOT_DIR', 'LOG_PLOT_DIR',
           'DAILY_PLOT_DIR', 'PA_PLOT_DIR', 'STD_PA_PLOT_DIR', 'FILTER_DIRS', 'HISTORIC_DATA_SHEET', 'JSON_FILES',
           'JSON_PRIVATE_DIR', 'JSON_PUBLIC_DIR']

CORE_DIR = Path(os.getcwd())  # assign the project directory as the one that this was run in

DB_NAME = 'sqlite:///zugspitze.sqlite'

# path data from json file, consider temporary
try:
    PATHS_DATA = json.loads((CORE_DIR / 'data/json/private/paths.json').read_text())
    REMOTE_BASE_PATH = PATHS_DATA.get('lightsail_base')  # base path for files on the remote AWS Lightsail instance
    BOULDAIR_BASE_PATH = PATHS_DATA.get('bouldair_base')  # base path on remote Bouldair website
except FileNotFoundError:
    print('WARNING: Could not load path data for remote connections. Connecting to server and website will not work.')

LOG_DIR = CORE_DIR / 'data/log/'
GCMS_DIR = CORE_DIR / 'data/GCMS'
DAILY_DIR = CORE_DIR / 'data/daily'

PROCESSOR_LOGS_DIR = CORE_DIR / 'processing/processors/processor_logs'

MR_PLOT_DIR = CORE_DIR / 'plotting/created/mr_plots'
PA_PLOT_DIR = CORE_DIR / 'plotting/created/PA_plots'
STD_PA_PLOT_DIR = CORE_DIR / 'plotting/created/std_PA_plots'
FULL_PLOT_DIR = CORE_DIR / 'plotting/created/full_plots'
LOG_PLOT_DIR = CORE_DIR / 'plotting/created/logplots'
DAILY_PLOT_DIR = CORE_DIR / 'plotting/created/dailyplots'


FILTER_DIRS = [
    CORE_DIR / 'data/json/private/filters/final',  # get all finalized filters
    CORE_DIR / 'data/json/private/filters/unprocessed',
    # filter unprocessed points, but still check then and moved to final
]

# TODO: JSON DIRs should be used, search project for " / '"
JSON_PRIVATE_DIR = CORE_DIR / 'data/json/private'
JSON_PUBLIC_DIR = CORE_DIR / 'data/json/public'

HISTORIC_DATA_SHEET = CORE_DIR / 'data/sheets/private/INSTAAR_mixing_ratios.xlsx'

JSON_PRIVATE_FILES = ['standards.json', 'lightsail_server_info.json', 'bouldair_server_info.json']
JSON_PUBLIC_FILES = ['zug_long_plot_info.json', 'zug_plot_info.json']

JSON_FILES = (
    [JSON_PRIVATE_DIR / file for file in JSON_PRIVATE_FILES]
    + [JSON_PUBLIC_DIR / file for file in JSON_PUBLIC_FILES]
)

for file in JSON_FILES:
    if not file.exists():
        print(f'WARNING: File {file} does not exist in project. Certain functions will not work.')

# cannot access all Paths and check is_dir() because that returns False if it doesn't exist.
# Maintain a list of all directories and if not .exists(), mkdir
