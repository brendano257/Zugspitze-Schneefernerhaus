import json
import traceback
import datetime as dt

from datetime import datetime

from settings import CORE_DIR, DB_NAME, FILTER_DIRS, JSON_PRIVATE_DIR
from IO import Base, connect_to_db
from IO.db.models import Config, Compound, LogFile, Integration, GcRun, Standard, Quantification
from processing import match_integrations_to_logs
from utils import search_for_attr_value, find_closest_date

__all__ = ['match_gcruns', 'quantify_runs', 'process_filters']


def match_gcruns(logger):
    """
    Processes all unmarried Integrations and LogFiles, looking for matches with tolerances.

    :param logger: Active logger that function should log to
    :return bool: True if it exits without issue/concern
    """
    logger.info('Running match_gcruns()')

    try:
        engine, session = connect_to_db(DB_NAME, CORE_DIR)
        Base.metadata.create_all(engine)
    except Exception as e:
        print(f'Connecting to DB failed for reason {e.args}.')
        print(f'The full traceback is {traceback.format_exc()}')
        return

    integrations = session.query(Integration).filter(Integration.status == 'single').order_by(Integration.date).all()

    logfiles = session.query(LogFile).filter(LogFile.status == 'single').order_by(LogFile.date).all()

    runs = match_integrations_to_logs(integrations, logfiles)

    if runs:
        run_dates = {r.date for r in runs}
        run_dates_in_db = session.query(GcRun).filter(GcRun.date.in_(run_dates)).all()
        run_dates_in_db = {r.date for r in run_dates_in_db}

        for r in runs:
            if r.date not in run_dates_in_db:
                session.merge(r)
                run_dates_in_db.add(r.date)
                logger.info(f'GcRun for {runs.date} added.')

        session.commit()

    session.close()
    engine.dispose()

    return


def quantify_runs(logger):
    """
    Iterates through unquantified GcRuns and attempts to quantify them.

    Queries and iterates through all unquantified GcRuns. If a working standard is found within six hours of that sample
    it will use that standard to quantify it.

    :param logger: Active logger that function should log to
    :return bool: True if it exits without issue/concern
    """
    logger.info('Running quantify_runs()')

    try:
        engine, session = connect_to_db(DB_NAME, CORE_DIR)
        Base.metadata.create_all(engine)
    except Exception as e:

        print(f'Connecting to DB failed for reason {e.args} in quantify_runs().')
        print(f'The full traceback is {traceback.format_exc()}')
        return

    runs = session.query(GcRun).filter(GcRun.quantified == False).all()

    voc_list = (session.query(Quantification.name)
                .join(Standard, Quantification.standard_id == Standard.id)
                .filter(Standard.name == 'vocs').all())
    voc_list[:] = [q.name for q in voc_list]

    if not voc_list:
        logger.error('Could not load VOC list from Standards.')
        return False

    std = None  # no standard found yet

    for run in runs:
        # call blank subtract with no provided blank (it will find one if possible), and don't commit changes
        run.blank_subtract(session=session, compounds_to_subtract=voc_list, commit=False)

    # commit once after all runs are done for performance
    session.commit()

    runs = session.query(GcRun).filter(GcRun.quantified == False).all()

    for run in runs:
        # find the certified standard that applies to this time period
        if not std or not (std.start_date <= run.date < std.end_date):
            std = (session.query(Standard)
                   .filter(Standard.start_date <= run.date, Standard.end_date > run.date)
                   .one_or_none())
        if not std:
            continue
        else:
            run.standard = std

        # find the working standard if this run wasn't one
        if run.type not in {1, 2, 3}:
            close_standards = (session.query(GcRun)
                               .filter(GcRun.type.in_({1, 2, 3}))
                               .filter(GcRun.date >= run.date - dt.timedelta(hours=6),
                                       GcRun.date < run.date + dt.timedelta(hours=6))
                               .all())

            match, delta = find_closest_date(run.date, [r.date for r in close_standards], how='abs')
            run.working_std = search_for_attr_value(close_standards, 'date', match)

            if run.standard:
                run.quantify()
            else:
                logger.warning(f'No Standard found for the GcRun at {run.date}')

            session.merge(run)

    session.commit()
    session.close()
    engine.dispose()


