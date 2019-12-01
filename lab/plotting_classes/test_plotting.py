__package__ = None

from datetime import datetime

from scratch_plotting import TimeSeries

from IO.db.models import Compound, GcRun
from plotting import create_daily_ticks
from reporting import abstract_query

data1 = abstract_query([GcRun.date, Compound.mr], [Compound.name == 'ethane',
                                                   GcRun.date.between(datetime(2019, 2, 1), datetime(2019, 2, 14)),
                                                   GcRun.type == 5, Compound.filtered == False])

data2 = abstract_query([GcRun.date, Compound.mr], [Compound.name == 'propane',
                                                   GcRun.date.between(datetime(2019, 2, 1), datetime(2019, 2, 14)),
                                                   GcRun.type == 5, Compound.filtered == False])

data_series = {
    'ethane': ([d.date for d in data1], [d.mr for d in data1]),
    'propane': ([d.date for d in data2], [d.mr for d in data2])
}

limits, major, minor = create_daily_ticks(14, end_date=datetime(2019, 2, 14))


def test_timeseries():
    t = TimeSeries(data_series, limits=limits, major_ticks=major, minor_ticks=minor, save=False, show=True)
    t.plot()

test_timeseries()
