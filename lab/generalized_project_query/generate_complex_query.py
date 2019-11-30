"""
INACTIVE/MOVED:
    Playing with extracting relationships from sqlalchemy was sucessful and was added as meta.py in IO.db
        The relations variable, also printable with print_database_meta is now available project-wide
    get_query() now has a permanent home in reporting.reports as abstract_query()

An experiment with generating custom queries with only a list of parameters and filters, letting the function handle
any joins that are necessary.
"""

from settings import CORE_DIR, DB_NAME
from IO.db import GcRun, Integration, Compound, LogFile, connect_to_db

from IO.db.meta import relations

# from IO.db.meta import print_database_meta
# print_database_meta()  # optionally take a peak at the project structure


def get_query(params, filters):
    """
    Create a query with only a list of parameters to grab, and filters to apply after

    Use SQLalchemy internals to poke around and get classes, etc
    """
    engine, session = connect_to_db(DB_NAME, CORE_DIR)

    q = session.query(*params)  # kick off the query

    classes = []
    for p in params:
        parent_class = p.parent.class_
        classes.append(parent_class) if parent_class not in classes else None # need order, so hack around a set...


    base = classes.pop(0)  # grab first class from list
    linked = [base]  # the first class is inherently already in the join-chain

    if classes:  # any more classes?
        for c in classes:
            relations_for_c = relations.get(c.__name__)

            if not relations_for_c:
                msg = f'{c.__name__} does not have any defined relationships.'
                raise NotImplementedError(msg)

            relation = relations_for_c.get(base.__name__)

            if relation:
                q = q.join(c, relation.key == relation.fkey)
            else:
                msg = f'{c.__name__} is not directly related to {base} in the schema.'
                raise NotImplementedError(msg)

    for f in filters:
        q = q.filter(f)

    return q.all()[:10]


from datetime import datetime

params = [GcRun.id, GcRun.date, LogFile.sample_time, LogFile.sample_type,
          Integration.filename, Compound.id, Compound.name, Compound.mr]
filters = [Compound.name == 'ethane', Compound.mr != None, GcRun.date > datetime(2019, 1, 1)]

# VERIFIED: Results have been matched with existing records
for r in get_query(params, filters):
    print(r)
# from reporting import get_df_with_filters, write_df_to_excel
# write_df_to_excel(get_df_with_filters(use_mrs=True, filters=filters, compounds=['ethane']))

