import os
import json
import traceback

from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

from settings import CORE_DIR, JSON_PRIVATE_DIR, DB_NAME, DAILY_DIR, LOG_DIR, GCMS_DIR, HISTORIC_DATA_SHEET
from utils import search_for_attr_value
from IO import Base, connect_to_db, get_all_data_files, filter_for_new_entities
from processing.file_io import read_daily_file, read_log_file, read_gcms_file
from IO.db.models import Config, OldData, Daily, DailyFile, LogFile, Integration, Standard, Quantification

__all__ = ['run_JFJ_corrections']


def run_JFJ_corrections(logger):
    """
    Runs once and not again unless the database is re-made. For data from 3/1/2018 to 12/20/2019, it will correct
    CFC-11, CFC-12, and CFC-113 by a constant factor for each compound to reflect sample differences discovered after we
    started taking two samples per day.
    :param logger:
    :return:
    """
    logger.info('Running load_historic_data()')
    try:
        engine, session = connect_to_db(DB_NAME, CORE_DIR)
    except Exception as e:
        logger.error(f'Error {e.args} prevented connecting to the database in run_JFJ_corrections()')
        return False

    config = session.query(Config).filter(Config.processor == 'JFJCorrection').one_or_none()
    if not config:
        config = Config(processor='JFJCorrection')
        config = session.merge(config)

    if config.last_data_date == datetime(1900, 1, 1):  # it's never been run before
        """
        Correct for CFC-11, CFC-12 and CFC-113
        """
        pass

        config.last_data_date = datetime.now()
        session.merge(config)

    session.commit()
    session.close()
    engine.dispose()
    return True
