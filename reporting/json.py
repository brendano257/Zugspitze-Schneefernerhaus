import json
from datetime import datetime, timezone, timedelta

from settings import CORE_DIR

from IO.db import DBConnection, Compound, Integration, GcRun
from IO import scan_and_create_dir_tree, get_standard_quants


def create_current_filtered_json():
    with DBConnection() as session:
        quantified_compounds = get_standard_quants('quantlist', session=session, set_=False)

        save_dir = CORE_DIR / f'data/generation/json/auto_by_date/{datetime.now().strftime("%Y_%m_%d")}'
        if not save_dir.exists():
            scan_and_create_dir_tree(save_dir, file=False)

        for compound in quantified_compounds:
            results = (session.query(Compound.mr, GcRun.date, Integration.filename)
                       .join(Integration, Integration.id == Compound.integration_id)
                       .join(GcRun, GcRun.id == Integration.run_id)
                       .filter(GcRun.type == 5)
                       .filter(Compound.name == compound)
                       .filter(Compound.filtered == False)
                       .order_by(Integration.date)
                       .all())

            data_for_json = []

            for r in results:
                if r.mr is not None:
                    date = r.date.replace(tzinfo=timezone(timedelta(hours=1))).timestamp()
                    compound_obj = {'date': date, 'value': r.mr, 'file': r.filename}  # report time as epoch UTC
                    data_for_json.append(compound_obj)

            # print(r.date, datetime.fromtimestamp(date, tz=timezone(timedelta(hours=1))))  # shows conversion works

            file = save_dir / f'{compound}_filtered.json'

            with file.open('w') as f:
                f.write(json.dumps(data_for_json))
