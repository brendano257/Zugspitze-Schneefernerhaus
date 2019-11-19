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


def add_or_ignore_plot(file, core_session):
    """
    Queries database and adds a plot only if one with the same path doesn't already exist.

    :param Plot file: Plot instance to be added to database
    :param Session core_session: a connected sqlalchemy.Session object
    :return None:
    """
    files_in_db = [f[0] for f in core_session.query(FileToUpload._path).all()]

    if str(file.path.resolve()) not in files_in_db:
        core_session.add(file)
    return
