
import json
import statistics as s

from pathlib import Path
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from collections import defaultdict

import pandas as pd

from settings import JSON_PRIVATE_DIR
from finalization.averaging import get_final_average_two_sample_data, get_final_single_sample_data
from IO.db import DBConnection, OldData
from processing.constants import DETECTION_LIMITS, EBAS_REPORTING_COMPOUNDS

FINAL_FILTERS_DIR = JSON_PRIVATE_DIR / 'filters/final_manual_filtering'


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
                           .order_by(OldData.date)
                           .all())

            dates = [o.date for o in old_results]
            mrs = [o.mr for o in old_results]

            # prepend older dates and mrs
            all_final_data[compound] = dates + new_final_data[compound][0], mrs + new_final_data[compound][1]

    return all_final_data


def fork_and_filter_moving_median(final_data, pct=10):
    """
    Accepts near-final data, and filters based on a moving median and excludes values according to their deviation from
    the moving median by some fixed or supplied percentage.
    :param final_data:
    :param pct: whole percentage, eg the default of 10 means 10%
    :return:
    """

    final_flagged_data = deepcopy(final_data)  # create an entirely separate copy

    # TODO: build medians and then filter both copies, keeping in one, removing from the other

    return final_data, final_flagged_data


def filter_all_final_data(final_data):

    filter_data = defaultdict(list)

    for filter_file in FINAL_FILTERS_DIR.iterdir():
        if filter_file.suffix == '.json':
            filters = json.loads(filter_file.read_text())

            for date, compounds in filters.items():
                filter_data[datetime.strptime(date, '%Y-%m-%d %H:%M')].extend(compounds)

    for date, compounds in filter_data.items():
        for compound in compounds:
            if __name__ == '__main__':  # only write the filter output if run directly in module
                print(
                    f'Filtering {compound} for {date}, which was '
                    + f'{final_data[compound][1][final_data[compound][0].index(date)]}'
                )

            final_data[compound][1][final_data[compound][0].index(date)] = None

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

    final_data, final_flagged_data = fork_and_filter_moving_median(final_data)

    return final_data, final_flagged_data  # TODO: address all prior use cases


def get_all_final_data_as_dict():
    """
    Sequentially build the final data by joining the single sample data to averaged two sample data, adding in the old,
    historic data, then applying all manual filter files and applying detection limits after.
    :return:
    """
    final_data_dict, _ = filter_all_final_data(prepend_historic_data(join_new_data()))
    return final_data_dict


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
