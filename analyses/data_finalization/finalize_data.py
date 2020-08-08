"""

Finalized data needs corrections from JFJ data and averaging where there's two daily samples.

Those will be handled separately and run from here.

datetime(2018, 12, 20)
datetime(2020, 1, 1))

"""
import json

from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict

import pandas as pd

from settings import JSON_PUBLIC_DIR
from analyses.data_finalization.daily_averaging import get_average_two_sample_data
from IO.db import DBConnection, GcRun, Compound, OldData
from IO import get_standard_quants, ambient_filters
from reporting import abstract_query
from processing.constants import DETECTION_LIMITS
from plotting import MixingRatioPlot


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


def join_and_filter_data():
    compounds_to_output = get_standard_quants('quantlist', string=True, set_=False)

    # with open(JSON_PUBLIC_DIR / 'zug_plot_info.json', 'r') as file:
    #     compound_limits = json.loads(file.read())

    single_sample_data = get_final_single_sample_data(compounds_to_output)
    two_sample_data, ratios = get_average_two_sample_data(datetime(2018, 12, 20),
                                                          datetime(2020, 1, 1),
                                                          compounds_to_output)

    # print_stats_on_ratios_by_compound(ratios)

    final_data = {}

    for compound in compounds_to_output:
        single_samples = single_sample_data.get(compound)
        two_samples = two_sample_data.get(compound)

        final_data[compound] = (single_samples[0] + two_samples[0], single_samples[1] + two_samples[1])
        # final data is now a dict of compound: (dates, mrs) for every compound

        # iterate explicitly over indices instead of the list! Python Rule #1: Don't iterate over and modify
        for index in range(len(final_data[compound][1])):
            # if the mr is below the detection limit, set to half the limit
            if (final_data[compound][1][index] is not None
                    and final_data[compound][1][index] < DETECTION_LIMITS.get(compound, 0)):
                final_data[compound][1][index] = DETECTION_LIMITS.get(compound, 0) / 2

                # if something has no DL, but is set to 0, mark as None/Null
                if final_data[compound][1][index] == 0:
                    final_data[compound][1][index] = None

        MixingRatioPlot(
            {compound: final_data[compound]},
            show=False,
            save=True,
            filepath=f'plots/{compound}_final.png'
        ).plot()


    filter_data = defaultdict(list)

    for filter_file in Path('manual_filtering').iterdir():
        if filter_file.suffix == '.json':
            filters = json.loads(filter_file.read_text())

            for date, compounds in filters.items():
                filter_data[datetime.strptime(date, '%Y-%m-%d %H:%M')].extend(compounds)

    for date, compounds in filter_data.items():
        for compound in compounds:
            final_data[compound][1][final_data[compound][0].index(date)] = None

    with DBConnection() as session:
        # connect to db and grab old data from previous project
        for compound in final_data:
            old_results = (session.query(OldData.date, OldData.mr)
                          .filter(OldData.name == compound)
                          .order_by(OldData.date)
                          .all())

            dates = [o.date for o in old_results]
            mrs = [o.mr for o in old_results]

            # prepend older dates and mrs
            final_data[compound] = dates + final_data[compound][0], mrs + final_data[compound][1]

    jsonify_data(final_data, '/home/brendan/PycharmProjects/Zugspitze/DataSelectors/FinalDataSelector/data')

    return final_data


def final_data_to_df(data):
    """
    Takes in data and returns a Pandas DataFrame.
    :param dict data: comes in as 'compound_name': [dates, mrs] where dates and mrs are iterables of equal length
    :return:
    """
    return pd.DataFrame().join([pd.DataFrame({'date': dates, compound: mrs}).set_index('date', drop=True)
                                for compound, (dates, mrs) in data.items()], how='outer')


def main():
    final_data = join_and_filter_data()
    df = final_data_to_df(final_data)
    df.to_csv(f'final_data_{datetime.now().strftime("%Y_%m_%d")}.csv', float_format='%.3f')


if __name__ == '__main__':
    main()
