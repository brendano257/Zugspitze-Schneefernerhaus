import json
from collections import namedtuple
from datetime import datetime

from settings import CORE_DIR, JSON_PUBLIC_DIR
from IO.db import GcRun, Compound, Integration, DBConnection
from plotting import create_monthly_ticks, MixingRatioPlot

PLOTDIR = CORE_DIR / 'analyses/quality_control/JFJ_comparison/plots'
PLOT_INFO = JSON_PUBLIC_DIR / 'zug_long_plot_info.json'

if not PLOTDIR.exists():
    PLOTDIR.mkdir()

with PLOT_INFO.open('r') as file:
    compound_limits = json.loads(file.read())

date_limits, major_ticks, minor_ticks = create_monthly_ticks(24, days_per_minor=0, start=datetime(2018, 1, 1))

major_ticks = major_ticks[::2]

converters = [lambda x, f=func: f(x) for func in (int, int, int, int, int, float, float, float, float, float, float)]

with open('JFJ_CFC_Helmig.txt', 'r') as file:
    for i in range(7):
        next(file)  # dispose of header

    t = namedtuple('data', [fieldname.strip().replace('-', '_') for fieldname in next(file).split(',')])

    data = [t(*[conv(field.strip()) for field, conv in zip(line.split(','), converters)]) for line in file]

jfj_dates = []
jfj_CFC_11 = []
jfj_CFC_12 = []
jfj_CFC_113 = []

for d in data:
    jfj_dates.append(datetime(d.year, d.month, d.day, d.hour, d.min, 0))
    jfj_CFC_11.append(d.CFC_11)
    jfj_CFC_12.append(d.CFC_12)
    jfj_CFC_113.append(d.CFC_113)


for compound, jfj_dataset in zip(('CFC-11', 'CFC-12', 'CFC-113'), (jfj_CFC_11, jfj_CFC_12, jfj_CFC_113)):

    date_limits = {'left': datetime(2018, 1, 1), 'right': datetime(2020, 1, 1)}

    with DBConnection() as session:
        z_results = (session.query(Compound.mr, GcRun.date, Integration.filename)
                            .join(Integration, Integration.id == Compound.integration_id)
                            .join(GcRun, GcRun.id == Integration.run_id)
                            .filter(GcRun.date >= date_limits['left'])
                            .filter(GcRun.date <= date_limits['right'])
                            .filter(GcRun.type == 5)
                            .filter(Compound.name == compound)
                            .filter(Compound.filtered == False)
                            .order_by(GcRun.date)).all()

        dates = [n.date for n in z_results]
        mrs = [n.mr for n in z_results]

        p = MixingRatioPlot(
            {compound: [dates, mrs], 'JFJ ' + compound: [jfj_dates, jfj_dataset]},
            title=f'Zugspitze and JFJ {compound} Plot',
            limits={**date_limits, **compound_limits[compound]},
            major_ticks=major_ticks,
            minor_ticks=minor_ticks,
            filepath=PLOTDIR / f'{compound}_plot.png'
        )

        p.plot()
