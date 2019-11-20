import os
import json
import traceback

from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

from settings import CORE_DIR, daily_dir, log_dir, gcms_dir
from utils import search_for_attr_value
from IO import Base, connect_to_db, get_all_data_files
from processing.file_io import read_daily_file, read_log_file, read_gcms_file
from IO.db.models import Config, OldData, DailyFile, LogFile, Integration, Standard, Quantification

__all__ = ['load_all_dailies', 'load_all_logs', 'load_all_integrations', 'load_standards', 'load_historic_data']


def load_all_dailies(logger):
    """
    Process all daily files in daily folder.

    Create DailyFile objects and compare to those in the database. Any new ones are processed and new Daily instances
    are committed.

    :param logger: Active logger that function should log to
    :return bool: True if it exits without issue/concern
    """
    logger.info('Running load_all_dailies()')

    try:
        engine, session = connect_to_db('sqlite:///zugspitze.sqlite', CORE_DIR)
        Base.metadata.create_all(engine)
    except Exception as e:
        print(f'Connecting to DB failed for reason {e.args}.')
        print(f'The full traceback is {traceback.format_exc()}')
        return

    daily_files_in_db = session.query(DailyFile).all()

    daily_files = [DailyFile(path) for path in sorted(get_all_data_files(daily_dir, '.txt'))]

    new_files = []

    for file in daily_files:
        file_in_db = search_for_attr_value(daily_files_in_db, 'path', file.path)

        if not file_in_db:
            new_files.append(file)
            logger.info(f'File {file.name} added for processing.')
        else:
            if file.size > file_in_db.size:
                logger.info(f'File {file_in_db.name} added to process additional data.')
                new_files.append(file_in_db)

    if new_files:
        for file in new_files:
            dailies = read_daily_file(file.path)
            file_daily_dates = [d.date for d in file.entries]
            file.entries.extend([d for d in dailies if d.date not in file_daily_dates])
            file.size = file.path.stat().st_size
            session.merge(file)
            logger.info(f'File {file.name} processed for daily data.')

        session.commit()

    session.close()
    engine.dispose()
    return True


def load_all_logs(logger):
    """
    Process all logfiles in the log directory.

    Create LogFiles from all files in directory and check against database. Any new ones are processed in and committed.

    :param logger: Active logger that function should log to
    :return bool: True if it exits without issue/concern
    """
    logger.info('Running load_all_logs()')

    try:
        engine, session = connect_to_db('sqlite:///zugspitze.sqlite', CORE_DIR)
        Base.metadata.create_all(engine)
    except Exception as e:
        print(f'Connecting to DB failed for reason {e.args}.')
        print(f'The full traceback is {traceback.format_exc()}')
        return

    logfiles = sorted([Path(file) for file in os.scandir(log_dir) if 'l.txt' in file.name])

    logs = []
    for file in logfiles:
        logs.append(LogFile(**read_log_file(file)))
    # TODO: The below is a common pattern. Re-factor into a function that splits into sets etc and use elsewhere
    log_dates = [log.date for log in logs]
    logs_in_db = session.query(LogFile.date).filter(LogFile.date.in_(log_dates)).all()
    logs_in_db[:] = [log.date for log in logs_in_db]

    for log in logs:
        if log.date not in logs_in_db:
            logs_in_db.append(log.date)
            session.add(log)
            logger.info(f'Log for {log.date} added.')

    session.commit()
    return True


def load_all_integrations(logger):
    """
    Process all integration_results.txt files in GCMS directory.

    Create Integrations from all files in directory and check against database. Any new ones are processed in and
    committed.

    :param logger: Active logger that function should log to
    :return bool: True if it exits without issue/concern
    """
    logger.info('Running load_all_integrations()')

    try:
        engine, session = connect_to_db('sqlite:///zugspitze.sqlite', CORE_DIR)
        Base.metadata.create_all(engine)
    except Exception as e:
        print(f'Connecting to DB failed for reason {e.args}.')
        print(f'The full traceback is {traceback.format_exc()}')
        return

    all_results = sorted(get_all_data_files(gcms_dir, 'integration_results.txt'))

    integrations = []
    for file in all_results:
        integrations.append(Integration(**read_gcms_file(file)))

    integration_dates = [i.date for i in integrations]
    integrations_in_db = session.query(Integration.date).filter(Integration.date.in_(integration_dates)).all()
    integrations_in_db[:] = [i.date for i in integrations_in_db]

    for integration in integrations:
        if integration.date not in integrations_in_db:
            integrations_in_db.append(integration.date)
            session.add(integration)
            logger.info(f'Integration for {integration.date} added.')

    session.commit()
    return True


