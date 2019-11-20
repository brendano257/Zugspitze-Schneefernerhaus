from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from models.common import TempDir

__all__ = ['Base', 'connect_to_db']

# Sqlalchemy declarative base to be subclassed by all persisted types
Base = declarative_base()


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
