import logging
from pathlib import Path

from sqlalchemy import event

__all__ = ['configure_logger', 'split_into_sets_of_n', 'gen_isempty', 'search_for_attr_value', 'find_closest_date',
           'make_class_iterable_on_attr']


def configure_logger(rundir, name):
    """
    Create the project-specific logger. DEBUG and up is saved to the log, INFO and up appears in the console.

    :param Path rundir: Path to create log sub-path in
    :param str name: name for logfile
    :return Logger: logger object
    """
    logfile = Path(rundir) / f'{name}.log'
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(logfile)
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s -%(levelname)s- %(message)s')

    [H.setFormatter(formatter) for H in [ch, fh]]
    if not len(logger.handlers):
        _ = [logger.addHandler(H) for H in [ch, fh]]

    return logger


def split_into_sets_of_n(lst, n):
    """
    Split a list into lists of length n

    :param list lst: a list of values to be split
    :param int n: number of items per set after split
    :return generator: returns lists of length n until empty
    """
    for i in range(0, len(lst), n):
        yield (lst[i:i + n])


def gen_isempty(gen):
    """
    Checks to see if a generator is empty, returning a copy of the original

    Returns a tuple of the original generator and False if it has at least one value, True if it's empty

    :param generator gen: any generator
    :return tuple: (generator, bool), returns the same generator, and True if empty, False if not
    """
    try:
        item = next(gen)

        def my_generator():
            yield item
            yield from gen

        return my_generator(), False
    except StopIteration:
        return (_ for _ in []), True


def search_for_attr_value(obj_list, attr, value):
    """
    Finds the first object in a list where it's attribute attr is equal to value.

    Finds the first (not necesarilly the only) object in a list, where its attribute 'attr' is equal to 'value'.
    Returns None if none is found.

    :param list obj_list: list of objects to search
    :param str attr: attribute to search for
    :param value: value that should be searched for
    :return: obj, from obj_list, where attribute attr matches value
        **returns the *first* obj, not necessarily the only
    """
    return next((obj for obj in obj_list if getattr(obj, attr, None) == value), None)


def find_closest_date(date, list_of_dates, how='abs'):
    """
    Finds the closest date in a provided list.

    Returns the closest date value, either absolutely, or closest without being above/below, and the timedelta from the
    provided date.

    :param datetime date: date from which to find closest match in list
    :param list list_of_dates: list of datetimes
    :param str how: ['abs', 'pos','neg']
            'abs': Absolute closest datetime, either above or below the given date
            'pos': Matched datetime must be greater than given date
            'neg': Matched datetime must be less than given date
    :return tuple: match, delta; the matching date from the list, and it's difference to the original as a timedelta
    """

    list_of_dates[:] = [l for l in list_of_dates if l]  # remove any Nones

    if how == 'abs':
        try:
            match = min(list_of_dates, key=lambda x: abs(x - date))
        except ValueError:
            return None, None
    elif how == 'pos':
        try:
            new_list = [d for d in list_of_dates if d > date]  # filter for only positives first
            match = min(new_list, key=lambda x: (x - date))
        except ValueError:
            return None, None
    elif how == 'neg':
        try:
            new_list = [d for d in list_of_dates if d <= date]  # filter for only negatives first
            match = max(new_list, key=lambda x: x - date)
        except ValueError:
            return None, None
    else:
        assert False, "Supplied 'how' not in ['abs', 'pos', 'neg']"

    delta = match - date

    return match, delta


def make_class_iterable_on_attr(attr):
    """
    Class decorator for making a class iterable by deligating iteration to it's attribute 'attr'.

    :param str attr: attribute to deligate iteration of the class to
    :return: the wrapped class, with added __iter__ method
    """
    def class_wrap(cls):
        def deligated_iter(self):
            return iter(getattr(self, attr))

        cls.__iter__ = deligated_iter
        return cls

    return class_wrap


def give_class_lookup_on_attr(attr_to_lookup, lookup_key_attr, lookup_value_attr, lookup_name):
    """
    Decorate a class with dictionary lookup on some sequential attribute of the class; often a relationship.

    For a class, MappedClass, create a lookup table of attr_to_lookup, such that it's:
        MappedClass.lookup_name = {obj.lookup_key_attr: getattr(obj, lookup_value_attr, obj) for obj in attr_to_lookup}

    Uses sqlalchemy 'load' event to automatically create lookup whenever re-instantiated from the database; otherwise
    the lookup is only created if the property (self.lookup_name['thing']) is called and would return a falsy value.

    :param str attr_to_lookup: attribute on the class to create a lookup table of
    :param str lookup_key_attr: attribute of attr_to_lookup instances to use as the key
    :param str | None lookup_value_attr: attribute of attr_to_lookup instances to use at the value.
        ** Passing None as the lookup_value_attr will make the value the object itself
    :param str lookup_name: name of the class property to access the lookup table by
    :return:
    """
    # None is a key for the lookup_value_attr to return the object itself (set in the default)
    if lookup_value_attr is None:
        lookup_value_attr = ''
        # passing an empty string will never find an attribute, which makes it the key for returning the default

    def class_wrap(cls):

        def func(self):
            attr = getattr(self, attr_to_lookup)

            lookup = dict(zip(
                [getattr(c, lookup_key_attr) for c in attr],
                [getattr(c, lookup_value_attr, c) for c in attr]
            ))

            # set a private attr as "self._<lookup_name>"
            setattr(self, '_' + lookup_name, lookup)

        cls._create_lookup = func

        def prop_getter(self, name=lookup_name):
            attr = getattr(self, '_' + name, None)

            if not attr:
                print('Lookup was not found. Created and returned.')
                self._create_lookup()
                attr = getattr(self, '_' + name)

            return attr

        setattr(cls, lookup_name, property(prop_getter))

        @event.listens_for(cls, 'load')
        def recieve_load(target, context):
            target._create_lookup()

        return cls

    return class_wrap
