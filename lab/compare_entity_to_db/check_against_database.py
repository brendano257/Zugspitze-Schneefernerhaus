"""
Added to test an abstracted version of checking any ORM class against the database to avoid integrity errors.

Several processors all rely on similar logic to check the database for identical dates or paths, this is to write and
test a function that can be generalized across those classes and replace several sets of duplicated code.
"""
import os
from pathlib import Path

from sqlalchemy.orm import Session

from utils import split_into_sets_of_n
from settings import DB_NAME, CORE_DIR, LOG_DIR, DAILY_DIR, GCMS_DIR
from IO.db import connect_to_db, Base, LogFile, Integration, Daily, DailyFile


def filter_for_new_entities(objs, orm_class, attr, session=None):
    """
    Filter a list of sqlalchemy class instances for only those that are unique along the provided attribute.

    :param objs:
    :param orm_class:
    :param attr:
    :param session:
    :return:
    """
    if not type(orm_class) is type(Base):
        msg = 'orm_class must be a declared sqlalchemy class'
        raise TypeError(msg)

    if not session:
        _, session = connect_to_db(DB_NAME, CORE_DIR)
    else:
        if not type(session) is type(Session):
            msg = 'Provided session must be an active sqlalchemy session'
            raise TypeError(msg)

    obj_attrs = [getattr(o, attr) for o in objs]

    obj_attr_sets = split_into_sets_of_n(obj_attrs, 750)  # avoid SQLite var limit of 1000

    objs_in_db = []
    for set_ in obj_attr_sets:
        db_attrs_from_set = session.query(orm_class).filter(getattr(orm_class, attr).in_(set_)).all()
        for item in db_attrs_from_set:
            objs_in_db.append(item)

    attrs_in_db = [getattr(e, attr) for e in objs_in_db]

    new_objs = []
    for obj in objs:
        if getattr(obj, attr) not in attrs_in_db:
            new_objs.append(obj)  # add new object to return list
            # adding the new obj attr to the check-against list is required to prevent duplicates in one batch
            attrs_in_db.append(getattr(obj, attr))

    return new_objs


def test_on_log_files():
    from processing.file_io import read_log_file

    logfiles = sorted([Path(file) for file in os.scandir(LOG_DIR) if 'l.txt' in file.name])

    logs = []
    for file in logfiles:
        logs.append(LogFile(**read_log_file(file)))

    print(f'LogFiles read: {len(logfiles)}')

    new_only = filter_for_new_entities(logs, LogFile, 'date')

    print(f'LogFiles returned: {len(new_only)}')

    for log in new_only:
        print(log.date)


def test_on_dailies():
    from IO import get_all_data_files

    daily_files = [DailyFile(path) for path in sorted(get_all_data_files(DAILY_DIR, '.txt'))]

    print(f'DailyFiles read: {len(daily_files)}')

    new_only = filter_for_new_entities(daily_files, DailyFile, '_path')

    print(f'DailyFiles returned: {len(new_only)}')

    for file in new_only:
        print(file.path)


if __name__ == '__main__':
    # test_on_log_files()  # returns only log dates not already in the database
    # test_on_dailies()

    pass