def load_standards(logger):
    """
    Read standards.json and parse for any new standards.

    Reads standards.json and parses into Standard objects that are then committed. New ones are added, but updated ones
    will need to be removed and then it will add it as new. Standards that were once used as working standards will have
    a start/end date attached to them while others will not. Some, like quantlist are used just to track all compounds
    that are quantified or vocs that tracks what compounds are considered vocs.

    :param logger: Active logger that function should log to
    :return bool: True if it exits without issue/concern
    """
    standards_filepath = CORE_DIR / 'data/json/private/standards.json'

    try:
        engine, session = connect_to_db('sqlite:///zugspitze.sqlite', CORE_DIR)
        Base.metadata.create_all(engine)
    except Exception as e:
        print(f'Connecting to DB failed for reason {e.args}.')
        print(f'The full traceback is {traceback.format_exc()}')
        return

    logger.info('Running load_standards()')

    standards_in_db = session.query(Standard.name).all()
    standards_in_db[:] = [s.name for s in standards_in_db]

    standards = json.loads(standards_filepath.read_text())

    for name, vals in standards.items():
        start_date = vals.get('start_date')
        end_date = vals.get('end_date')

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')

        standard = Standard(name, start_date, end_date)
        quantifications = []
        for compound, cert_value in vals.items():
            if compound not in ['start_date', 'end_date']:
                quantifications.append(Quantification(compound, cert_value, standard))

        if standard.name not in standards_in_db:
            session.merge(standard)  # cascades with merging all quantifications
            logger.info(f'Standard {standard.name} added.')

    session.commit()

    session.close()
    engine.dispose()

    return


def load_historic_data(logger):
    """
    Loads a modified file from Wei Wang with 2013 - 2017 mixing ratio data.

    Creates OldData objects by reading a provided spreadsheet and storing them in the database. The file is read once
    (when the Config has the default/unchanged date of (1900, 1, 1)), and will not be read again. Changes to the file
    can be processed by removing the Config 'HistoricData' from the database.

    :param logger: logging logger to record to
    :return: bool, True if ran corrected, False if exit on error
    """

    logger.info('Running load_historic_data()')
    try:
        engine, session = connect_to_db('sqlite:///zugspitze.sqlite', CORE_DIR)
    except Exception as e:
        logger.error(f'Error {e.args} prevented connecting to the database in load_historic_data()')
        return False

    config = session.query(Config).filter(Config.processor == 'HistoricData').one_or_none()
    if not config:
        config = Config(processor='HistoricData')
        config = session.merge(config)

    if config.last_data_date == datetime(1900, 1, 1):  # it's never been run before

        historic_sheet = CORE_DIR / 'data/sheets/private/INSTAAR_mixing_ratios.xlsx'

        old_data = pd.read_excel(historic_sheet, header=0, sheet_name='AmbientMixingRatio')
        old_data['Time stamp'] = old_data['Time stamp'].replace('--', np.nan)
        old_data['Time stamp'] = old_data['Time stamp'].str.lstrip()
        old_data.dropna(axis=0, subset=['Time stamp'], inplace=True)
        old_data.index = pd.to_datetime(old_data['Time stamp'])
        old_data.dropna(axis=1, how='all', inplace=True)

        compounds_to_plot = (session.query(Quantification.name)
                             .join(Standard, Quantification.standard_id == Standard.id)
                             .filter(Standard.name == 'quantlist').all())
        compounds_to_plot[:] = [q.name for q in compounds_to_plot]

        dates = [d.to_pydatetime() for d in old_data.index.to_list()]

        data = []
        for cpd in compounds_to_plot:
            try:
                compound_values = [c for c in old_data[cpd].values.tolist()]
            except KeyError:
                logger.warning(f'Compound {cpd} not found in historic data sheeet.')
                continue

            for date, val in zip(dates, compound_values):
                data.append(OldData(cpd, date, val))

        if data:
            data_dates = [d.date for d in data]
            data_in_db = session.query(OldData.date).filter(OldData.date.in_(data_dates)).all()
            data_in_db[:] = [d.date for d in data_in_db]
            for datum in data:
                if datum.date not in data_in_db:
                    # this allows all compounds for a single date to load on the initial run, then blocks all from
                    # being loaded any subsequent times
                    session.add(datum)

        config.last_data_date = datetime.now()
        session.merge(config)

    session.commit()
    session.close()
    engine.dispose()
    return True
