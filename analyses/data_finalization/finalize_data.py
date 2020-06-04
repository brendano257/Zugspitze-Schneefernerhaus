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

from analyses.data_finalization.daily_averaging import get_average_two_sample_data
from IO.db import DBConnection, GcRun, Compound
from IO import get_standard_quants, ambient_filters
from reporting import abstract_query


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

        final_single_sample_data[compound] = ([r.date for r in results], [r.mr for r in results])

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
                compound_obj = {'date': date, 'value': mr}  # report time as epoch UTC
                data_for_json.append(compound_obj)

        # print(r.date, datetime.fromtimestamp(date, tz=timezone(timedelta(hours=1))))  # shows conversion works

        file = Path(rel_dir) / f'{compound}_filtered.json'

        with file.open('w') as f:
            f.write(json.dumps(data_for_json))


def main():
    compounds_to_output = get_standard_quants('quantlist', string=True, set_=False)

    single_sample_data = get_final_single_sample_data(compounds_to_output)
    two_sample_data = get_average_two_sample_data(datetime(2018, 12, 20), datetime(2020, 1, 1), compounds_to_output)

    final_data = {}

    for compound in compounds_to_output:
        single_samples = single_sample_data.get(compound)
        two_samples = two_sample_data.get(compound)

        final_data[compound] = (single_samples[0] + two_samples[0], single_samples[1] + two_samples[1])

    filter_data = defaultdict(list)

    for filter_file in Path('manual_filtering').iterdir():
        if filter_file.suffix == '.json':
            filters = json.loads(filter_file.read_text())

            for date, compounds in filters.items():
                filter_data[datetime.strptime(date, '%Y-%m-%d %H:%M')].extend(compounds)

    # TODO: finish applying filter data

    print(filter_data)

    jsonify_data(final_data, 'semifinal_json')




if __name__ == '__main__':
    main()
