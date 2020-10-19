"""
For CFCs -11, -12, and -113, we have JFJ data to correct by for the period we have only one skewed sample per day.
That is addressed here.
"""
raise DeprecationWarning("Most of this functionality has been moved to reporting.finalization.<...>.")

import statistics as stats
from collections import namedtuple, defaultdict
from datetime import datetime, timedelta
from bisect import bisect_right
from math import isnan

from sqlalchemy.sql.expression import not_

from IO.db import DBConnection
from IO.db.models import GcRun, Integration


def read_jfj_file(filepath, sort=True):
    converters = [lambda x, f=func: f(x) for func in
                  (int, int, int, int, int, float, float, float, float, float, float)]

    with open(filepath, 'r') as file:
        for i in range(7):
            next(file)  # dispose of header

        t = namedtuple('data', [fieldname.strip().replace('-', '_') for fieldname in next(file).split(',')])

        data = [t(*[conv(field.strip()) for field, conv in zip(line.split(','), converters)]) for line in file]

    jfj_dates = []
    jfj_cfc_11 = []
    jfj_cfc_12 = []
    jfj_cfc_113 = []

    for d in data:
        jfj_dates.append(datetime(d.year, d.month, d.day, d.hour, d.min, 0))
        jfj_cfc_11.append(d.CFC_11)
        jfj_cfc_12.append(d.CFC_12)
        jfj_cfc_113.append(d.CFC_113)

    if sort:
        # pack up, sort, then unpack data to sort it all together
        jfj_dates, jfj_cfc_11, jfj_cfc_12, jfj_cfc_113 = (
            zip(*sorted(zip(jfj_dates, jfj_cfc_11, jfj_cfc_12, jfj_cfc_113)))
        )

    return {'date': jfj_dates, 'CFC-11': jfj_cfc_11, 'CFC-12': jfj_cfc_12, 'CFC-113': jfj_cfc_113}


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


def find_gt(a, x):
    """
    Binary search on sorted data for efficiency.
    Find leftmost value greater than x; from: https://docs.python.org/3.7/library/bisect.html
    :param a:
    :param x:
    :return:
    """
    i = bisect_right(a, x)
    if i != len(a):
        return a[i]
    raise ValueError


def compare_single_samples():
    """

    :return:
    """
    print('Comparing Single Samples')
    # get jfj data sorted by date so it can be binary-searched
    jfj_data = read_jfj_file('JFJ_CFC_Helmig.txt', sort=True)

    with DBConnection() as session:
        zug_single_sample_data = (session.query(GcRun)
                                         .filter(GcRun.type == 5)
                                         .filter(GcRun.date >= datetime(2018, 3, 1))
                                         .filter(GcRun.date < datetime(2018, 12, 20))).all()

    ratios = []
    for compound in ['CFC-11', 'CFC-12', 'CFC-113']:
        for sample in zug_single_sample_data:
            # print(f'GcRun: {sample.date}')
            # print(f'Close samples are: {find_le(jfj_data["date"], sample.date)}'
            #       + f' and {find_gt(jfj_data["date"], sample.date)}')

            # get indexes for +/- 12h from this sample
            first_index = bisect_right(jfj_data['date'], sample.date - timedelta(hours=12))
            second_index = bisect_right(jfj_data['date'], sample.date + timedelta(hours=12)) - 1

            zug_compound = sample.compound.get(compound)

            if zug_compound:
                zug_compound = zug_compound.mr or 0
            else:
                zug_compound = 0

            # print(f"\tZUG Sample: {zug_cfc11}")

            try:
                denom = stats.mean([s for s in jfj_data[compound][first_index:second_index] if not isnan(s)])
            except stats.StatisticsError:
                ratios.append(0)
                continue

            ratios.append(zug_compound / denom)

        # for sample, ratio in zip(zug_single_sample_data, ratios):
        #     print(f'{sample.date}: {ratio}')

        non_zero_ratios = [r for r in ratios if r != 0]
        all_average = stats.mean(non_zero_ratios)
        all_stdev = stats.stdev(non_zero_ratios)

        all_min = min(non_zero_ratios)
        all_max = max(non_zero_ratios)

        print(compound)
        print(f'Min: {all_min}, Max: {all_max}, Mean: {all_average}, StDev: {all_stdev}')
        print(f"2-Sigma: {all_average - 2*all_stdev} : {all_average + 2*all_stdev}")

        from plotting import ResponsePlot

        dates = [sample.date for sample in zug_single_sample_data]
        pairs = [(date, ratio) for date, ratio in zip(dates, ratios) if ratio != 0]

        dates = [p[0] for p in pairs]
        ratios = [p[1] for p in pairs]

        p = ResponsePlot(
            {'Zug:JFJ': (dates, ratios)},
            limits={'top': 1.05, 'bottom': .95},
            y_label_str='Zug/(JFJ Daily Average)',
            title=f'{compound} Ratio',
            save=True,
            show=False,
            filepath=f'{compound}_ratios.png'
        )

        p.plot()


