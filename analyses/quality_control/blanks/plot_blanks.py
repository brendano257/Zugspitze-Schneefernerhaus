"""
A scripting processor for plotting the blank data for all compounds as mixing ratios (where calculable).
"""

__package__ = 'Z'

import json
from datetime import datetime

from settings import CORE_DIR, JSON_PUBLIC_DIR, DB_NAME
from IO.db import connect_to_db, GcRun, Standard, Quantification, Compound, Integration, TempDir
from plotting import create_monthly_ticks, MixingRatioPlot

PLOT_DIR = CORE_DIR / "analyses/quality_control/blanks/plots"

if not PLOT_DIR.exists():
    PLOT_DIR.mkdir()


def plot_blank_data(logger):
    logger.info('Running plot_blank_data()')

    try:
        engine, session = connect_to_db(DB_NAME, CORE_DIR)
    except Exception as e:
        logger.error(f'Error {e.args} prevented connecting to the database in plot_new_data()')
        return False

    compounds_to_plot = (session.query(Quantification.name)
                         .join(Standard, Quantification.standard_id == Standard.id)
                         .filter(Standard.name == 'quantlist').all())
    compounds_to_plot[:] = [q.name for q in compounds_to_plot]

    date_limits, major_ticks, minor_ticks = create_monthly_ticks(6)

    with open(JSON_PUBLIC_DIR / 'zug_plot_info.json', 'r') as file:
        compound_limits = json.loads(file.read())

    for name in compounds_to_plot:
        results = (session.query(Compound.mr, Integration.date)
                          .join(Integration, Integration.id == Compound.integration_id)
                          .join(GcRun, GcRun.id == Integration.run_id)
                          .filter(Integration.date >= datetime(2018, 3, 1))
                          .filter(GcRun.type == 0)
                          .filter(Compound.name == name)
                          .order_by(Integration.date)
                          .all())

        dates = [r.date for r in results]
        mrs = [r.mr for r in results]

        p = MixingRatioPlot(
            {name: [dates, mrs]},
            limits={**date_limits, 'bottom': 0, 'top': compound_limits.get(name).get('top') * .10},
            # plotting from 0 to 10% of the max value for each compound for good blank scaling
            major_ticks=major_ticks,
            minor_ticks=minor_ticks,
            filepath=PLOT_DIR / f'{name}_plot.png'
        )

        p.plot()

    session.commit()
    session.close()
    engine.dispose()

    return True


if __name__ == '__main__':
    from utils import configure_logger

    logger = configure_logger(PLOT_DIR / '..', "blank_plotter")

    plot_blank_data(logger)
