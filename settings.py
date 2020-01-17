"""
Project-wide settings, currently limited to directories needed accross the project.

TODO:
    # Notes about what general things should be done in the future
    .
    .
    1) Standardize .quantify() and make it a method shared by GcRuns and SampleQuants (it should call blank_subtract)
    1.1) Make a re-quantify method that takes dates to match between, etc. Use in processor to avoid pointless checking
        of old, unmatched data. (use a config last_data_date, but always check 2-weeks back.
    5) Make all classes hashable by their SQLite ID and uniquely dimensioned data
        would allow more abstraction in database query/update/checking on different data types
    6) Use sets wherever possible (updated daily date checking at same time)
    7) Switch to generators wherever possible
    8) Create EBAS data module -- generator based

"""
import json
from pathlib import Path

__all__ = ['CORE_DIR', 'REMOTE_BASE_PATH', 'BOULDAIR_BASE_PATH', 'PROCESSOR_LOGS_DIR',
           'LOG_DIR', 'GCMS_DIR', 'DAILY_DIR', 'LOCAL_BASE_PATH', 'DB_NAME', 'DB_PROTO', 'DB_FILE', 'MR_PLOT_DIR',
           'FULL_PLOT_DIR', 'LOG_PLOT_DIR', 'DAILY_PLOT_DIR', 'PA_PLOT_DIR', 'STD_PA_PLOT_DIR', 'FILTER_DIRS',
           'HISTORIC_DATA_SHEET', 'JSON_FILES', 'JSON_PRIVATE_DIR', 'JSON_PUBLIC_DIR']

CORE_DIR = Path('/home/brendan/PycharmProjects/Z')  # assign static project directory

DB_FILE = 'zugspitze.sqlite'
DB_PROTO = 'sqlite:///{}'
DB_NAME = DB_PROTO.format(DB_FILE)

# data directories for LabView logs, GCMS output files, and daily files
LOG_DIR = CORE_DIR / 'data/log/'
GCMS_DIR = CORE_DIR / 'data/GCMS'
DAILY_DIR = CORE_DIR / 'data/daily'

LOCAL_BASE_PATH = CORE_DIR / 'data'

# directory to put logging data files in
PROCESSOR_LOGS_DIR = CORE_DIR / 'processing/processors/processor_logs'

# plotting directories
MR_PLOT_DIR = CORE_DIR / 'plotting/created/mr_plots'
PA_PLOT_DIR = CORE_DIR / 'plotting/created/PA_plots'
STD_PA_PLOT_DIR = CORE_DIR / 'plotting/created/std_PA_plots'
FULL_PLOT_DIR = CORE_DIR / 'plotting/created/full_plots'
LOG_PLOT_DIR = CORE_DIR / 'plotting/created/logplots'
DAILY_PLOT_DIR = CORE_DIR / 'plotting/created/dailyplots'

# directories that should be scanned for filter files when run
FILTER_DIRS = [
    CORE_DIR / 'data/json/private/filters/final',  # get all finalized filters
    CORE_DIR / 'data/json/private/filters/unprocessed',
    # filter unprocessed points, but still check them and move to final after
]

# directories containing JSON files for various purposes
JSON_PRIVATE_DIR = CORE_DIR / 'data/json/private'
JSON_PUBLIC_DIR = CORE_DIR / 'data/json/public'

# files needed in JSON dirs to ensure proper running of all functions
JSON_PRIVATE_FILES = ['standards.json', 'lightsail_server_info.json', 'bouldair_server_info.json']
JSON_PUBLIC_FILES = ['zug_long_plot_info.json', 'zug_plot_info.json']

JSON_FILES = (
    [JSON_PRIVATE_DIR / file for file in JSON_PRIVATE_FILES]
    + [JSON_PUBLIC_DIR / file for file in JSON_PUBLIC_FILES]
)

# check for existence of needed JSON files
for file in JSON_FILES:
    if not file.exists():
        print(f'WARNING: File {file} does not exist in project. Certain functions will not work.')

# path data from json file, consider temporary
try:
    PATHS_DATA = json.loads((JSON_PRIVATE_DIR / 'paths.json').read_text())
    REMOTE_BASE_PATH = PATHS_DATA.get('lightsail_base')  # base path for files on the remote AWS Lightsail instance
    BOULDAIR_BASE_PATH = PATHS_DATA.get('bouldair_base')  # base path on remote Bouldair website
except FileNotFoundError:
    print('WARNING: Could not load path data for remote connections. Connecting to server and website will not work.')

# static XLSX sheet containing data from 2013 - 2017
HISTORIC_DATA_SHEET = CORE_DIR / 'data/sheets/private/INSTAAR_mixing_ratios.xlsx'

# maintained list of directories needed at runtime; may require manual updating
_needed_dirs = [LOG_DIR, GCMS_DIR, DAILY_DIR, PROCESSOR_LOGS_DIR, MR_PLOT_DIR, PA_PLOT_DIR, STD_PA_PLOT_DIR,
                FULL_PLOT_DIR, LOG_PLOT_DIR, DAILY_PLOT_DIR, JSON_PRIVATE_DIR, JSON_PUBLIC_DIR]

# check for and create necesssary dirs
# for d in _needed_dirs:
#     if not d.exists():
#         d.mkdir()
#         print(f'Directory {d} created at runtime.')
