from pathlib import Path
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean

from IO.db import Base

__all__ = ['Config', 'FileToUpload']


class Config(Base):
    """
    A generic storage container for state and information about a processor.

    Configs are kept in the core database, and not every column is used by every processor. Some are used loosely,
    while others were designed specifically for the processor they're used exclusively in. Some processors rely on state
    for performance or continuity concerns, e.g. a plotting processor needs to know if new data has been committed to
    the database, so last_data_date indicates the last point of data that it plotted. If a quick check indicates no new
    data exists, it will exit and not create a new plot. Similar catches exist for not reading a file that hasn't
    changed size (filesize attr), or only reading new lines of a file (startline).

    Default values are given so only the necessary new values need to be given for init. Essentially any or none of the
    traits persisted to the database can be used. For instance, configs for plotters will likely use the last_data_date
    to indicate the last point of data they plotted, but would not use the filesize or pa_startline attributes which
    are used primarily by file readers.
    """
    __tablename__ = 'config'

    id = Column(Integer, primary_key=True)

    processor = Column(String, unique=True)  # only one config per processor
    filesize = Column(Integer)
    startline = Column(Integer)
    last_data_date = Column(DateTime)
    days_to_plot = Column(Integer)

    def __init__(self, processor=None, filesize=0, startline=0, last_data_date=datetime(1900, 1, 1), days_to_plot=7):
        """
        Create a config to persist details and state for a processor, potentially with all default arguments.

        :param str processor: Unique string identifier for the processor. Usually a plain-text name.
        :param int filesize: Last-accessed filesize of a file for the processor to determine if it's been updated.
        :param int startline: Line to begin reading file from. Used mostly for text-processing processors.
        :param datetime last_data_date: Date of the recent data point used by the processor; also generic date storage.
        :param int days_to_plot: Number of days that should be plotted prior to the last point of data.
        """
        self.processor = processor
        self.filesize = filesize
        self.startline = startline
        self.last_data_date = last_data_date
        self.days_to_plot = days_to_plot


class FileToUpload(Base):
    """
    A register for queueing files that will be uploaded to the webserver.

    FileToUploads are used to register created plots, files, etc as ready to upload in the core database. For instance,
    plots will be created by a plotting processor, then registered as ready to upload using a FileToUpload. These can
    then be checked and uploaded from their local path to the designated path on the remote server. In order for a file
    to be uploaded, it must have staged == True, otherwise it merely sits in the queue and will be ignored.
    """
    __tablename__ = 'stagedfiles'

    id = Column(Integer, primary_key=True)

    staged = Column(Boolean)
    _path = Column(String, unique=True)
    remote_path = Column(String)
    _name = Column(String)

    def __init__(self, path, remote_path, staged):
        """
        Create a file in the queue that should be uploaded from it's local path to the given remote path.

        :param Path path: local file path, persisted as a string but set/returned as Path
        :param Path remote_path: remote file path to be sent to, persisted as a string but set/returned as Path
        :param bool staged: True if the file is queued and ready to be uploaded, False if not
        """
        self.path = path
        self.remote_path = remote_path
        self.staged = staged

    @property
    def path(self):
        """Create a Path object from the string of the path kept in the database."""
        return Path(self._path)

    @path.setter
    def path(self, value):
        """Set the string-path as the resolved value of the input Path, set _name to Path.name simultaneously"""
        self._path = str(value.resolve())
        self._name = value.name

    @property
    def name(self):
        """Get the name of the Path, e.g. file.txt"""
        return self._name
