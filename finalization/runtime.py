"""
TODO:
    1) Move final data to a real object; needs better and named structure
    2) Give all data on return; fix connections across project
    3) Move plotting to a separate optional place
"""

import json
import statistics as s

from pathlib import Path
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from collections import defaultdict

import pandas as pd

from settings import JSON_PRIVATE_DIR, CORE_DIR
from finalization.averaging import get_final_average_two_sample_data, get_final_single_sample_data
from IO.db import DBConnection, OldData
from processing.constants import DETECTION_LIMITS, EBAS_REPORTING_COMPOUNDS
from finalization.constants import (MEDIAN_10_COMPOUNDS, MEDIAN_25_COMPOUNDS, SEASONAL_CYCLE_COMPOUNDS, NONE,
                                    TWENTY_ONE_DAY)
from plotting import MixingRatioPlot

FINAL_FILTERS_DIR = JSON_PRIVATE_DIR / 'filters/final_manual_filtering'

EBAS_REPORTING_COMPOUNDS_SET = frozenset(EBAS_REPORTING_COMPOUNDS)


def jsonify_data(data, rel_dir):
    """
    Create json files that can be used with DataSelector to filter any bad averages, etc.

    :param dict data: data to be jsonified, formatted: {compound: [dates, mrs], ...}
    :return:
    """

    for compound in data.keys():
        data_for_json = []
        for date, mr in zip(*data[compound]):
            if mr is not None:
                date = date.replace(tzinfo=timezone(timedelta(hours=1))).timestamp()
                compound_obj = {'date': date, 'mr': mr}  # report time as epoch UTC
                data_for_json.append(compound_obj)

        # print(r.date, datetime.fromtimestamp(date, tz=timezone(timedelta(hours=1))))  # shows conversion works

        file = Path(rel_dir) / f'{compound}_filtered.json'

        with file.open('w') as f:
            f.write(json.dumps(data_for_json))


def print_stats_on_ratios_by_compound(ratios):
    """
    Print statistics on ratios between two-sample data so they can be used in reporting the data.
    :param ratios:
    :return:
    """
    for name, data in ratios.items():
        print(f'{name}: {data}')


def join_new_data():
    single_sample_data = get_final_single_sample_data(EBAS_REPORTING_COMPOUNDS)
    two_sample_data = get_final_average_two_sample_data(datetime(2018, 12, 20),
                                                        datetime(2021, 1, 1),
                                                        EBAS_REPORTING_COMPOUNDS)
    joined_new_data = {}

    for compound in EBAS_REPORTING_COMPOUNDS:
        single_samples = single_sample_data.get(compound)
        two_samples = two_sample_data.get(compound)

        joined_new_data[compound] = (single_samples[0] + two_samples[0], single_samples[1] + two_samples[1])
        # final data is now a dict of compound: (dates, mrs) for every compound

    return joined_new_data


def prepend_historic_data(new_final_data):

    all_final_data = {}

    with DBConnection() as session:
        # connect to db and grab old data from previous project
        for compound in EBAS_REPORTING_COMPOUNDS:
            old_results = (session.query(OldData.date, OldData.mr)
                           .filter(OldData.name == compound)
                           .filter(OldData.filtered == False)
                           .order_by(OldData.date)
                           .all())

            dates = [o.date for o in old_results]
            mrs = [o.mr for o in old_results]

            # prepend older dates and mrs
            all_final_data[compound] = [dates + new_final_data[compound][0], mrs + new_final_data[compound][1]]

    return all_final_data