def process_filters(logger):
    """
    Read any filter files and process them to filter any questionable data.

    Filters are kept in /filters, but only the subset of /filters/final and /filters/unprocessed are processed on each
    run though this function. First, ALL compounds in the data are flagged as unfiltered. This refresh prevents
    filtered data persisting despite being removed from filter files, though it requires all files being processed each
    run. Next, all filter files are parsed and all points contained in them are flagged for specific compounds or 'all'.

    Rules for filtering:
        - The files containing filter objects is authoratative. Calls to this function are regular and will refresh from
            the file, removing all filters, then re-adding them to ensure the file is the only reason one can be
            filtered.
        - Scripts seeking to filter should append to the files or add new ones (see rule 1)
        - Filters are a large JSONized dictionary {'datestring': [compound1tofilter, compound2tofilter, etc]}
        - 'all' is an acceptable compound keyword - more may be added
        - Filters can overlap; eg if both filter the same compound on the same date, that's okay.

    :param logger: Active logger that function should log to
    :return bool: True if it exits without issue/concern
    """

    logger.info("Running process_filters()")

    try:
        engine, session = connect_to_db(DB_NAME, CORE_DIR)
        Base.metadata.create_all(engine)
    except Exception as e:

        print(f'Connecting to DB failed for reason {e.args} in process_filters().')
        print(f'The full traceback is {traceback.format_exc()}')
        return

    json_files = []
    for d in FILTER_DIRS:
        json_files.extend([f for f in d.iterdir() if f.is_file() and f.suffix == '.json'])

    # TODO: Ideally, only process filters when one or more has been changed; but all must be processed, per below

    session.query(Compound).update({Compound.filtered: False})
    session.commit()  # un-filter ALL data prior to editing
    # this is desired since only adding filters means removed ones in the JSON
    # file will still be filtered in the database

    for file in json_files:
        if not file.exists():
            logger.error('JSON file could not be found for filtered data. Filter not processed')
            continue

        filter_name = "/".join(file.parts[-2:])
        proc_name = f'Filter::{filter_name}'  # use filename and containing dir to prevent collisions

        config = session.query(Config).filter(Config.processor == proc_name).one_or_none()

        if not config:
            config = Config(processor=proc_name)  # accept all other defaults
            config = session.merge(config)

        logger.info(f'Filtered data for {filter_name} was modified or added.')

        with open(file, 'r') as f:
            filters = json.loads(f.read())

        for date, compound_list in filters.items():
            date = datetime.strptime(date[:16], '%Y-%m-%d %H:%M')  # cut string to first 16 to remove extra text

            gc_run = (session.query(GcRun)
                      .filter(GcRun.date >= date, GcRun.date <= date + dt.timedelta(minutes=1))
                      .one_or_none())  # search within one minute of date

            if gc_run:
                for compound in compound_list:
                    if compound == 'all':
                        for matched_compound in gc_run.compounds:
                            matched_compound.filtered = True
                    else:
                        matched_compound = search_for_attr_value(gc_run.compounds, 'name', compound)

                        if matched_compound:
                            matched_compound.filtered = True
                            session.merge(matched_compound)
                        else:
                            logger.warning(f"Compound {compound} was filtered in the JSON file for GcRun with {date} "
                                           + "but was not present in the GcRun.")
            else:
                logger.warning(f"GcRun with date {date} was not found in the record, "
                               + "but was present in the JSON filter file.")

        session.merge(config)

        session.commit()

    # Clean Filters
    # Since filter files are loaded and put in the Config table, they must be checked at runtime to see if they
    # still exist. Non-existent ones will be removed from the db and warned in the console/logging
    all_filter_configs = (session.query(Config)
                          .filter(Config.processor.like('Filter::%'))
                          .all())

    for config in all_filter_configs:
        file = JSON_PRIVATE_DIR / f'filters/{config.processor.replace("Filter::", "")}'  # recreate filename
        if not file.exists():
            logger.warning(f'Filter file {"/".join(file.parts[-2:])} was not found so its config was removed.')
            session.delete(config)
        session.commit()

    session.close()
    engine.dispose()

    return True
