"""
An experiment with generating custom queries with only a list of parameters and filters, letting the function handle
any joins that are necessary.
"""

from settings import CORE_DIR, DB_NAME
from IO.db import GcRun, Integration, Compound, connect_to_db

import inspect

d = dict(m for m in inspect.getmembers(Integration.id))

# the parent class of an attribute can be used to *attempt* to track down relationships.

print(Integration.id.parent.class_)
print(Integration)


def get_query(params, filters):
    engine, session = connect_to_db(DB_NAME, CORE_DIR)

    q = session.query(*params)

    for f in filters:
        q = q.filter(f)

    return q.all()[:10]


print(get_query([Compound.name, Compound.mr], [Compound.name == 'ethane']))

