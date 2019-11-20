"""
Run any portion of the processing or all of it at once from the command line.
"""
import argparse
from datetime import datetime

from settings import PROCESSOR_LOGS_DIR
from processing import configure_logger
from processing.processors import *

parser = argparse.ArgumentParser(description='Run part of all of the Zugpsitze Runtime in sequence.')
parser.add_argument('-A', '--all', action='store_true')  # flag to run everything in sequence

args = parser.parse_args()

if args.all:
    """Run the entire process from start to end"""

    # get a logger and save to a file with the current datetime of the run start
    logger = configure_logger(PROCESSOR_LOGS_DIR, datetime.now().strftime('%Y_%m_%d_%H%M_run'))

    load_all_dailies(logger)
    load_all_logs(logger)
    load_all_integrations(logger)
    match_gcruns(logger)
    load_standards(logger)

    quantify_runs(logger)

    process_filters(logger)

    plot_new_data(logger)
    plot_logdata(logger)
    plot_dailydata(logger)
    plot_standard_and_ambient_peak_areas(logger)
    load_historic_data(logger)
    plot_history(logger)

    # check_send_files(logger)
