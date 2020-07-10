"""
A script for plotting all data from 2018-03 onward for quality control checks.
"""
__package__ = 'Z'

import json
import statistics as s

from datetime import datetime
from calendar import monthrange

import pandas as pd

from settings import CORE_DIR, JSON_PUBLIC_DIR, DB_NAME
from IO.db import connect_to_db, GcRun, Compound, Standard, final_data_first_sample_only_filter
from plotting import create_daily_ticks, create_monthly_ticks, AnnotatedResponsePlot

with open(JSON_PUBLIC_DIR / 'zug_plot_info.json', 'r') as file:
    compound_limits = json.loads(file.read())

engine, session = connect_to_db(DB_NAME, CORE_DIR)

start_date = datetime(2018, 3, 1)
end_date = datetime(2018, 3, 1)

date_ranges = pd.period_range(start_date, end_date, freq='1M')

standard = (session.query(Standard)
            .filter(Standard.name == 'quantlist')
            .one())

compounds = [q.name for q in standard.quantifications]

BASE_PLOT_DIR = CORE_DIR / 'analyses/quality_control/preliminary_final_plots/plots'

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
                   .filter(Compound.filtered == False)
                   .order_by(GcRun.date)
                   .all())

        dates = [r.date for r in results]
        mrs = [r.mr for r in results]

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

        p = AnnotatedResponsePlot(
            {compound: [dates, mrs]},
            limits={**date_limits, **compound_limits[compound]},
            major_ticks=major_ticks,
            minor_ticks=minor_ticks,
            date_format='%m-%d',
            filepath=month_dir / f'{compound}_plot.png'
        )

        p.plot()

    print(f'Created plots for the month of {month.year:04d}/{month.month:02d}')


full_plot_dir = BASE_PLOT_DIR / 'full_plots'

if not full_plot_dir.exists():
    full_plot_dir.mkdir()

for compound in compounds:

    date_limits, major_ticks, minor_ticks = create_monthly_ticks(22, start=start_date)

    # filter for date and compound on query
    results = (session.query(Compound.mr, GcRun.date)
               .join(GcRun, GcRun.id == Compound.run_id)
               .filter(Compound.name == compound)
               .filter(GcRun.date >= date_limits['left'], GcRun.date < date_limits['right'])
               .filter(GcRun.type == 5)
               .filter(Compound.filtered == False)
               .filter(*final_data_first_sample_only_filter)
               .order_by(GcRun.date))

    for f in final_data_first_sample_only_filter:
        results = results.filter(f)

    results = results.all()

    dates = [r.date for r in results]
    mrs = [r.mr for r in results]

    p = AnnotatedResponsePlot(
        {compound: [dates, mrs]},
        {**date_limits, **compound_limits[compound]},
        major_ticks=major_ticks,
        minor_ticks=minor_ticks,
        date_format='%Y-%m',
        filepath=full_plot_dir / f'{compound}_plot.png'
    )

    p.plot()
