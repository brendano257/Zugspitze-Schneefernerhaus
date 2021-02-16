"""
This was created to allow creating blanket filters for specific time periods. Simply enter a start and end date and
a file containing every date between them will be generated and placed in "filters/final/".

compounds is specified as "all" so that all compounds are filtered by default, but compounds could be changed to
compounds = ["benzene", "toluene"] etc if desired for a specific output

Filters created with this script will be read in and filtered on the next pass of zugspitze_runtime.py
"""
__package__ = 'Z'

import json
from datetime import datetime

from settings import CORE_DIR, DB_NAME
from IO.db import connect_to_db, GcRun

engine, session = connect_to_db(DB_NAME, CORE_DIR)

filename = input('Filename for filter? (Do not include filetype) ')

start_date = input('What date do you want to filter from? (inclusive mm/dd/yyyy HH:MM) ')
end_date = input('What date do you want to filter to? (inclusive mm/dd/yyyy HH:MM) ')

start_date = datetime.strptime(start_date, '%m/%d/%Y %H:%M')
end_date = datetime.strptime(end_date, '%m/%d/%Y %H:%M')

compounds = ['all']  # can be specific list of compounds

dates = (session.query(GcRun.date)
		 .filter(GcRun.date >= start_date, GcRun.date <= end_date)
		 .filter(GcRun.type == 5)
		 .all())

dates = [d.date for d in dates]  # unpack from tuples

filters = {}

for d in dates:
	filters[d.strftime('%Y-%m-%d %H:%M')] = compounds

json_output = json.dumps(filters).replace('],', '],\n')

file = CORE_DIR / f'data/json/private/filters/final/{filename}.json'

if file.exists():
	raise FileExistsError
else:
	with file.open('w') as f:
		f.write(json_output)
