from sqlalchemy.orm import Session

from utils import split_into_sets_of_n
from settings import DB_NAME, CORE_DIR
from IO.db.models import FileToUpload
from IO.db import connect_to_db, Base

__all__ = ['add_or_ignore_plot', 'filter_for_new_entities']


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


def filter_for_new_entities(objs, orm_class, attr, session=None):
    """
    Filter a list of sqlalchemy class instances for only those whose attribute attr are not already in the databse.

    The provided list of objects is checked against the database by returning only objects whose specified attribute
    does not match any entry in the database for that class. Frequently used with paths or dates to determine what
    unique data to add to and commit to the database.

    :param Sequence objs: sequence of objects to check against the database
    :param orm_class: Declared class of the provided objects
    :param str attr: Attribute of the orm class to compare against the database
        **IntegrityErrors are completely possible if attr is not actually a unique-constrained attribute of orm_class
    :param Session session: an active sqlalchemy session to use; created and closed internally if not given
    :return list: potentially empty list of all objs that are not already present in the database
    :raises TypeError: if session is not a sqlalchemy session, or the orm_class is not a declared sqlalchemy class
    """
    if not type(orm_class) is type(Base):
        msg = 'orm_class must be a declared sqlalchemy class'
        raise TypeError(msg)

    if not session:
        _, session = connect_to_db(DB_NAME, CORE_DIR)
        close_on_exit = True
    else:
        if not isinstance(session, Session):
            msg = 'Provided session must be an active sqlalchemy session'
            raise TypeError(msg)
        close_on_exit = False

    obj_attrs = [getattr(o, attr) for o in objs]
    obj_attr_sets = split_into_sets_of_n(obj_attrs, 750)  # avoid SQLite var limit of 1000

    objs_in_db = []
    for set_ in obj_attr_sets:
        db_objs_from_set = session.query(orm_class).filter(getattr(orm_class, attr).in_(set_)).all()
        for item in db_objs_from_set:
            objs_in_db.append(item)

    attrs_in_db = {getattr(e, attr) for e in objs_in_db}

    new_objs = []
    for obj in objs:
        if getattr(obj, attr) not in attrs_in_db:
            new_objs.append(obj)  # add new object to return list
            # adding the new obj attr to the check-against list is required to prevent duplicates in one batch
            attrs_in_db.add(getattr(obj, attr))

    if close_on_exit:
        session.close()

    return new_objs