def compare_double_samples():
    """

    :return:
    """
    print('Comparing Double Samples')
    # get jfj data sorted by date so it can be binary-searched
    jfj_data = read_jfj_file('JFJ_CFC_Helmig.txt', sort=True)

    # # filter for ambient data from start of data collection until switch to two samples a day
    # filters = (*ambient_filters, GcRun.date >= datetime(2018, 3, 1), GcRun.date < datetime(2018, 12, 20))
    #
    # zug_single_sample_data = abstract_query((GcRun,), filters, order=GcRun.date)

    with DBConnection() as session:
        # filter for dates where the pattern is NOT _xxa_02.D, but IS _xx_02.D, which is first ambient samples
        zug_first_sample_data = (session.query(GcRun)
                                         .join(Integration, Integration.run_id == GcRun.id)
                                         .filter(GcRun.type == 5)
                                         .filter(not_(Integration.filename.ilike('%/___a/_02.D', escape='/')),)
                                         .filter(Integration.filename.ilike('%/___/_02.D', escape='/'),)
                                         .filter(GcRun.date >= datetime(2018, 12, 20))
                                         .filter(GcRun.date < datetime(2021, 1, 1))).all()

        # filter for dates where the pattern IS _xxa_02.D, which is second ambient samples
        zug_second_sample_data = (session.query(GcRun)
                                 .join(Integration, Integration.run_id == GcRun.id)
                                 .filter(GcRun.type == 5)
                                 .filter(Integration.filename.ilike('%/___a/_02.D', escape='/'))
                                 .filter(GcRun.date >= datetime(2018, 12, 20))
                                 .filter(GcRun.date < datetime(2021, 1, 1))).all()

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

        # for k, v in sample_sets.items():
        #     print(f'{k}: {v}')

        # clean sample_sets to only those with two samples
        sample_sets = {k: v for k, v in sample_sets.items() if len(v) == 2}

    for compound in ('CFC-11', 'CFC-12', 'CFC-113'):
        ratios = {}
        for sample_day, sample_pair in sample_sets.items():
            # print(f'GcRun: {sample_day}')

            averaged_date = sample_pair[0].date + (.5 * (sample_pair[1].date - sample_pair[0].date))

            # print(f'Close samples are: {find_le(jfj_data["date"], averaged_date)}'
            #       + f' and {find_gt(jfj_data["date"], averaged_date)}')

            # get indexes for +/- 12h from this sample
            first_index = bisect_right(jfj_data['date'], averaged_date - timedelta(hours=12))
            second_index = bisect_right(jfj_data['date'], averaged_date + timedelta(hours=12)) - 1

            both_samples = [s.compound.get(compound) for s in sample_pair]
            both_samples = [s.mr for s in both_samples if s]
            both_samples = [s for s in both_samples if s is not None]

            if both_samples:
                compound_mr = stats.mean(both_samples) if len(both_samples) == 2 else both_samples[0]
            else:
                compound_mr = None

            try:
                denom = stats.mean([s for s in jfj_data[compound][first_index:second_index] if not isnan(s)])
            except stats.StatisticsError:
                ratios[sample_day] = 0
                continue

            ratios[sample_day] = compound_mr / denom if compound_mr else 0

        # for sample_date, ratio in ratios.items():
        #     print(f'{sample_date}: {ratio}')

        non_zero_ratios = [r for r in ratios.values() if r != 0]
        all_average = stats.mean(non_zero_ratios)
        all_stdev = stats.stdev(non_zero_ratios)

        all_min = min(non_zero_ratios)
        all_max = max(non_zero_ratios)

        print(compound)
        print(f'Min: {all_min}, Max: {all_max}, Mean: {all_average}, StDev: {all_stdev}, Median: {stats.median(non_zero_ratios)}')
        print(f"2-Sigma: {all_average - 2*all_stdev} : {all_average + 2*all_stdev}")

        from plotting import ResponsePlot

        dates, ratios = list(ratios.keys()), list(ratios.values())

        p = ResponsePlot(
            {'Zug:JFJ': (dates, ratios)},
            limits={'top': 1.05, 'bottom': .95},
            y_label_str='Zug/(JFJ Daily Average)',
            title=f'{compound} Ratio',
            save=True,
            show=False,
            filepath=f'{compound}_ratios.png'
        )

        p.plot()


if __name__ == '__main__':
    read_jfj_file('JFJ.txt', sort=True)
    compare_single_samples()
    print()
    compare_double_samples()