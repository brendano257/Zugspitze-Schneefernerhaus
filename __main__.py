"""
Run any portion of the processing or all of it at once from the command line.
"""
import argparse
from datetime import datetime

from settings import PROCESSOR_LOGS_DIR
from utils import configure_logger
from processing.processors import *


# get a logger and log to a file with the current datetime of the run start
logger = configure_logger(PROCESSOR_LOGS_DIR, datetime.now().strftime('%Y_%m_%d_%H%M_run'))

sequence = [
    retrieve_new_files,
    load_all_dailies,
    load_all_logs,
    load_all_integrations,
    load_standards,
    load_historic_data,
    match_gcruns,
    quantify_runs,
    process_filters,
    plot_new_data,
    plot_logdata,
    plot_dailydata,
    plot_standard_and_ambient_peak_areas,
    plot_history,
    check_send_files
]

run_one_desc = (
    'Run one or more specific functions from the Zugspitze runtime.\n'
    + "Use run-proc unless you know exactly what you're trying to accomplish.\n"
    + '\n'.join([f'\t{ind} - {f.__name__}' for ind, f in enumerate(sequence)])
)


def run(ergs):
    """
    Run the entire sequence, with the option to not upload or download files.

    :param ergs: arguments passed by calling subparser.func(args)
    :return None:
    """
    if ergs.no_download:
        sequence.pop(0)  # remove the first element (always the download function, retrieve_new_files)

    if ergs.no_upload:
        sequence.pop(-1)  # remove the last element (always the upload function, check_send_files)

    # Run the entire process from start to end
    for proc in sequence:
        proc(logger)


def run_proc(ergs):
    """
    Run a subset of categorical tasks, eg loading data files or uploading new files.

    Categories are somewhat arbitrary, but are grouped according to commond sets of tasks, such that if one wanted to
    load all the data, they would need only use the flag --load instead of flags for
    [load_all_dailies, load_all_logs, load_all_integrations, ...].

    :param ergs:
    :return:
    """

    if not any(vars(ergs.values())):  # check for at least one arg
        parser.error('No arguments provided.')

    if ergs.retrieve:
        retrieve_new_files(logger)

    if ergs.load:
        load_all_dailies(logger)
        load_all_logs(logger)
        load_all_integrations(logger)
        load_standards(logger)
        load_historic_data(logger)

    if ergs.match:
        match_gcruns(logger)

    if ergs.quantify:
        quantify_runs(logger)
        process_filters(logger)

    if ergs.plot:
        plot_new_data(logger)
        plot_logdata(logger)
        plot_dailydata(logger)
        plot_standard_and_ambient_peak_areas(logger)
        plot_history(logger)

    if ergs.send:
        check_send_files(logger)


def run_one(ergs):
    """
    Run individual functions by their given index in the sequence **sequentially**. Providing funcs out of order will
    NOT force them to be run non-sequentially.

    :param ergs: Args produced by parser.parse_args(), should include args.numbers = [...]
    :return None:
    """
    indices = (int(num) for num in ergs.numbers)

    # if not explictly asked to maintain the order they were given in, sort the provided numbers
    if not ergs.ordered:
        indices = sorted(indices)

    procs = [sequence[index] for index in indices]

    for proc in procs:
        proc(logger)


parser = argparse.ArgumentParser(
    prog='zugspitze',
    description='Run part of or all of the Zugpsitze runtime in sequence.'
)

subparsers = parser.add_subparsers(required=True,
                                   title='Mandatory Subcommands',
                                   help='Run the entire sequence (run), a set of processes (run-proc), '
                                        + 'or one to many of the individual functions (one).')

# ----------------- Parser for running everything, optionally not downloading or uploading ----------------- #
parser_run = subparsers.add_parser('run',
                                   description='Run the entire sequence, with the ability to opt-out of uploading.')

parser_run.add_argument('-D', '--no-download', action='store_true', dest='no_download',
                        help='Do not download new files when running all.')
parser_run.add_argument('-U', '--no-upload', action='store_true', dest='no_upload',
                        help='Do not upload any staged files when running all.')

# if parser_run is used, run is set as it's func, such that args.func(args) can be called
parser_run.set_defaults(func=run)

# ----------------- Parser for running logical groups of functions ----------------- #
parser_run_proc = subparsers.add_parser('run-proc',
                                        description='Run a subset of processes, such as loading data or plotting.'
                                        + ' Order of input is ignored.'
                                        + ' Any added processes are run in their proper order, and are listed below '
                                        + "in the order they'll be run in.")

parser_run_proc.add_argument('-R', '--retrieve', action='store_true', dest='retrieve',
                             help='Run function(s) for retrieving new files from the Lightsail server.')

parser_run_proc.add_argument('-L', '--load', action='store_true', dest='load',
                             help='Run functions for reading all data in from files.')

parser_run_proc.add_argument('-M', '--match', action='store_true', dest='match',
                             help='Run functions for matching any existing data into GcRuns.')

parser_run_proc.add_argument('-Q', '--quantify', action='store_true', dest='quantify',
                             help='Run functions for quantifying data. Does NOT including matching existing data. '
                             + 'Call --match and --quantify to process, then quantify existing data.')

parser_run_proc.add_argument('-P', '--plot', action='store_true', dest='plot',
                             help='Run functions for plotting sequentially. Will queue plots for uploading if created.')

parser_run_proc.add_argument('-S', '--send', action='store_true', dest='send',
                             help='Run function(s) for uploading any staged files to the Bouldair Website.')

parser_run_proc.set_defaults(func=run_proc)

# ------------------ Parser for running functions individually ------------------ #
parser_run_one = subparsers.add_parser('run-one',
                                       formatter_class=argparse.RawTextHelpFormatter,
                                       description=run_one_desc)

parser_run_one.add_argument('-N', '--number', nargs='+', required=True, dest='numbers',
                            help=f'Choose a number from 0 - {len(sequence) - 1} to run that process.')

parser_run_one.add_argument('-O', '--ordered', action='store_true', dest='ordered',
                            help='Force arguments to be run in the order they were provided. '
                            + f'Eg "zugspitze run-one {len(sequence) - 1} 0" will upload files, THEN retrieve new ones.'
                            + 'This should rarely, if ever, be necessary.')

parser_run_one.set_defaults(func=run_one)

# ----------------------------- Finally, run it all ----------------------------- #
args = parser.parse_args()
args.func(args)
