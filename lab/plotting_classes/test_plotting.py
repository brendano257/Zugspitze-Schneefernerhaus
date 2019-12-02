__package__ = None

from datetime import datetime

from scratch_plotting import TimeSeries, TwoAxisTimeSeries

from IO.db.models import Compound, GcRun
from plotting import create_daily_ticks
from reporting import abstract_query

ethane = abstract_query([GcRun.date, Compound.mr], [Compound.name == 'ethane',
                                                    GcRun.date.between(datetime(2019, 2, 1), datetime(2019, 2, 14)),
                                                    GcRun.type == 5, Compound.filtered == False])

propane = abstract_query([GcRun.date, Compound.mr], [Compound.name == 'propane',
                                                     GcRun.date.between(datetime(2019, 2, 1), datetime(2019, 2, 14)),
                                                     GcRun.type == 5, Compound.filtered == False])

iButane = abstract_query([GcRun.date, Compound.mr], [Compound.name == 'i-butane',
                                                     GcRun.date.between(datetime(2019, 2, 1), datetime(2019, 2, 14)),
                                                     GcRun.type == 5, Compound.filtered == False])

nButane = abstract_query([GcRun.date, Compound.mr], [Compound.name == 'n-butane',
                                                     GcRun.date.between(datetime(2019, 2, 1), datetime(2019, 2, 14)),
                                                     GcRun.type == 5, Compound.filtered == False])

hfc152a = abstract_query([GcRun.date, Compound.mr], [Compound.name == 'HFC-152a',
                                                       GcRun.date.between(datetime(2019, 2, 1), datetime(2019, 2, 14)),
                                                       GcRun.type == 5, Compound.filtered == False])

data_series = {
    'ethane': ([d.date for d in ethane], [d.mr for d in ethane]),
    'propane': ([d.date for d in propane], [d.mr for d in propane])
}

data_series_c4 = {
    'i-butane': ([d.date for d in iButane], [d.mr for d in iButane]),
    'n-butane': ([d.date for d in nButane], [d.mr for d in nButane])
}

data_series_c4_2 = {
    'HFC-152a': ([d.date for d in hfc152a], [d.mr for d in hfc152a])
}

print(data_series_c4_2)

limits, major, minor = create_daily_ticks(14, end_date=datetime(2019, 2, 14))


def test_timeseries():
    t = TimeSeries(data_series, limits=limits, major_ticks=major, minor_ticks=minor, save=False, show=True)
    t.plot()


def test_twoaxis_timeseries():
    t = TwoAxisTimeSeries(data_series_c4, data_series_c4_2, limits_y1=limits,
                          limits_y2={'bottom': -20, 'top': 30},
                          major_ticks=major,
                          minor_ticks=minor, save=False, show=True)
    t.plot()


test_timeseries()
test_twoaxis_timeseries()
