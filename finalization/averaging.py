from datetime import datetime
from bisect import bisect_right
from collections import defaultdict

from sqlalchemy.sql.expression import not_

from IO import ambient_filters
from reporting import abstract_query
from IO.db import DBConnection, GcRun, Integration, Compound


def find_le(a, x):
    """
    Binary search on sorted data for efficiency.
    Find rightmost value less than or equal to x; from: https://docs.python.org/3.7/library/bisect.html
    :param a:
    :param x:
    :return:
    """
    i = bisect_right(a, x)
    if i:
        return a[i-1]
    raise ValueError


def get_final_single_sample_data(compounds):

    final_single_sample_data = {}

    for compound in compounds:
        params = (GcRun.date, Compound.mr)
        filters = (
            Compound.name == compound,
            GcRun.date >= datetime(2018, 3, 1),
            GcRun.date < datetime(2018, 12, 20),
            *ambient_filters  # includes filtering data for filtered = False
        )

        results = abstract_query(params, filters, GcRun.date)

        final_single_sample_data[compound] = ([r.date.replace(second=0) for r in results], [r.mr for r in results])

    return final_single_sample_data


def get_final_average_two_sample_data(start_date, end_date, compounds_to_average):
    with DBConnection() as session:
        # filter for dates where the pattern is NOT _xxa_02.D, but IS _xx_02.D, which is first ambient samples
        zug_first_sample_data = (session.query(GcRun)
                                 .join(Integration, Integration.run_id == GcRun.id)
                                 .filter(GcRun.type == 5)
                                 .filter(not_(Integration.filename.ilike('%/___a/_02.D', escape='/')),)
                                 .filter(Integration.filename.ilike('%/___/_02.D', escape='/'),)
                                 .filter(GcRun.date >= start_date)
                                 .filter(GcRun.date < end_date)
                                 .order_by(GcRun.date).all())

        # filter for dates where the pattern IS _xxa_02.D, which is second ambient samples
        zug_second_sample_data = (session.query(GcRun)
                                  .join(Integration, Integration.run_id == GcRun.id)
                                  .filter(GcRun.type == 5)
                                  .filter(Integration.filename.ilike('%/___a/_02.D', escape='/'))
                                  .filter(GcRun.date >= start_date)
                                  .filter(GcRun.date < end_date)
                                  .order_by(GcRun.date).all())

    first_sample_dates = [run.date for run in zug_first_sample_data]
    second_sample_dates = [run.date for run in zug_second_sample_data]

    # get all dates as unique dates at midnight only
    all_dates = list(frozenset([datetime.combine(d.date(), datetime.min.time()) for d in first_sample_dates]
                               + [datetime.combine(d.date(), datetime.min.time()) for d in second_sample_dates]))
    all_dates.sort()

    sample_sets = defaultdict(list)

    # map all samples to their dates by finding the date that's lte it
    for sample in zug_first_sample_data + zug_second_sample_data:
        sample_sets[find_le(all_dates, sample.date)].append(sample)

    averaged_dates = {}

    for _, sample_pair in sample_sets.items():
        # only proceed if there's two samples
        if len(sample_pair) == 2:
            average_date = (sample_pair[0].date + ((sample_pair[1].date - sample_pair[0].date) / 2))
            averaged_dates[average_date] = sample_pair

    compounds = {}

    # 'round' down to 0 microseconds and seconds for ALL data
    dates = [date.replace(second=0, microsecond=0) for date in averaged_dates.keys()]
    for compound in compounds_to_average:
        compound_mrs = []
        for sample_pair in averaged_dates.values():
            first_compound, second_compound = [s.compound.get(compound) for s in sample_pair]

            if first_compound is None or second_compound is None:
                compound_mrs.append(None)
            else:
                if first_compound.filtered or second_compound.filtered:
                    compound_mrs.append(None)
                else:
                    if first_compound.mr is None or second_compound.mr is None:
                        compound_mrs.append(None)
                    else:
                        compound_mrs.append((first_compound.mr + second_compound.mr) / 2)

        compounds[compound] = (dates, compound_mrs)

    return compounds
