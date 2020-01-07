from pathlib import Path

from IO.db.models import Config, FileToUpload, Compound, LogFile, Daily, DailyFile, Integration, GcRun, OldData
from IO.db.models import Quantification, Standard, SampleQuant, LocalFile, RemoteFile

from IO.db import connect_to_db
from settings import DB_NAME, CORE_DIR


def test_all_common_reprs():
    config = Config()
    file = FileToUpload(Path('/home/local/path'), Path('/home/server/'), False)

    print(repr(config))
    print(repr(file))


def test_basic_data_types():
    _, session = connect_to_db(DB_NAME, CORE_DIR)

    for cls in (Compound, LogFile, Daily, DailyFile, Integration, GcRun, OldData, Quantification, Standard):
        instances = session.query(cls).limit(5).all()
        print(f'\n{cls.__name__}: ')
        for instance in instances:
            print(repr(instance))

    runs = session.query(GcRun).limit(5).all()
    quant =  SampleQuant(*runs)

    print(repr(quant))


def test_all_network_reprs():
    local_file = LocalFile(123456, '/home/local/path')
    remote_file = RemoteFile(123456, '/home/remote/path')

    print(repr(local_file))
    print(repr(remote_file))


def main():
    print('Common:')
    test_all_common_reprs()
    print('\nNetwork:')
    test_all_network_reprs()
    print('\nBasic Data:')
    test_basic_data_types()


if __name__ == '__main__':
    main()
