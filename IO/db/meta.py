"""
Meta contains

"""
from collections import namedtuple, defaultdict

from sqlalchemy.inspection import inspect

from IO.db.models import GcRun, LogFile, Integration, Compound

__all__ = ['relations', 'print_database_meta']

Relation = namedtuple('Relation', 'fkey key')
relations = defaultdict(dict)

for class_ in (GcRun, LogFile, Integration, Compound):
    related_classes = inspect(class_).relationships

    remote_classes = [r.entity.class_ for r in related_classes]  # get class of remote entity in relationship
    directions = [r.direction.name for r in related_classes]  # get direction of relationship relative to class_
    key_pairs = [r.local_remote_pairs[0] for r in related_classes]  # get (local, remote) information

    for rclass, direction, key_pair in zip(remote_classes, directions, key_pairs):
        if direction == 'ONETOMANY':  # only address one-to-many, as they can be flipped to address many-to-one
            key = key_pair[0]  # column in rclass that's used as a key
            fkey = key_pair[1]  # column in class_ that's used as a key

            relations[class_.__name__][rclass.__name__] = Relation(fkey, key)  # add relationship and it's reverse
            relations[rclass.__name__][class_.__name__] = Relation(key, fkey)


def print_database_meta():
    """
    Closure that prints relationship metadata generated at runtime.

    Prints:\n
    <class name>
        <column of class's key to related class>:<column of foreign key in related class>
        <...>
    <class2 name>
        <...>

    :return:
    """
    for class_ in relations.items():
        print(class_[0])  # print class name
        for y in class_[1].items():
            print(f'\t{y}')
