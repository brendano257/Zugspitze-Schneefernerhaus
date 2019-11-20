from models.common import FileToUpload

__all__ = ['add_or_ignore_plot']


def add_or_ignore_plot(file, core_session):
    """
    Queries database and adds a plot only if one with the same path doesn't already exist.

    :param Plot file: Plot instance to be added to database
    :param Session core_session: a connected sqlalchemy.Session object
    :return None:
    """
    # intentional abuse: avoiding doing str(path) after the property just gave path back Path(_path)
    # noinspection PyProtectedMember
    files_in_db = [f[0] for f in core_session.query(FileToUpload._path).all()]

    if str(file.path.resolve()) not in files_in_db:
        core_session.add(file)
    return
