__package__ = 'Z'

from datetime import datetime

from settings import CORE_DIR, DB_NAME
from plotting import create_daily_ticks, MixingRatioPlot
from IO.db import connect_to_db, Standard, Compound, GcRun, TempDir

SELF_DIR = CORE_DIR / 'analyses/quality_control/2018_05_shifts'
ALL_COMPOUND_PLOTS = SELF_DIR / 'all_plots'

if not ALL_COMPOUND_PLOTS.exists():
    ALL_COMPOUND_PLOTS.mkdir()

engine, session = connect_to_db(DB_NAME, CORE_DIR)

standard = (session.query(Standard)
            .filter(Standard.name == 'quantlist')
            .one())

compounds = [q.name for q in standard.quantifications]

# plot one month around the working standard change-over
limits = (datetime(2018, 5, 1), datetime(2018, 6, 15))
days = (limits[1] - limits[0]).days

for compound in compounds:
    results = (session.query(Compound.mr, GcRun.date)
                      .join(GcRun, GcRun.id == Compound.run_id)
                      .filter(Compound.name == compound)
                      .filter(Compound.filtered == False)
                      .filter(GcRun.date.between(limits[0], limits[1]))
                      .filter(GcRun.type == 5)
                      .order_by(GcRun.date)
                      .all())

    dates = [r.date for r in results]
    mrs = [r.mr for r in results]

    date_limits, major_ticks, minor_ticks = create_daily_ticks(days, minors_per_day=2, end_date=limits[1])
    major_ticks = [m for ind, m in enumerate(major_ticks) if not ind % 4]

    p = MixingRatioPlot(
        {compound: [dates, mrs]},
        limits={'left': date_limits.get('left'),
                'right': date_limits.get('right')},
        major_ticks=major_ticks, minor_ticks=minor_ticks,
        filepath=ALL_COMPOUND_PLOTS / f'{compound}_plot_working_std_shift_qc.png'
    )

    p.plot()
