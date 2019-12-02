"""
Plotting functions are a mess of duplicated and slightly modified code. This is an attempt to clean that up
substantially with classes and subclassed.
"""
from datetime import datetime
from pathlib import Path
from collections.abc import Sequence

import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from numpy.polynomial.polynomial import polyfit
from pandas.plotting import register_matplotlib_converters

color_set_y1=('#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33', '#a65628', '#f781bf')
color_set_y2=('#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854', '#ffd92f', '#e5c494', '#b3b3b3')


class TimeSeries:
    """
    A base-class for creating nearly unstyled timeseries plots.
    """
    def __init__(self, series, limits=None, major_ticks=None, minor_ticks=None, x_label_str=None,
                 y_label_str=None, title=None, date_format='%Y-%m-%d', filepath=None, save=True, show=False):
        """
        Create a Timeseries object to be plotted.

        :param dict series: data as {name: (xData, yData)}
        :param dict limits: plot limits, containing any of 'top', 'bottom', 'right', 'left'
        :param Sequence[datetime] major_ticks: major ticks for x axis
        :param Sequence[datetime] minor_ticks: minor ticks for x axis
        :param str x_label_str: string label for the x axis
        :param str y_label_str: string label for the y axis
        :param str title: title to be displayed on plot
        :param str date_format: C-format for date
        :param str | Path filepath: path for saving the file; otherwise saved in the current working directory
        :param bool save: save plot as png?
        :param bool show: show plot with figure.show()?
        """

        self.series = series
        self.major_ticks = major_ticks
        self.minor_ticks = minor_ticks
        self.x_label_str = x_label_str
        self.y_label_str = y_label_str
        self.title = title
        self.filepath = filepath
        self.date_format = date_format
        self.save = save
        self.show = show

        if not limits:
            limits = {}

        self.limits = limits

        self.figure = None
        self.primary_axis = None
        self.safe_names = None

        register_matplotlib_converters()

    def plot(self):
        self.get_axes()
        self.add_and_format_ticks()

        self.style()

        self.plot_all_series()

        self.set_axes_limits()  # limits must be set after plotting for limits of None to auto-scale
        self.format()  # legend must be set after data is added
        self.save_to_file()

    def plot_all_series(self):
        for name, data in self.series.items():
            self.primary_axis.plot(data[0], data[1], '-o')

    def make_safe_names(self):
        for k, _ in self.series.items():
            self.safe_names.append(k.replace('/', '_').replace(' ', '_'))

    def get_axes(self):
        self.figure = plt.figure()
        self.primary_axis = self.figure.gca()

    def set_axes_limits(self):
        if self.limits:
            self.primary_axis.set_xlim(**{k: v for k, v in self.limits.items() if k in ('right', 'left')})
            self.primary_axis.set_ylim(**{k: v for k, v in self.limits.items() if k in ('top', 'bottom')})

    def add_and_format_ticks(self):
        if self.major_ticks:
            self.primary_axis.set_xticks(self.major_ticks, minor=False)

        if self.minor_ticks:
            self.primary_axis.set_xticks(self.minor_ticks, minor=True)

        fmt = DateFormatter(self.date_format)
        self.primary_axis.xaxis.set_major_formatter(fmt)

        self.primary_axis.tick_params(axis='x', labelrotation=30)
        self.primary_axis.tick_params(axis='both', which='major', size=8, width=2, labelsize=15)

    def format(self, loc='upper left'):
        self.primary_axis.set_ylabel(self.y_label_str, fontsize=20)
        self.primary_axis.legend(self.series.keys(), loc=loc)

        if self.title:
            self.primary_axis.set_title(self.title, fontsize=24, y=1.02)

    def style(self):
        self.figure.set_size_inches(11.11, 7.406)
        self.figure.subplots_adjust(bottom=.20)

        for i in self.primary_axis.spines.values():
            i.set_linewidth(2)

    def save_to_file(self):
        if self.save:
            if not self.filepath:
                d = datetime.now()
                self.filepath = f'{d.strftime("%Y_%m_%d_%H%M")}_plot.png'

            self.figure.savefig(self.filepath, dpi=150)

        if self.show:
            self.figure.show()


class TwoAxisTimeSeries(TimeSeries):

    def __init__(self, series1, series2, limits_y1=None, limits_y2=None, major_ticks=None, minor_ticks=None,
                 x_label_str=None, y_label_str=None, y2_label_str=None, title=None, date_format='%Y-%m-%d',
                 filepath=None, save=True, show=False,
                 color_set_y2=('#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854', '#ffd92f', '#e5c494', '#b3b3b3')):

        super().__init__(series1, limits_y1, major_ticks, minor_ticks, x_label_str, y_label_str, title, date_format,
                         filepath, save, show)

        self.series2 = series2
        self.y2_label_str = y2_label_str
        self.color_set_y2 = (c for c in color_set_y2)  # convert to a generator

        if not limits_y2:
            limits_y2 = {}

        self.limits_y2 = limits_y2

        self.secondary_axis = None
        self.safe_names2 = None

    def plot_all_series(self):
        super().plot_all_series()

        for name, data in self.series2.items():
            self.secondary_axis.plot(data[0], data[1], '-o', color=next(self.color_set_y2))

    def make_safe_names(self):
        super().make_safe_names()

        for k, _ in self.series2.items():
            self.safe_names2.append(k.replace('/', '_').replace(' ', '_'))

    def get_axes(self):
        super().get_axes()
        self.secondary_axis = self.primary_axis.twinx()

    def set_axes_limits(self):
        super().set_axes_limits()

        if self.limits:
            self.secondary_axis.set_xlim(**{k: v for k, v in self.limits_y2.items() if k in ('right', 'left')})
            self.secondary_axis.set_ylim(**{k: v for k, v in self.limits_y2.items() if k in ('top', 'bottom')})

    def add_and_format_ticks(self):
        super().add_and_format_ticks()
        self.secondary_axis.tick_params(axis='both', which='major', size=8, width=2, labelsize=15)

    def format(self, loc='upper right'):
        super().format()
        self.secondary_axis.set_ylabel(self.y2_label_str, fontsize=20)
        self.secondary_axis.legend(self.series2.keys(), loc=loc)

    def style(self):
        super().style()
        for i in self.secondary_axis.spines.values():
            i.set_linewidth(2)
