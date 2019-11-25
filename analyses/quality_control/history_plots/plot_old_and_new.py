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
from IO.db import GcRun, Standard, Quantification, Compound, OldData, Integration, TempDir, connect_to_db
from plotting import zugspitze_mixing_plot, create_monthly_ticks

PLOTDIR = CORE_DIR / 'analyses/quality_control/history_plots/plots'
PLOT_INFO = JSON_PUBLIC_DIR / 'zug_long_plot_info.json'


def plot_history():
    try:
        engine, session = connect_to_db(DB_NAME, CORE_DIR)
    except Exception:
        return False

    compounds_to_plot = (session.query(Quantification.name)
                         .join(Standard, Quantification.standard_id == Standard.id)
                         .filter(Standard.name == 'quantlist').all())

    compounds_to_plot[:] = [q.name for q in compounds_to_plot]

    date_limits, major_ticks, minor_ticks = create_monthly_ticks(72, days_per_minor=0, start=datetime(2013,1,1))

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
        for result in new_results:
            dates.append(result[1])
            mrs.append(result[0])

        with TempDir(PLOTDIR):
            try:
                compound_limits.get(name).get('bottom')
            except:
                print(f'Compound {name} needs limits to plot!')
                continue

            zugspitze_mixing_plot(None, ({name: [dates, mrs]}),
                                          limits={'right': date_limits.get('right', None),
                                                  'left': date_limits.get('left', None),
                                                  'bottom': compound_limits.get(name).get('bottom'),
                                                  'top': compound_limits.get(name).get('top')},
                                          major_ticks=major_ticks,
                                          minor_ticks=minor_ticks)

    session.commit()
    session.close()
    engine.dispose()


plot_history()
