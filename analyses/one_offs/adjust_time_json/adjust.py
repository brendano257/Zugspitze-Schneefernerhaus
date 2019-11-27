"""
The filter file 2019_10_30_filters.json was somehow created with a time offset of -3 hours from Zugspitze time.

This fixes that, creating an _fixed file from the original.
"""
import os
import json
import datetime as dt

from datetime import datetime
from pathlib import Path

from settings import CORE_DIR, DB_NAME
from IO.db import connect_to_db, GcRun

engine, session = connect_to_db(DB_NAME, CORE_DIR)  # use the database to verify all 'fixed' dates

file = Path(os.getcwd()) / '2019_10_30_filters.json'

data = json.loads(file.read_text())

new_dict = {}
proof = {}  # helper dict to show conversion

for k, v in data.items():
    date = datetime.strptime(k[:16], '%Y-%m-%d %H:%M')
    date += dt.timedelta(hours=3)

    gc_run = (session.query(GcRun)
              .filter(GcRun.date >= date, GcRun.date <= date + dt.timedelta(minutes=1))
              .one_or_none())  # search within one minute of date

    if not gc_run:
        print('WARNING - Date for {date} STILL NOT FOUND!')

    new_key = date.strftime('%Y-%m-%d %H:%M') + k[16:]  # add back in data from the rest of the key

    proof[k] = new_key  # save k: new key to a helper dict
    new_dict[new_key] = v  # save new_key: old_value to dict

# print(proof)  # peak at old vs new key for verification

new_file = file.name.rstrip('.json') + '_fixed.json'

with open(new_file, 'w') as f:
    f.write(json.dumps(new_dict).replace('],', '],\n'))  # write a slightly prettified version to file
