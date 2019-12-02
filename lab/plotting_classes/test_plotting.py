__package__ = None

from datetime import datetime
from random import randint

from scratch_plotting import (TimeSeries, TwoAxisTimeSeries, LinearityPlot, MixingRatioPlot, PeakAreaPlot,
                               StandardPeakAreaPlot, LogParameterPlot)

from IO.db.models import Compound, GcRun, LogFile
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

hfc152a = abstract_query([GcRun.date, Compound.mr, Compound.pa], [Compound.name == 'HFC-152a',
                                                       GcRun.date.between(datetime(2019, 2, 1), datetime(2019, 2, 14)),
                                                       GcRun.type == 5, Compound.filtered == False])

hfc152a_stds = abstract_query([GcRun.date, Compound.mr, Compound.pa], [Compound.name == 'HFC-152a',
                                                                       GcRun.date.between(datetime(2019, 2, 1),
                                                                                          datetime(2019, 2, 14)),
                                                                       GcRun.type == 2, Compound.filtered == False])

params = abstract_query([LogFile.date, LogFile.trap_temp_fh, LogFile.trap_temp_bakeout,
                             LogFile.gc_oven_temp, LogFile.mfc1_ramp], ())

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

data_series_2 = {
    'HFC-152a': ([d.date for d in hfc152a], [d.pa for d in hfc152a])
}

data_series_3 = {
    'HFC-152a': ([d.date for d in hfc152a_stds], [d.pa for d in hfc152a_stds])
}

param_series_1 = {
    'Trap Temp @ FH': ([d.date for d in params], [d.trap_temp_fh for d in params]),
    'Trap Temp @ Bakeout': ([d.date for d in params], [d.trap_temp_bakeout for d in params])
}

param_series_2 = {
    'GC Oven': ([d.date for d in params], [d.gc_oven_temp for d in params]),
}

param_series_3 = {
    'MFC1 Ramp': ([d.date for d in params], [d.mfc1_ramp for d in params]),
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
                      limits={'top': 6000, 'bottom': 0, 'left': 0}, save=False, show=True)
    t.plot()


def test_mixing_ratio_plot():
    t = MixingRatioPlot(data_series_two_axis2)
    t.plot()


def test_peak_area_plot():
    t = PeakAreaPlot(data_series_2, show=True, save=False)
    t.plot()


def test_std_peak_area_plot():
    t = StandardPeakAreaPlot(data_series_3, show=True, save=False)
    t.plot()


def test_log_parameter_plot():
    t = LogParameterPlot(param_series_1, 'Trap Temps', 'log_trap_temps.png', show=True, save=False)
    t.plot()


test_timeseries()
test_twoaxis_timeseries()
test_linearity_plot()
test_mixing_ratio_plot()
test_peak_area_plot()
test_std_peak_area_plot()
test_log_parameter_plot()
