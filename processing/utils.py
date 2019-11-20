import logging
import datetime as dt

from pathlib import Path

from utils import search_for_attr_value, find_closest_date
from models import GcRun

__all__ = ['configure_logger', 'match_integrations_to_logs', 'blank_subtract', 'get_mr_from_run']


def configure_logger(rundir, name):
    """
    Create the project-specific logger. DEBUG and up is saved to the log, INFO and up appears in the console.

    :param Path rundir: Path to create log sub-path in
    :param str name: name for logfile
    :return Logger: logger object
    """
    logfile = Path(rundir) / f'processor_logs/{name}.log'
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(logfile)
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s -%(levelname)s- %(message)s')

    [H.setFormatter(formatter) for H in [ch, fh]]
    if not len(logger.handlers):
        _ = [logger.addHandler(H) for H in [ch, fh]]

    return logger


def match_integrations_to_logs(integrations, logs):
    """
    Matches any integrations and logs within sampletype specific tolerances.

    LogFiles are matched to Integrations if they're less than 50 minutes after to the Integration's date for samples of
    LogFile.sample_type of 0-5, LogFiles of type 6 can be +/- 45 minutes from the LogFile.

    :param list integrations: list of Integrations
    :param list logs: list of LogFiles
    :return list: list of GcRun objects, potentially empty
    """
    runs = []

    integration_dates = [i.date for i in integrations]

    for log in logs:
        if log.sample_type in [5, 4, 3, 2, 1, 0]:
            # samples (5), standards (3, 2, 1), and zero air (0) logs
            # should be 30-40 minutes before the Agilent acq. log date
            date, difference = find_closest_date(log.date, integration_dates, how='pos')
            if difference and difference < dt.timedelta(minutes=50):
                matched_integration = search_for_attr_value(integrations, 'date', date)
                if matched_integration:
                    runs.append(GcRun(log, matched_integration))
                else:
                    print(f'No integration found for log {log.date}.')
                    continue
            else:
                print(f'No integration found for log {log.date}.')
                continue

        elif log.sample_type == 6:
            # trap blanks (6) logs should be +/- 10 minutes from the Agilent aquisition date
            date, difference = find_closest_date(log.date, integration_dates, how='abs')
            if difference and (dt.timedelta(minutes=-45) < difference < dt.timedelta(minutes=45)):
                matched_integration = search_for_attr_value(integrations, 'date', date)
                if matched_integration:
                    runs.append(GcRun(log, matched_integration))
                else:
                    print(f'No integration found for log {log.date}.')
                    continue
            else:
                print(f'No integration found for log {log.date}.')
                continue

    return runs


def blank_subtract(run, compounds_to_subtract, session, blank=None, force_no_blank=False):
    """
    Find a matching blank, then subtract any compounds in compounds_to_subtract from the run.

    If the blank=None, it will find a blank with time limits, then go peak-by-peak in the run and find/subtract a blank
    value from the matched or provided blank. If run is blank, it can be subtracted with another supplied blank,
    but blanks (types 0|6) will otherwise not be matched.

    :param GcRun run: GcRun, the run to be blank subtracted
    :param list compounds_to_subtract: list, of compound names to be subtracted
    :param Session session: active Sqlalchemy session
    :param GcRun blank: the blank to subtract, defaults to None
    :param bool force_no_blank: If True, do not search for a blank to match.
        Allow no blank to be used and pass current values to corrected_pa for every compound.
    :return: run
    """

    run.blank = blank  # assign, even if None

    if not blank and run.type not in [0, 6] and not force_no_blank:
        close_blanks = (session.query(GcRun)
                        .filter(GcRun.type == 0)
                        .filter(GcRun.date >= run.date - dt.timedelta(hours=6),
                                GcRun.date < run.date + dt.timedelta(hours=6))
                        .all())

        match, delta = find_closest_date(run.date, [r.date for r in close_blanks], how='abs')
        run.blank = search_for_attr_value(close_blanks, 'date', match)  # will return None if not found

    if run.blank:
        blank_peaks = run.blank.compounds

        if blank_peaks:
            for peak in run.compounds:
                if peak.name in compounds_to_subtract:  # only blank-subtract VOCs (or a given subset)
                    matched_blank_peak = search_for_attr_value(blank_peaks, 'name', peak.name)

                    if matched_blank_peak:
                        if peak.pa is not None and matched_blank_peak.pa is not None:
                            peak.corrected_pa = peak.pa - matched_blank_peak.pa  # subtract the blank area
                            if peak.corrected_pa < 0:
                                peak.corrected_pa = 0  # catch negatives and set to 0
                        elif peak.pa is None:
                            peak.corrected_pa = None  # leave as None
                        elif matched_blank_peak.pa is None:
                            peak.corrected_pa = peak.pa  # subtract nothing
                        else:
                            peak.corrected_pa = peak.pa  # can we get here? Pass the value
                    else:
                        peak.corrected_pa = peak.pa
                else:
                    peak.corrected_pa = peak.pa
        else:
            for peak in run.compounds:
                peak.corrected_pa = peak.pa
    else:
        for peak in run.compounds:
            peak.corrected_pa = peak.pa

    run = session.merge(run)

    return run


def get_mr_from_run(run, name):
    """
    Inefficient helper function to pull mixing ratios from a GcRun.

    :param GcRun run: GcRun that has been quantified
    :param str name: name of compound to look up, eg "ethane"
    :return float: float or None; mixing ratio of the compound if quantified, else None
    """
    comp = search_for_attr_value(run.compounds, 'name', name)
    return comp.mr if comp else None
