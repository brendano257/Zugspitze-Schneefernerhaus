__all__ = ['split_into_sets_of_n', 'gen_isempty', 'search_for_attr_value', 'find_closest_date']


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
