import os
from pathlib import Path

__all__ = ['list_files_recur', 'scan_and_create_dir_tree', 'get_all_data_files', 'get_subsubdirs']


def list_files_recur(path):
    """
    Cheater function that wraps path.rglob().

    :param Path path: path to list recursively
    :return list: list of Path objects
    """
    files = []
    for file in path.rglob('*'):
        files.append(file)

    return files


def scan_and_create_dir_tree(path, file=True):
    """
    Creates all the necessary directories for the file at the end of path to be created.

    When specified with a filepath to a file or folder, it creates directories until the path is valid.

    :param Path path: must end with a filename, else the final directory won't be created
    :param bool file: Boolean, does the given path end with a file? If not, path.parts[-1] will be created
    :return None:
    """

    parts = path.parts
    path_to_check = Path(parts[0])

    for i in range(1, len(parts)):
        if not path_to_check.exists():
            path_to_check.mkdir()
        path_to_check = path_to_check / parts[i]

    if file:
        pass
    else:
        if not path_to_check.exists():
            path_to_check.mkdir()


def get_all_data_files(path, filetype):
    """
    Recursively search the given directory for .xxx files.

    :param Path path: Path to search
    :param str filetype: str, ".type" of file to search for
    :return list: list of file-like Path objects
    """
    files = list_files_recur(path)
    files[:] = [file for file in files if filetype in file.name]

    return files


def get_subsubdirs(path):
    """
    Get the second-level subdirectories of the given path.

    If given path 'a/b', a sample return would be ['a/b/c/d', 'a/b/c/d2', 'a/b/c/etc']

    :param str path:
    :return list: list containing Path instances for all paths found two levels below the supplied path
    """
    leveltwo_subdirs = []
    immediate_subdirs = [os.scandir(subdir) for subdir in os.scandir(path) if Path(subdir).is_dir()]

    for scan in immediate_subdirs:
        for subdir in scan:
            leveltwo_subdirs.append(Path(subdir)) if Path(subdir).is_dir() else None

    return leveltwo_subdirs
