"""
NOTE: All filters MAY NOT BE IN EFFECT if the main script, zugspitze_runtime.py has not been run after adding more
filter JSON files.
"""
__package__ = 'Z'

import json
from datetime import timezone, timedelta

from settings import CORE_DIR, DB_NAME

from IO.db import connect_to_db, Standard, Compound, Integration, Quantification, GcRun
from IO import scan_and_create_dir_tree

engine, session = connect_to_db(DB_NAME, CORE_DIR)

quantified_compounds = (session.query(Quantification)
                        .join(Standard, Standard.id == Quantification.standard_id)
                        .filter(Standard.name == 'quantlist').all())

if quantified_compounds is None:
    raise ValueError('Quantified compounds cannot be None; check that database is available')

quantified_compounds = [q.name for q in quantified_compounds]

for type_ in ("filtered", "raw"):

    save_dir = CORE_DIR / f'data/generation/json/{type_}'
    if not save_dir.exists():
        scan_and_create_dir_tree(save_dir, file=False)

    for compound in quantified_compounds:

        #  if raw, get filtered == False AND filtered == True, else get where filtered == False or filtered == False
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
                # print(r.date, datetime.fromtimestamp(date, tz=timezone(timedelta(hours=1))))  # shows conversion works
                compound_obj = {'date': date, 'value': r.mr, 'file': r.filename}  # report time as epoch UTC
                data_for_json.append(compound_obj)

        file = save_dir / f'{compound}_{type_}.json'

        with file.open('w') as f:
            f.write(json.dumps(data_for_json))
