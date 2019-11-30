"""
An experiment with generating custom queries with only a list of parameters and filters, letting the function handle
any joins that are necessary.
"""
from collections import namedtuple, defaultdict

from sqlalchemy.inspection import inspect

from settings import CORE_DIR, DB_NAME
from IO.db import GcRun, Integration, Compound, LogFile, connect_to_db

# the parent class of an attribute can be used to *attempt* to track down relationships.
# print(Integration.id.parent.class_)
# print(Integration)

# class to simplify relationships...
Relation = namedtuple('Relation', 'fkey key')

# get_query works with a fixed project structure like below...
project_structure = {
    'Compound': {'GcRun': Relation(Compound.run_id, GcRun.id)},
    'GcRun': {}  # not sure how to reference many to one...? At all...?
}

# TODO: generating the project structure should be kicked to the end of IO.db.models.data
#   the below shows exactly how to get names needed; next get the related fields...

relations = defaultdict(dict)

for c in (GcRun, LogFile, Integration, Compound):
    # print(c)
    related_classes = inspect(c).relationships
    #
    # for r in related_classes:
    #     print(r.local_remote_pairs[0])
    #
    # print(' ')


    directions = [r.direction.name for r in related_classes]
    remote_classes = [r.entity.class_ for r in related_classes]
    key_pairs = [r.local_remote_pairs[0] for r in related_classes]
    # remote_columns = [c.remote_side for c in related_classes]

    for rclass, key_pair, direction in zip(remote_classes, key_pairs, directions):
        if direction == 'ONETOMANY':
            key = key_pair[0]
            fkey = key_pair[1]
            # print(f'{c.__name__} is related {direction} to {rclass.__name__}')
            # print(f'\tThe relationship is {key}:{fkey}')
            # print(f'\tAttrs are {getattr(c, key.name)}:{getattr(rclass, fkey.name)}')

            relations[c.__name__][rclass.__name__] = Relation(key, fkey)
            relations[rclass.__name__][c.__name__] = Relation(fkey, key)

    # print(' ')

for x in relations.items():
    print(x[0])
    for y in x[1].items():
        print(f'\t{y}')


# related_classes = inspect(Integration).relationships
# print([c.entity.class_ for c in related_classes])
# remote_columns = [c.remote_side for c in related_classes]
# directions = [c.direction.name for c in related_classes]
#
# reverse_relations = [c._reverse_property for c in related_classes]
#
# for r, d in zip(remote_columns, directions):
#     print(r)
#     print(d)
#     for part in r:
#         print(part.name)
#         print(part.table)

# print('\n')
#
# for r in reverse_relations:
#     print(r)
#     for x in r:
#         print(x.entity)
    # print(r.entity)
    # for part in r:
    #     print(part.name)
    #     print(part.table)


# look into RelationshipProperty.class_attribute


# def get_query(params, filters):
#     """
#     Create a query with only a list of parameters to grab, and filters to apply after
#
#     Use SQLalchemy internals to poke around and get classes, etc
#     """
#     engine, session = connect_to_db(DB_NAME, CORE_DIR)
#
#     q = session.query(*params)  # kick off the query
#
#     classes = []
#     for p in params:
#         parent_class = p.parent.class_
#         classes.append(parent_class) if parent_class not in classes else None # need order, so hack around a set...
#
#
#     base = classes.pop(0)  # grab first class from list
#     linked = [base]  # the first class is inherently already in the join-chain
#
#     if classes:  # any more classes?
#         for c in classes:
#             relations_for_c = project_structure.get(c.__name__)
#
#             if not relations_for_c:
#                 msg = f'{c.__name__} does not have any defined relationships.'
#                 raise NotImplementedError(msg)
#
#             relation = relations_for_c.get(base.__name__)
#
#             if relation:
#                 q = q.join(c, relation.key == relation.fkey)
#             else:
#                 msg = f'{c.__name__} is not directly related to {base} in the schema.'
#                 raise NotImplementedError(msg)
#
#     for f in filters:
#         q = q.filter(f)
#
#     return q.all()[:10]
#
#
# # print(get_query([Compound.name, Compound.mr], [Compound.name == 'ethane']))  # working w/ one class
#
# params = [GcRun.id, GcRun.date, Compound.id, Compound.name, Compound.mr]
# filters = [Compound.name == 'ethane', Compound.mr != None]
#
# for r in get_query(params, filters):
#     print(r)
#
# # TODO: Verify results w/ other table/methods
