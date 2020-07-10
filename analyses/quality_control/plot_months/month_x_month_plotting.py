"""
A script for plotting sequences of months at a time (by changing date_ranges).

Optional code for adding annotations based on stdevs and distance from the median is included. Plots include all data
and do not filter out the second sample of each day.
"""
import json
import statistics as s

from collections import OrderedDict
from calendar import monthrange

import pandas as pd

from settings import CORE_DIR, JSON_PUBLIC_DIR, DB_NAME
from IO.db import connect_to_db, GcRun, Compound, Standard
from plotting import create_daily_ticks, AnnotatedResponsePlot

engine, session = connect_to_db(DB_NAME, CORE_DIR)

date_ranges = pd.period_range('2019-11-1', '2020-06-01', freq='1M')

standard = (session.query(Standard)
            .filter(Standard.name == 'quantlist')
            .one())

compounds = [q.name for q in standard.quantifications]

outliers = {}  # dict of outliers, will take date and add compounds to a list

BASE_PLOT_DIR = CORE_DIR / 'analyses/quality_control/plot_months/plots'

if not BASE_PLOT_DIR.exists():
    BASE_PLOT_DIR.mkdir()

for month in date_ranges:
    month_dir = BASE_PLOT_DIR / f'{month.year:04d}_{month.month:02d}'
    if not month_dir.exists():
        month_dir.mkdir()

    for compound in compounds:

        # filter for date and compound on query
        results = (session.query(Compound.mr, GcRun.date)
                   .join(GcRun, GcRun.id == Compound.run_id)
                   .filter(Compound.name == compound)
                   .filter(GcRun.date >= month.start_time, GcRun.date < month.end_time)
                   .filter(GcRun.type == 5)
                   .order_by(GcRun.date)
                   .all())

        dates = [r.date for r in results]
        mrs = [r.mr for r in results]

        with open(JSON_PUBLIC_DIR / 'zug_plot_info.json', 'r') as file:
            compound_limits = json.loads(file.read())

        days = monthrange(month.year, month.month)[1]

        date_limits, major_ticks, minor_ticks = create_daily_ticks(days, end_date=month.end_time)
        major_ticks = [tick for num, tick in enumerate(major_ticks) if num % 2 == 0]  # eliminate every other tick

        bottom_limit = compound_limits.get(compound).get('bottom')
        top_limit = compound_limits.get(compound).get('top')
        span = (top_limit - bottom_limit) * .2  # outliers are outside 20% of the plot limits +/- the median

        real_mrs = [mr for mr in mrs if mr is not None]

        if len(real_mrs) > 1:
            median = s.median(real_mrs)
        else:
            median = 0

        annotations = []
        for mr, date in zip(mrs, dates):
            if mr is not None:
                if mr >= median + span or mr <= median - span:
                    annotations.append(date)

                    try:
                        date = date.strftime("%Y-%m-%d %H:%M")
                        outliers[date].add(compound)
                    except KeyError:
                        outliers[date] = {compound}
                else:
                    annotations.append("")

        p = AnnotatedResponsePlot(
            {compound: [dates, mrs]},
            limits={**date_limits, **compound_limits[compound]},
            major_ticks=major_ticks,
            minor_ticks=minor_ticks,
            date_format='%m-%d',
            filepath=month_dir / f'{compound}_plot.png',
            # annotations=annotations,
            # annotate_y=median
        )

        p.plot()

    print(f'Created plots for the month of {month.year:04d}/{month.month:02d}')

for k, v in outliers.items():
    outliers[k] = list(outliers[k])  # convert sets to lists to allow JSON-ing

outliers = OrderedDict(sorted(outliers.items()))

# move up from plot directory to save outliers.json
with open(BASE_PLOT_DIR / '../outliers.json', 'w') as file:
    file.write(json.dumps(outliers).replace('],', '],\n'))  # write a semi-human-readable json version