def fork_and_filter_with_moving_median(final_data, plot=False):
    """
    Accepts near-final data, and filters based on a moving median and excludes values according to their deviation from
    the moving median by some fixed or supplied percentage.

    :param final_data:
    :param int | float pct: whole percentage, eg the default of 10 means 10%
    :return:
    """


    final_flagged_data = deepcopy(final_data)  # create an entirely separate copy to hold flagged-only data
    final_clean_data = deepcopy(final_data)  # create an entirely separate copy for clean data only

    for compound in EBAS_REPORTING_COMPOUNDS:
        final_data[compound].append([None] * len(final_data[compound][0]))  # add a new list which will hold the median values

        stdev_all = s.stdev([d for d in final_data[compound][1] if d is not None])

        for index, (date, mr) in enumerate(zip(final_data[compound][0], final_data[compound][1])):
            if date is None:
                continue

            if compound in SEASONAL_CYCLE_COMPOUNDS:
                days = 14
            else:
                days = 28

            date_start = date - timedelta(days=days)
            date_end = date + timedelta(days=days)

            # this will be slow! It's a linear all-points check every time, but guarantees we get it right
            # some iterator magic would be faster but riskier without substantial testing
            cleaned_points = [
                point for date, point in zip(final_data[compound][0], final_data[compound][1])
                if date_start <= date < date_end and point is not None
            ]

            median = None if not cleaned_points else s.median(cleaned_points)
            stdev_moving = None if len(cleaned_points) < 2 else s.stdev(cleaned_points)

            if mr is not None:
                if compound in SEASONAL_CYCLE_COMPOUNDS and stdev_all is not None:
                    if median - (stdev_all * 2) <= mr < median + (stdev_all * 2):
                        # data is consistent with median; remove it from the flagged data
                        final_flagged_data[compound][1][index] = None
                    else:
                        # data is outside the bounds; remove from clean data
                        final_clean_data[compound][1][index] = None

                elif compound in MEDIAN_10_COMPOUNDS and median is not None:
                    if median * .9 <= mr < median * 1.1:
                        # data is consistent with median; remove it from the flagged data
                        final_flagged_data[compound][1][index] = None
                    else:
                        # data is outside the bounds; remove from clean data
                        final_clean_data[compound][1][index] = None

                elif compound in MEDIAN_25_COMPOUNDS and median is not None:
                    if median * .75 <= mr < median * 1.25:
                        # data is consistent with median; remove it from the flagged data
                        final_flagged_data[compound][1][index] = None
                    else:
                        # data is outside the bounds; remove from clean data
                        final_clean_data[compound][1][index] = None
                else:  # is in group NONE or some other non-filtered list
                    final_flagged_data[compound][1][index] = None

        if plot:

            if compound in SEASONAL_CYCLE_COMPOUNDS:
                flag_policy = 'stdev'
            elif compound in MEDIAN_10_COMPOUNDS:
                flag_policy = 'median 10%'
            elif compound in MEDIAN_25_COMPOUNDS:
                flag_policy = 'median 25%'
            elif compound in NONE:
                flag_policy = 'no flag'
            else:
                flag_policy = 'none given'

            MixingRatioPlot(
                {
                    f'{compound} (clean)': (final_clean_data[compound][0], final_clean_data[compound][1]),
                    f'{compound} ({flag_policy})': (final_flagged_data[compound][0], final_flagged_data[compound][1])
                },
                title=f'{compound} Mixing Ratios',
                limits={'left': datetime(2013, 1, 1), 'right': datetime(2021, 1, 1)},
                show=False,
                save=True,
                filepath=Path(CORE_DIR / f'finalization/scratch_plots/flagged_data_comparisons/{compound}_flagged_mrs.png')
            ).plot()

    return final_clean_data, final_flagged_data


def filter_all_final_data(final_data):

    filter_data = defaultdict(list)

    for filter_file in FINAL_FILTERS_DIR.iterdir():
        if filter_file.suffix == '.json':
            filters = json.loads(filter_file.read_text())

            for date, compounds in filters.items():
                filter_data[datetime.strptime(date, '%Y-%m-%d %H:%M')].extend(compounds)

    for date, compounds in filter_data.items():
        for compound in compounds:
            if compound not in EBAS_REPORTING_COMPOUNDS:
                continue  # ignore any filters that don't apply to final data (eg SF6)
            try:
                if __name__ == '__main__':  # only write the filter output if run directly in module
                    print(
                        f'Filtering {compound} for {date}, which was '
                        + f'{final_data[compound][1][final_data[compound][0].index(date)]}'
                    )

                final_data[compound][1][final_data[compound][0].index(date)] = None
            except ValueError:
                # if compound isn't found in the list, we can't/won't bother to filter it
                # this can happen is something was wholesale-filtered beforehand, and no longer appears in some
                # manual filter that was created specifically while finalizing data; it's perfectly okay
                continue

    for compound in EBAS_REPORTING_COMPOUNDS:
        # iterate explicitly over indices instead of the list! Python Rule #1: Don't iterate over and modify
        for index in range(len(final_data[compound][1])):
            # if the mr is below the detection limit, set to half the limit
            if (final_data[compound][1][index] is not None
                    and final_data[compound][1][index] < DETECTION_LIMITS.get(compound, 0)):
                final_data[compound][1][index] = DETECTION_LIMITS.get(compound, 0) / 2

                # if something has no DL, but is set to 0, mark as None/Null
                if final_data[compound][1][index] == 0:
                    final_data[compound][1][index] = None

    final_clean_data, final_flagged_data = fork_and_filter_with_moving_median(final_data, plot=__name__ == '__main__')

    return final_clean_data, final_flagged_data


def get_all_final_data_as_dict():
    """
    Sequentially build the final data by joining the single sample data to averaged two sample data, adding in the old,
    historic data, then applying all manual filter files and applying detection limits after.
    :return:
    """
    final_data_dict, _ = filter_all_final_data(prepend_historic_data(join_new_data()))
    return final_data_dict, _


def final_data_to_df(data):
    """
    Takes in data and returns a Pandas DataFrame.
    :param dict data: comes in as {'compound_name': [dates, mrs], ...} where dates and mrs are iterables of equal length
    :return:
    """
    return pd.DataFrame().join([pd.DataFrame({'date': dates, compound: mrs}).set_index('date', drop=True)
                                for compound, (dates, mrs) in data.items()], how='outer')


def main():
    final_data, _ = get_all_final_data_as_dict()
    df = final_data_to_df(final_data)
    df.to_csv(f'final_data_{datetime.now().strftime("%Y_%m_%d")}.csv', float_format='%.3f')


if __name__ == '__main__':
    main()
