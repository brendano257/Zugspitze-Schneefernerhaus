import json
from datetime import datetime, timezone, timedelta

from settings import CORE_DIR

from IO.db import DBConnection, Compound, Integration, GcRun
from IO import scan_and_create_dir_tree, get_standard_quants, final_data_first_sample_only_filter

__all__ = ['create_current_json']


def create_current_semifinal_json(filtered=True, additional_filters=final_data_first_sample_only_filter):
    create_current_json(filtered=filtered, additional_filters=additional_filters, type_='final')


def create_current_json(filtered=True, additional_filters=None, type_=None):
    """
    Auto-save json files of the (optionally filtered) data for the entire record.

    :param bool filtered: True, if data in files should be filtered, False if all data should be included.
    :return:
    """

    # always use a given type name, and default to filtered or raw otherwise
    filt_type = type_ if type_ else 'filtered' if filtered else 'raw'
    file_suffix = filt_type if filt_type is not 'final' else 'filtered'

    with DBConnection() as session:
        quantified_compounds = get_standard_quants('quantlist', string=True,session=session, set_=False)

        save_dir = CORE_DIR / f'data/generation/json/auto_by_date/{filt_type}/{datetime.now().strftime("%Y_%m_%d")}'
        if not save_dir.exists():
            scan_and_create_dir_tree(save_dir, file=False)

        for compound in quantified_compounds:
            results = (session.query(Compound.mr, GcRun.date, Integration.filename)
                       .join(Integration, Integration.id == Compound.integration_id)
                       .join(GcRun, GcRun.id == Integration.run_id)
                       .filter(GcRun.type == 5)
                       .filter(Compound.name == compound))

            if filtered:
                results = results.filter(Compound.filtered == False)

            if additional_filters:
                for f in additional_filters:
                    results = results.filter(f)

            results = results.order_by(Integration.date).all()

            data_for_json = []

            for r in results:
                if r.mr is not None:
                    date = r.date.replace(tzinfo=timezone(timedelta(hours=1))).timestamp()
                    compound_obj = {'date': date, 'value': r.mr, 'file': r.filename}  # report time as epoch UTC
                    data_for_json.append(compound_obj)

            # print(r.date, datetime.fromtimestamp(date, tz=timezone(timedelta(hours=1))))  # shows conversion works

            file = save_dir / f'{compound}_{file_suffix}.json'

            with file.open('w') as f:
                f.write(json.dumps(data_for_json))
