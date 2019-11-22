import os
import datetime as dt
from datetime import datetime

from settings import CORE_DIR, REMOTE_BASE_PATH
from IO import Base, connect_to_db, connect_to_lightsail, connect_to_bouldair, send_files_sftp
from IO import list_files_recur, list_remote_files_recur, scan_and_create_dir_tree
from IO.db.models import RemoteFile, LocalFile, FileToUpload
from utils import split_into_sets_of_n, search_for_attr_value

__all__ = ['retrieve_new_files', 'check_send_files']


def retrieve_new_files(logger):
    """
    Connect to an AWS Lightsail instance and compare local to remote files.

    Uses a local SQLite database as part of the project to track remote and local files, pulling only those with changed
    file sizes. Only gets GCMS data for this month and the month it was 7 days ago (if different) as an optimization.

    TODO: Need a better way of comparing local/remote paths; probably just a lookup or differencer? Local will
        always be prefixed with /data now...
        FOUND IT: relpath should be stripped properly in LocalFile...it currently is not.

    :param logger: Active logger that function should log to
    :return bool: True if it exits without issue/concern
    """
    logger.info('Running retrieve_new_files()')
    engine, session = connect_to_db('sqlite:///zugspitze.sqlite', CORE_DIR)
    Base.metadata.create_all(engine)

    con = connect_to_lightsail()

    paths_to_check = ['daily', 'log']

    date = datetime.now()
    paths_to_check.append(f'GCMS/{date.year}_{date.month:02}')  # check only this month's and last month's for speed

    month_ago = date - dt.timedelta(days=7)
    # go back one week in case it's been a few days and the last month still has data to retrieve

    if month_ago.month is not date.month:  # if it's a different month, add that to the checklist
        paths_to_check.append(f'GCMS/{month_ago.year}_{month_ago.month:02}')  # check

    for path in paths_to_check:
        logger.info(f'Processing {path} files.')
        local_path = CORE_DIR / f'data/{path}'
        remote_path = REMOTE_BASE_PATH + f'/{path}'

        all_remote_files = list_remote_files_recur(con, remote_path)  # get a list of all SFTPAttributes + paths

        all_local_files = [str(p) for p in list_files_recur(local_path)]  # get all local file paths

        new_remote_files = []
        for remote_file in all_remote_files:
            new_remote_files.append(RemoteFile(remote_file.st_mtime, remote_file.path))
        # create DB objects for all remote paths

        new_local_files = []
        for remote_file in all_local_files:
            new_local_files.append(LocalFile(os.stat(remote_file).st_mtime, remote_file))
        # create DB objects for all local paths

        remote_sets = split_into_sets_of_n([r.path for r in new_remote_files], 750)  # don't exceed 1K sqlite var limit
        local_sets = split_into_sets_of_n([l.path for l in new_local_files], 750)

        # loop through remote, then local filesets to check against DB and commit any new ones
        for Filetype, filesets, new_files in zip([RemoteFile, LocalFile],
                                                 [remote_sets, local_sets],
                                                 [new_remote_files, new_local_files]):
            paths_in_db = []
            for set_ in filesets:
                # noinspection PyUnresolvedReferences
                in_db = session.query(Filetype.path).filter(Filetype.path.in_(set_)).all()
                if in_db:
                    paths_in_db.extend([p.path for p in in_db])

            for file in new_files:
                if file.path in paths_in_db:
                    file_in_db = session.query(Filetype).filter(Filetype.path == file.path).one_or_none()
                    if file.st_mtime > file_in_db.st_mtime:
                        file_in_db.st_mtime = file.st_mtime
                        session.merge(file_in_db)
                else:
                    session.add(file)
            session.commit()  # commit at the end of each filetype

        # local and remote files are now completely up-to-date in the database
        files_to_retrieve = []
        remote_files = session.query(RemoteFile).order_by(RemoteFile.relpath).all()
        local_files = session.query(LocalFile).order_by(LocalFile.relpath).all()

        for remote_file in remote_files:
            if remote_file.local is None:
                local_match = search_for_attr_value(local_files, 'relpath', '/data' + remote_file.relpath)
                if local_match:
                    remote_file.local = local_match
                    if remote_file.st_mtime > local_match.st_mtime:
                        files_to_retrieve.append(remote_file)  # add the remote file to download if st_mtime is greater
                else:
                    files_to_retrieve.append(remote_file)  # add the remote file if there's no local copy (create later)
            else:
                if remote_file.st_mtime > remote_file.local.st_mtime:
                    files_to_retrieve.append(remote_file)

        logger.info(f'Remote files: {len(remote_files)}')
        logger.info(f'Local files: {len(local_files)}')
        logger.info(f'{len(files_to_retrieve)} files need updating or retrieval.')

        ct = 0
        for remote_file in files_to_retrieve:
            if remote_file.local is not None:
                con.get(remote_file.path, remote_file.local.path)  # get remote file and put in the local's path

                remote_file.local.st_mtime = remote_file.st_mtime  # update, then merge
                session.merge(remote_file)

                logger.info(f'Remote file {remote_file.relpath} was updated.')
                ct += 1
            else:
                new_local_path = CORE_DIR / 'data' / remote_file.relpath.lstrip('/')

                scan_and_create_dir_tree(new_local_path)  # scan the path and create any needed folders

                new_local_path = str(new_local_path)  # revert to string
                con.get(remote_file.path, new_local_path)  # get file and put in it's relative place

                new_local = LocalFile(remote_file.st_mtime, new_local_path)
                new_local.remote = remote_file

                session.add(new_local)  # create, relate, and add the local file that was transferred
                session.merge(remote_file)

                logger.info(f'Remote file {remote_file.relpath} was retrieved and added to local database.')
                ct += 1

            if not ct % 100:
                session.commit()  # routinely commit files in batches of 100
                logger.info(f'{ct} of {len(files_to_retrieve)} retrieved.')

        session.commit()

    con.close()
    session.close()
    engine.dispose()
    return True


def check_send_files(logger):
    """
    Sends all queued files to the Bouldair server for the website.

    :param logger: logging logger to record to
    :return: bool, True if ran correctly, False if exit on error
    """
    logger.info('Running check_send_files()')

    try:
        engine, session = connect_to_db('sqlite:///zugspitze.sqlite', CORE_DIR)
        con = connect_to_bouldair()
    except Exception as e:
        logger.error(f'Exception {e.args} prevented connection to the database in check_send_files()')
        return False

    files_to_upload = session.query(FileToUpload).filter(FileToUpload.staged == True)

    remote_dirs = set([f.remote_path for f in files_to_upload.all()])

    for remote_dir in remote_dirs:
        file_set = files_to_upload.filter(FileToUpload.remote_path == remote_dir).all()

        if file_set:
            paths_to_upload = [p.path for p in file_set]
            successes = send_files_sftp(con, paths_to_upload, remote_dir)

            for file, success in zip(file_set, successes):
                if success:
                    logger.info(f'File {file.name} uploaded to website.')
                    session.delete(file)
                else:
                    logger.warning(f'File {file.name} failed to upload.')

    session.commit()

    session.close()
    engine.dispose()

    con.close()

    return True
