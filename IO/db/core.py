import os

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from settings import CORE_DIR, DB_PROTO, DB_FILE

__all__ = ['Base', 'connect_to_db', 'TempDir', 'DBConnection']

# Sqlalchemy declarative base to be subclassed by all persisted types
Base = declarative_base()


class TempDir:
    """
    Context manager for working in a directory.
    """

    def __init__(self, path):
        self.old_dir = os.getcwd()
        self.new_dir = path

    def __enter__(self):
        os.chdir(self.new_dir)

    def __exit__(self, *args):
        os.chdir(self.old_dir)


def connect_to_db(engine_str, directory):
    """
    Takes string name of the database to create/connect to, and the directory it should be in.

    :param str engine_str: connection string for the database
    :param str directory: directory the database should be in
        **will create database if specified incorrectly (or intentionally different than existing)
    :return: engine, session
    """
    with TempDir(directory):
        engine = create_engine(engine_str)
    sessy = sessionmaker(bind=engine)
    sess = sessy()

    return engine, sess


class DBConnection:
    """
    DBConnection is a context manager for database connections to the primary database.

    Care should be taken that lazy queries are not made inside the context and then retrieved outside of the context.
    """
    def __init__(self, db_file=DB_FILE, directory=CORE_DIR):
        """
        :param str db_file: the filename of the database to be concatenated with it's directory
        :param Path directory: the Path to the database, excepting it's filename
        """
        self._db = db_file
        self._dir = directory

    @property
    def db_file(self):
        return self._db

    @property
    def directory(self):
        return self._dir

    def __enter__(self):
        self._engine = create_engine(DB_PROTO.format(self._dir / DB_FILE))
        self._session = sessionmaker(bind=self._engine)()
        return self._session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._session.close()
        self._engine.dispose()
