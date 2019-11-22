from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from IO.db import Base
from settings import CORE_DIR, REMOTE_BASE_PATH

__all__ = ['LocalFile', 'RemoteFile']


class LocalFile(Base):
    """
    A database-persisted file representation used for comparing local and remote files.

    LocalFiles are used to keep track of local files needed for data analysis and compar against their related remote
    files to determine if any need to be downloaded. (The remote is considered authoratative for this project's
    purposes). They are related one to one with RemoteFiles.
    """
    __tablename__ = 'localfiles'

    remote_id = Column(Integer, ForeignKey('remotefiles.id'))
    remote = relationship('RemoteFile', uselist=False, back_populates='local')

    id = Column(Integer, primary_key=True)
    st_mtime = Column(Integer)
    path = Column(String, unique=True)
    relpath = Column(String)

    def __init__(self, st_mtime, path):
        """
        Create an instance using the filepath given and st_mtime given by the system.

        The incoming path is stripped to only the relative (to the base directory) before being persisted.

        :param int st_mtime: posix time the local file was last modified at
        :param str path: provided path on the local system
        """
        self.st_mtime = st_mtime
        self.path = path
        self.relpath = path.replace(str(CORE_DIR), '')


class RemoteFile(Base):
    """
    A database-persisted file representation used for comparing local and remote files.

    LocalFiles are used to keep track of local files needed for data analysis and compar against their related remote
    files to determine if any need to be downloaded. (The remote is considered authoratative for this project's
    purposes). They are related one to one with LocalFiles.
    """
    __tablename__ = 'remotefiles'

    local = relationship('LocalFile', uselist=False, back_populates='remote')

    id = Column(Integer, primary_key=True)
    st_mtime = Column(Integer)
    path = Column(String, unique=True)
    relpath = Column(String)

    def __init__(self, st_mtime, path):
        """
        Create an instance using the filepath given and st_mtime given by the system.

        The incoming path is stripped to only the relative (to the base remote directory) before being persisted.

        :param int st_mtime: posix time the local file was last modified at
        :param str path: provided path on the remote system
        """
        self.st_mtime = st_mtime
        self.path = path
        self.relpath = path.replace(REMOTE_BASE_PATH, '')