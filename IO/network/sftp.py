import json
from stat import S_ISDIR
from itertools import chain

import paramiko

from utils import gen_isempty
from settings import JSON_PRIVATE_DIR

__all__ = ['connect_to_lightsail', 'connect_to_bouldair', 'list_remote_files',
           'list_remote_files_recur', 'send_files_sftp']


def open_sftp_from_json(filepath):
    """
    With a given filepath, create an open SFTP client to the details provided in the JSON file at filepath.

    :param Path filepath: pathlib Path (or str) to a json file containing the necessary information to connect.
    :return:
    """
    with open(filepath, 'r') as file:
        server_info = json.loads(file.read())

    key = paramiko.RSAKey.from_private_key_file(server_info.pop('pem_file'))  # grab pem_file and remove from dict
    server_info['pkey'] = key

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(**server_info)
    client.get_transport().window_size = 3 * 1024 * 1024  # speed modification

    return client.open_sftp()


def connect_to_lightsail():
    """
    Uses Paramiko to create a connection to Brendan's instance. Relies on authetication information from a JSON file.

    :return SFTP_Client:
    """
    return open_sftp_from_json(JSON_PRIVATE_DIR / 'lightsail_server_info.json')


def connect_to_bouldair():
    """
    Uses Paramiko to create a connection to the Bouldair website.

    Relies on authetication information from a JSON file.
    :return SFTP_Client:
    """
    return open_sftp_from_json(JSON_PRIVATE_DIR / 'bouldair_server_info.json')


def list_remote_files(con, directory):
    """
    List the files and folders in a remote directory using an active SFTPClient from Paramiko

    :param SFTPClient con: an active connection to an SFTP server
    :param str directory: the directory to search
    :return tuple: (generator, generator) the files and directories as separate generators
    """
    all_files = [file for file in con.listdir_attr(directory)]

    files = []
    dirs = []

    for file in all_files:
        file.path = directory + f'/{file.filename}'  # ad-hoc add the remote filepath since Paramiko ignores this?!

        dirs.append(file) if S_ISDIR(file.st_mode) else files.append(file)

    files = (file for file in files)  # create and return generators instead
    dirs = (dir_ for dir_ in dirs)

    return files, dirs


def list_remote_files_recur(con, directory, files=None, dirs=None):
    """
    List all remote files, recursively through all directories in the given directory.

    :param SFTPClient con: an active SFTP connection
    :param str directory: directory to search for files and folders
    :param generator files: optional, file generator to append to with chain()
    :param generator dirs: optional, directory generator to append to with chain()
    :return generator: files; a generator of all the SFTPAttribute files
    """
    if not files and not dirs:
        files, dirs = list_remote_files(con, directory)

    dirs, dirs_is_empty = gen_isempty(dirs)

    if not dirs_is_empty:
        directory_to_check = None
        for d in dirs:
            directory_to_check = d.path
            new_files, new_dirs = list_remote_files(con, directory_to_check)
            files = chain(files, new_files)
            dirs = chain(dirs, new_dirs)
        return list_remote_files_recur(con, directory_to_check, files=files, dirs=dirs)
    else:
        return files


def send_files_sftp(con, filepaths, remote_path):
    """
    Send a list of files to the provided remote path via SFTP.

    Unspecified (read: all) exceptions result in the remaining files not uploading.

    :param con: a connected Paramiko client
    :param list filepaths: list of pathlib Path objects
    :param str remote_path: remote path to send all files to
    :return list: list of booleans of which plots uploaded sucessfully
    """

    bools = []
    try:
        con.chdir(remote_path)

        for file in filepaths:
            try:
                con.put(str(file), file.name)
                bools.append(True)
            except Exception:
                bools.append(False)

    except Exception:
        while len(bools) < len(filepaths):
            bools.append(False)

    return bools
