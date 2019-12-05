"""
A script for plotting all data from 2013 onward for consistency checks.

This attempts to filter for only the first sample of every day by not taking samples past 5AM, and not taking any
samples that have an 'a' in their integration filename, eg 2019_03_19a_02.D, which is the standard notation for the
second ambient run of the day.
"""
__package__ = 'Z'

import json
from datetime import datetime

from sqlalchemy.sql.expression import extract, not_

from settings import CORE_DIR, DB_NAME, JSON_PUBLIC_DIR
from IO.db import GcRun, Standard, Quantification, Compound, OldData, Integration, connect_to_db
from plotting import create_monthly_ticks, MixingRatioPlot

PLOTDIR = CORE_DIR / 'analyses/quality_control/history_plots/plots'
PLOT_INFO = JSON_PUBLIC_DIR / 'zug_long_plot_info.json'


def plot_history():
    try:
        engine, session = connect_to_db(DB_NAME, CORE_DIR)
    except Exception as e:
        return False

    compounds_to_plot = (session.query(Quantification.name)
                         .join(Standard, Quantification.standard_id == Standard.id)
                         .filter(Standard.name == 'quantlist').all())

    compounds_to_plot[:] = [q.name for q in compounds_to_plot]

    date_limits, major_ticks, minor_ticks = create_monthly_ticks(72, days_per_minor=0, start=datetime(2013, 1, 1))

    major_ticks = major_ticks[::4]

    with PLOT_INFO.open('r') as file:
        compound_limits = json.loads(file.read())

    for name in compounds_to_plot:

        old_results = (session.query(OldData.date, OldData.mr)
                       .filter(OldData.name == name)
                       .order_by(OldData.date)
                       .all())

        # extract and filter by 4AM or earlier to only get first measurement on normal days
        # also filter by 'a' not in the filename to avoid "2018_10a_02.D" ie second ambient samples
        new_results = (session.query(Compound.mr, Integration.date)
                       .join(Integration, Integration.id == Compound.integration_id)
                       .join(GcRun, GcRun.id == Integration.run_id)
                       .filter(Integration.date >= date_limits['left'])
                       .filter(extract('hour', Integration.date) < 5)
                       .filter(not_(Integration.filename.in_('a')))
                       .filter(GcRun.type == 5)
                       .filter(Compound.name == name)
                       .filter(Compound.filtered == False)
                       .order_by(Integration.date)
                       .all())

        dates = [o.date for o in old_results]
        mrs = [o.mr for o in old_results]

        dates.extend([n.date for n in new_results])
        mrs.extend([n.mr for n in new_results])

        p = MixingRatioPlot(
            {name: [dates, mrs]},
            limits={**date_limits, **compound_limits[name]},
            major_ticks=major_ticks,
            minor_ticks=minor_ticks,
            filepath=PLOTDIR / f'{name}_plot.png'
        )

        p.plot()

    session.commit()
    session.close()
    engine.dispose()


plot_history()
