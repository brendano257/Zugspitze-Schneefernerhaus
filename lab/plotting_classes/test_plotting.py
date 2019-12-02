__package__ = None

from datetime import datetime
from random import randint

from scratch_plotting import TimeSeries, TwoAxisTimeSeries, LinearityPlot

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

data_series_two_axis1 = {
    'i-butane': ([d.date for d in iButane], [d.mr for d in iButane]),
    'n-butane': ([d.date for d in nButane], [d.mr for d in nButane])
}

data_series_two_axis2 = {
    'HFC-152a': ([d.date for d in hfc152a], [d.mr for d in hfc152a])
}

limits, major, minor = create_daily_ticks(14, end_date=datetime(2019, 2, 14))

lin_data_x = [n * 1000 for n in range(1, 9)]  # create 8 samples of increasing 'sample volume'
lin_data_y = [.5 * x + randint(-750, 750) for x in lin_data_x]  # create y-data with variable offset from formula


def test_timeseries():
    t = TimeSeries(data_series, limits=limits, major_ticks=major, minor_ticks=minor, save=False, show=True)
    t.plot()


def test_twoaxis_timeseries():
    t = TwoAxisTimeSeries(data_series_two_axis1, data_series_two_axis2, limits_y1=limits,
                          limits_y2={'bottom': -20, 'top': 30},
                          major_ticks=major,
                          minor_ticks=minor, save=False, show=True)
    t.plot()


def test_linearity_plot():
    t = LinearityPlot('Fake Compound', lin_data_x, lin_data_y,
                      limits={'top': 6000, 'bottom': 0}, save=False, show=True)
    t.plot()


test_timeseries()
test_twoaxis_timeseries()
test_linearity_plot()
