import os

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

__all__ = ['Base', 'connect_to_db', 'TempDir']

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
