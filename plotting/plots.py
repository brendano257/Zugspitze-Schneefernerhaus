from pathlib import Path
from datetime import datetime

from abc import ABC, abstractmethod
from collections.abc import Sequence

import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from numpy.polynomial.polynomial import polyfit
from pandas.plotting import register_matplotlib_converters

__all__ = ['zugspitze_mixing_plot', 'zugspitze_qc_plot', 'zugspitze_pa_plot', 'zugspitze_parameter_plot',
           'zugspitze_twoaxis_parameter_plot', 'zugspitze_linearity_plot', 'Plot2D', 'TimeSeries', 'ResponsePlot',
           'MixingRatioPlot', 'PeakAreaPlot', 'StandardPeakAreaPlot', 'LogParameterPlot', 'TwoAxisTimeSeries',
           'TwoAxisResponsePlot', 'TwoAxisLogParameterPlot', 'LinearityPlot']


class Plot2D(ABC):
    """
    Plot2D is an abstract class meant to be subclassed by just about any 2D plot for convenience methods.

    Plot2D contains project-wide features common to 2D plots, like the need to get the axes, set a title, and set some
    basic styling on the plot. It is abstract to prevent it's stand-alone use, which has no purpose.
    """

    @abstractmethod
    def __init__(self):
        """
        Abstract to prevent Plot2D from being created.

        Title, labels, etc are included to silence IDE warnings about referencing non-existent fields or defining them
        outside __init__.
        """
        self.title = None
        self.x_label_str = None
        self.y_label_str = None
        self.save = None
        self.show = None
        self.minor_ticks = None
        self.major_ticks = None
        self.figure = None
        self.primary_axis = None
        self.filepath = None
        self.limits = {}  # limits must be an empty dict so it can be iterated, even if empty

    @abstractmethod
    def plot(self):
        """Abstract to stipulate that any subclass should have a public plot function."""
        pass

    def _get_axes(self):
        """Assign the figure and axes to self. Needed prior to any plotting, adding limits, title, etc."""

        self.figure = plt.figure()
        self.primary_axis = self.figure.gca()

    def _style_plot(self):
        """
        Style the size of the figure, adjust the bottom for titled date labels, and tweak line widths across the plot.

        :return None:
        """
        self.figure.set_size_inches(11.11, 7.406)
        self.figure.subplots_adjust(bottom=.20)

        for i in self.primary_axis.spines.values():
            i.set_linewidth(2)

    def _add_and_format_ticks(self):
        """
        Add major and minor ticks to the axis if they were specified. In all cases, change tick width and label size.

        :return None:
        """
        if self.major_ticks:
            self.primary_axis.set_xticks(self.major_ticks, minor=False)

        if self.minor_ticks:
            self.primary_axis.set_xticks(self.minor_ticks, minor=True)

        self.primary_axis.tick_params(axis='both', which='major', size=8, width=2, labelsize=15)

    def _set_axes_limits(self):
        """Set the limits on the y-axis"""
        self._set_axis()  # operates on self.primary_axis using self.limits by default

    def _set_axis(self, axis_attr='primary_axis', limits_attr='limits'):
        """
        Helper method that defaults to setting the first/only axis limits.

        :param str axis_attr: name of the attribute that contains the axis name that should be set
        :param str limits_attr: name of the attribute that contains the limits name that should be set on the axis
        :return None:
        """
        axis = getattr(self, axis_attr)
        limits = getattr(self, limits_attr)

        if self.limits:
            axis.set_xlim(**{k: v for k, v in limits.items() if k in ('right', 'left')})
            axis.set_ylim(**{k: v for k, v in limits.items() if k in ('top', 'bottom')})

    def axis(self):
        """Set the axes labels on the primary axis."""

        self.primary_axis.set_ylabel(self.y_label_str, fontsize=20)
        self.primary_axis.set_xlabel(self.x_label_str, fontsize=20)

    def _set_title(self):
        """Set the title for the plot."""

        if self.title:
            self.primary_axis.set_title(self.title, fontsize=24, y=1.02)

    def _save_to_file(self):
        """Save the figure with a default filepath of the current working dir with a datetime-formatted filename."""
        if self.save:
            if not self.filepath:
                d = datetime.now()
                self.filepath = f'{d.strftime("%Y_%m_%d_%H%M")}_plot.png'

            self.figure.savefig(self.filepath, dpi=150)

        if self.show:
            self.figure.show()
        else:
            plt.close(self.figure)


class TimeSeries(Plot2D):
    """
    A base-class for creating nearly unstyled timeseries plots.

    TimeSeries gets most of its basic behavior from Plot2D, but adds formatting specific to having a datetime x-axis,
    as well as implementing methods for actually plotting data. Though you can instantiate TimeSeries, it's likely to be
    used almost exclusively as a subclass.
    """
    def __init__(self, series, limits=None, major_ticks=None, minor_ticks=None, x_label_str=None, y_label_str=None,
                 title=None, date_format='%Y-%m-%d', filepath=None, save=True, show=False):
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

        super().__init__()  # useless, just keeps IDE quiet
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
            limits = {}  # limits must be an empty dict so it can be iterated, even if empty

        self.limits = limits

        self.figure = None  # these are defined here to keep all definitions in __init__
        self.primary_axis = None
        self.safe_names = []

        register_matplotlib_converters()

    def plot(self):
        """
        Call all internal methods needed to create and style plot, either saving or showing plot at the end.

        :return None:
        """
        self._get_axes()
        self._add_and_format_ticks()

        self._style_plot()

        self._plot_all_series()

        self._set_axes_limits()  # limits must be set after plotting for limits of None to auto-scale
        self.axis()
        self._set_legend()  # legend must be set after data is added
        self._set_title()
        self._save_to_file()

    def _plot_all_series(self):
        """Plot data on the primary axis."""
        for name, data in self.series.items():
            self.primary_axis.plot(data[0], data[1], '-o')

    def _make_safe_names(self):
        """Remove common unsafe characters from parameter names to make them safe for filenames."""

        for k, _ in self.series.items():
            self.safe_names.append(k.replace('/', '_').replace(' ', '_'))

        return self.safe_names

    def _add_and_format_ticks(self):
        """
        Call Plot2D super method to add basic ticks, then format appropriately for a timeseries plot.

        :return None:
        """
        super()._add_and_format_ticks()

        fmt = DateFormatter(self.date_format)
        self.primary_axis.xaxis.set_major_formatter(fmt)
        self.primary_axis.tick_params(axis='x', labelrotation=30)

    def _set_legend(self, loc='upper left'):
        self.primary_axis.legend(self.series.keys(), loc=loc)


class ResponsePlot(TimeSeries):
    """
    ResponsePlots contain the minimal styling to create a project plot for mixing ratios or peak areas.

    ResponsePlots are rarely going to be used outside of subclassing. They're essentially the base for any plot that is
    set up to plot a response (peak area, mixing ratio, logged parameter) against time.
    """
    def __init__(self, series, limits=None, major_ticks=None, minor_ticks=None, x_label_str=None,
                 y_label_str=None, type_=None, title=None, date_format='%Y-%m-%d',
                 filepath=None, save=True, show=False):
        """
        Create an instance, using next-to-no defaults.

        :param dict series: data as {name: (xData, yData)}
        :param dict limits: plot limits, containing any of 'top', 'bottom', 'right', 'left'
        :param Sequence[datetime] major_ticks: major ticks for x axis
        :param Sequence[datetime] minor_ticks: minor ticks for x axis
        :param str x_label_str: string label for the x axis
        :param str y_label_str: string label for the y axis
        :param str type_: Usually 'Mixing Ratios' or 'Peak Areas'; becomes part of the title
        :param str title: title to be displayed on plot
        :param str date_format: C-format for date
        :param str | Path filepath: path for saving the file; otherwise saved in the current working directory
        :param bool save: save plot as png?
        :param bool show: show plot with figure.show()?
        """

        if not title:
            # title should be the names of whatever is plotting, plus the type of the plot, if any
            title = f'Zugspitze {", ".join(series.keys())} {type_}'

        super().__init__(series, limits, major_ticks, minor_ticks, x_label_str, y_label_str,
                         title, date_format, filepath, save, show)

    def _save_to_file(self):
        """Override _save_to_file and make the path the filename-safe names of what's plotted + _plot.png"""
        if not self.filepath:
            plotted_names = self._make_safe_names()
            self.filepath = f'{"_".join(plotted_names)}_plot.png'

        super()._save_to_file()

    def _set_legend(self, loc=None):
        """Override _set_legend with loc=None to trigger matplotlibs auto-placement of the legend."""
        super()._set_legend(loc)


class MixingRatioPlot(ResponsePlot):
    """
    MixingRatioPlots are the base for any plot of a compound's mixing ratios.
    """

    def __init__(self, series, limits=None, major_ticks=None, minor_ticks=None, x_label_str=None,
                 y_label_str='Mixing Ratio (pptv)', type_='Mixing Ratios', title=None, date_format='%Y-%m-%d',
                 filepath=None, save=True, show=False):
        """
        Create an instance, using defaults suitable for mixing ratio plots.

        :param dict series: data as {name: (xData, yData)}
        :param dict limits: plot limits, containing any of 'top', 'bottom', 'right', 'left'
        :param Sequence[datetime] major_ticks: major ticks for x axis
        :param Sequence[datetime] minor_ticks: minor ticks for x axis
        :param str x_label_str: string label for the x axis
        :param str y_label_str: string label for the y axis
        :param str type_: Usually 'Mixing Ratios' or 'Peak Areas'; becomes part of the title
        :param str title: title to be displayed on plot
        :param str date_format: C-format for date
        :param str | Path filepath: path for saving the file; otherwise saved in the current working directory
        :param bool save: save plot as png?
        :param bool show: show plot with figure.show()?
        """

        super().__init__(series, limits, major_ticks, minor_ticks, x_label_str,
                         y_label_str, type_, title, date_format,
                         filepath, save, show)


class PeakAreaPlot(ResponsePlot):
    """
    MixingRatioPlots are the base for any plot of a compound's peak areas.
    """

    def __init__(self, series, limits=None, major_ticks=None, minor_ticks=None, x_label_str=None,
                 y_label_str='Peak Area', type_='Peak Areas', title=None, date_format='%Y-%m-%d',
                 filepath=None, save=True, show=False):
        """
        Create an instance, using defaults suitable for peak area ratio plots.

        :param dict series: data as {name: (xData, yData)}
        :param dict limits: plot limits, containing any of 'top', 'bottom', 'right', 'left'
        :param Sequence[datetime] major_ticks: major ticks for x axis
        :param Sequence[datetime] minor_ticks: minor ticks for x axis
        :param str x_label_str: string label for the x axis
        :param str y_label_str: string label for the y axis
        :param str type_: Usually 'Mixing Ratios' or 'Peak Areas'; becomes part of the title
        :param str title: title to be displayed on plot
        :param str date_format: C-format for date
        :param str | Path filepath: path for saving the file; otherwise saved in the current working directory
        :param bool save: save plot as png?
        :param bool show: show plot with figure.show()?
        """
        super().__init__(series, limits, major_ticks, minor_ticks, x_label_str,
                         y_label_str, type_, title, date_format,
                         filepath, save, show)

    def _save_to_file(self):
        """Override _save_to_file and make the path the filename-safe names of what's plotted + _pa_plot.png"""
        if not self.filepath:
            plotted_names = self._make_safe_names()
            self.filepath = f'{"_".join(plotted_names)}_pa_plot.png'

        super()._save_to_file()


class StandardPeakAreaPlot(ResponsePlot):
    """
    MixingRatioPlots are the base for any plot of a compound's peak areas from standards.

    Overrides are only for file save name and changing default values in __init__.
    """

    def __init__(self, series, limits=None, major_ticks=None, minor_ticks=None, x_label_str=None,
                 y_label_str='Peak Area', type_='Standard Peak Areas', title=None, date_format='%Y-%m-%d',
                 filepath=None, save=True, show=False):
        """
        Create an instance, using defaults suitable for standard peak area ratio plots.

        :param dict series: data as {name: (xData, yData)}
        :param dict limits: plot limits, containing any of 'top', 'bottom', 'right', 'left'
        :param Sequence[datetime] major_ticks: major ticks for x axis
        :param Sequence[datetime] minor_ticks: minor ticks for x axis
        :param str x_label_str: string label for the x axis
        :param str y_label_str: string label for the y axis
        :param str type_: Usually 'Mixing Ratios' or 'Peak Areas'; becomes part of the title
        :param str title: title to be displayed on plot
        :param str date_format: C-format for date
        :param str | Path filepath: path for saving the file; otherwise saved in the current working directory
        :param bool save: save plot as png?
        :param bool show: show plot with figure.show()?
        """
        super().__init__(series, limits, major_ticks, minor_ticks, x_label_str,
                         y_label_str, type_, title, date_format,
                         filepath, save, show)

    def _save_to_file(self):
        """Override _save_to_file and make the path the filename-safe names of what's plotted + _plot.png"""
        if not self.filepath:
            plotted_names = self._make_safe_names()
            self.filepath = f'{"_".join(plotted_names)}_plot.png'

        super()._save_to_file()


class LogParameterPlot(ResponsePlot):
    """LogParameterPlots are the base for plotting any set of parameters on a single axis"""

    def __init__(self, series, title, filepath, limits=None, major_ticks=None, minor_ticks=None, x_label_str=None,
                 y_label_str='Temperature (\xb0C)', date_format='%Y-%m-%d', save=True, show=False):
        """
        Create a ResponsePlot, but make the title and filepath mandatory for LogParameterPlot.

        :param dict series: data as {name: (xData, yData)}
        :param dict limits: plot limits, containing any of 'top', 'bottom', 'right', 'left'
        :param Sequence[datetime] major_ticks: major ticks for x axis
        :param Sequence[datetime] minor_ticks: minor ticks for x axis
        :param str x_label_str: string label for the x axis
        :param str y_label_str: string label for the y axis
        :param str date_format: C-format for date
        :param str | Path filepath: path for saving the file; otherwise saved in the current working directory
        :param bool save: save plot as png?
        :param bool show: show plot with figure.show()?
        """
        super().__init__(series, limits, major_ticks, minor_ticks, x_label_str,
                         y_label_str, '', title, date_format,
                         filepath, save, show)


class TwoAxisTimeSeries(TimeSeries):
    """
    A base class extending TimeSeries that creates a nearly unstyled plot with two y-axes.

    Again, this is not likely to be instantiated, and instead will most often be subclassed.
    """

    def __init__(self, series1, series2, limits_y1=None, limits_y2=None, major_ticks=None, minor_ticks=None,
                 x_label_str=None, y_label_str=None, y2_label_str=None, title=None, date_format='%Y-%m-%d',
                 filepath=None, save=True, show=False,
                 color_set_y2=('#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854', '#ffd92f', '#e5c494', '#b3b3b3')):
        """
        Create the instance and define defaults.

        :param dict series1: data for the primary (left) y axis as {name: (xData, yData)}
        :param dict series2: data for the secondary (right) y axis as {name: (xData, yData)}
        :param dict limits_y1: plot limits for the primary (left) y axis;
            containing any of 'top', 'bottom', 'right', 'left'; if limits_y2 contains a right or left limit it *will*
            overwrite any top/bottom limit given by limits_y1
        :param dict limits_y2: plot limits for the secondary (right) y axis;
            containing any of 'top', 'bottom', 'right', 'left'; if limits_y2 contains a right or left limit it *will*
            overwrite any right/left limit given by limits_y1
        :param Sequence[datetime] major_ticks: major ticks for x axis
        :param Sequence[datetime] minor_ticks: minor ticks for x axis
        :param str x_label_str: string label for the x axis
        :param str y_label_str: string label for the primary (left) y axis
        :param str y2_label_str: string label for the secondary (right) y axis
        :param str title: title to be displayed on plot
        :param str date_format: C-format for date
        :param str|Path filepath: path for saving the file; otherwise saved in the current working directory
        :param boolean save: save plot as png?
        :param boolean show: show plot with figure.show()?
        :param Sequence[str] color_set_y2: abitrary-length sequence of valid Matplotlib color values; defaulted to a
            ColorBrewer set (http://colorbrewer2.org/#type=qualitative&scheme=Set2&n=8).
        :raises StopIteration: if color_set_y2 is exhausted (ie: not len(color_set_y2) >= len(series2))
        """
        super().__init__(series1, limits_y1, major_ticks, minor_ticks, x_label_str, y_label_str, title, date_format,
                         filepath, save, show)

        self.series2 = series2
        self.y2_label_str = y2_label_str
        self.color_set_y2 = (c for c in color_set_y2)  # convert to a generator

        if not limits_y2:
            limits_y2 = {}  # limits must be an empty dict so it can be iterated, even if empty

        self.limits_y2 = limits_y2

        self.secondary_axis = None
        self.safe_names2 = None

    def _plot_all_series(self):
        """
        Plot the primary and secondary axis data, using a separate color scheme for the second axis.

        :return None:
        """
        super()._plot_all_series()

        for name, data in self.series2.items():
            self.secondary_axis.plot(data[0], data[1], '-o', color=next(self.color_set_y2))

    def _make_safe_names(self):
        """Remove common unsafe characters from parameter names to make them safe for filenames."""
        super()._make_safe_names()

        for k, _ in self.series2.items():
            self.safe_names2.append(k.replace('/', '_').replace(' ', '_'))

        return self.safe_names2

    def _get_axes(self):
        """Get primary and secondary axes and assign to self."""
        super()._get_axes()
        self.secondary_axis = self.primary_axis.twinx()

    def _set_axes_limits(self):
        """Set limits for primary and secondary axes."""
        super()._set_axes_limits()  # calls with defaults to format the primary axis

        self._set_axis('secondary_axis', 'limits_y2')

    def _add_and_format_ticks(self):
        """Add ticks to primary axis, then format secondary axis."""
        super()._add_and_format_ticks()
        self.secondary_axis.tick_params(axis='both', which='major', size=8, width=2, labelsize=15)

    def axis(self):
        """Set labels for both axes."""
        super().axis()
        self.secondary_axis.set_ylabel(self.y2_label_str, fontsize=20)

    def _set_legend(self, loc='upper right'):
        """Set legend on primary and secondary axes, putting legend in upper corner nearest each axis."""
        super()._set_legend()  # calls with upper left as the default to set primary axis legend
        self.secondary_axis.legend(self.series2.keys(), loc=loc)  # set secondary legend in other corner

    def _style_plot(self):
        """Style line-widths of both axes, and format plot size."""
        super()._style_plot()
        for i in self.secondary_axis.spines.values():
            i.set_linewidth(2)


class TwoAxisResponsePlot(TwoAxisTimeSeries):
    """
    TwoAxisResponsePlots contain the minimal styling to create a project plot for any response requiring two y axes.

    TwoAxisResponsePlots are rarely going to be used outside of subclassing. They're essentially the base for any plot
    that is set up to plot a response (peak area, mixing ratio, logged parameter) against time, but requires a second
    y axis for scaling.
    """

    def __init__(self, series1, series2, limits_y1=None, limits_y2=None, major_ticks=None, minor_ticks=None,
                 x_label_str=None, y_label_str=None, y2_label_str=None, title=None, date_format='%Y-%m-%d',
                 filepath=None, save=True, show=False,
                 color_set_y2=('#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854', '#ffd92f', '#e5c494', '#b3b3b3')):
        """
        Create the instance and define defaults.

        :param dict series1: data for the primary (left) y axis as {name: (xData, yData)}
        :param dict series2: data for the secondary (right) y axis as {name: (xData, yData)}
        :param dict limits_y1: plot limits for the primary (left) y axis;
            containing any of 'top', 'bottom', 'right', 'left'; if limits_y2 contains a right or left limit it *will*
            overwrite any top/bottom limit given by limits_y1
        :param dict limits_y2: plot limits for the secondary (right) y axis;
            containing any of 'top', 'bottom', 'right', 'left'; if limits_y2 contains a right or left limit it *will*
            overwrite any right/left limit given by limits_y1
        :param Sequence[datetime] major_ticks: major ticks for x axis
        :param Sequence[datetime] minor_ticks: minor ticks for x axis
        :param str x_label_str: string label for the x axis
        :param str y_label_str: string label for the primary (left) y axis
        :param str y2_label_str: string label for the secondary (right) y axis
        :param str title: title to be displayed on plot
        :param str date_format: C-format for date
        :param str|Path filepath: path for saving the file; otherwise saved in the current working directory
        :param boolean save: save plot as png?
        :param boolean show: show plot with figure.show()?
        :param Sequence[str] color_set_y2: abitrary-length sequence of valid Matplotlib color values; defaulted to a
            ColorBrewer set (http://colorbrewer2.org/#type=qualitative&scheme=Set2&n=8).
        :raises StopIteration: if color_set_y2 is exhausted (ie: not len(color_set_y2) >= len(series2))
        """

        super().__init__(series1, series2, limits_y1, limits_y2, major_ticks, minor_ticks,
                         x_label_str, y_label_str, y2_label_str, title, date_format,
                         filepath, save, show, color_set_y2)

    def _save_to_file(self):
        """Override _save_to_file and make the path the filename-safe names of what's plotted + _plot.png"""
        if not self.filepath:
            self._make_safe_names()
            self.filepath = f'{"_".join(self.safe_names + self.safe_names2)}_plot.png'

        super()._save_to_file()


class TwoAxisLogParameterPlot(TwoAxisResponsePlot):
    """TwoAxisLogParameterPlots are the base for plotting any set of parameters on two separate y axes."""

    def __init__(self, series1, series2, title, filepath, limits_y1=None, limits_y2=None, major_ticks=None,
                 minor_ticks=None, x_label_str=None, y1_label_str='Temperature (\xb0C)',
                 y2_label_str='Temperature (\xb0C)', date_format='%Y-%m-%d', save=True, show=False,
                 color_set_y2=('#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854', '#ffd92f', '#e5c494', '#b3b3b3')):
        """
        Create the instance and define defaults.

        :param dict series1: data for the primary (left) y axis as {name: (xData, yData)}
        :param dict series2: data for the secondary (right) y axis as {name: (xData, yData)}
        :param str title: title to be displayed on plot
        :param str|Path filepath: path for saving the file; otherwise saved in the current working directory
        :param dict limits_y1: plot limits for the primary (left) y axis;
            containing any of 'top', 'bottom', 'right', 'left'; if limits_y2 contains a right or left limit it *will*
            overwrite any top/bottom limit given by limits_y1
        :param dict limits_y2: plot limits for the secondary (right) y axis;
            containing any of 'top', 'bottom', 'right', 'left'; if limits_y2 contains a right or left limit it *will*
            overwrite any right/left limit given by limits_y1
        :param Sequence[datetime] major_ticks: major ticks for x axis
        :param Sequence[datetime] minor_ticks: minor ticks for x axis
        :param str x_label_str: string label for the x axis
        :param str y1_label_str: string label for the primary (left) y axis
        :param str y2_label_str: string label for the secondary (right) y axis
        :param str date_format: C-format for date
        :param boolean save: save plot as png?
        :param boolean show: show plot with figure.show()?
        :param Sequence[str] color_set_y2: abitrary-length sequence of valid Matplotlib color values; defaulted to a
            ColorBrewer set (http://colorbrewer2.org/#type=qualitative&scheme=Set2&n=8).
        :raises StopIteration: if color_set_y2 is exhausted (ie: not len(color_set_y2) >= len(series2))
        """

        super().__init__(series1, series2, limits_y1, limits_y2, major_ticks, minor_ticks,
                         x_label_str, y1_label_str, y2_label_str, title, date_format,
                         filepath, save, show, color_set_y2)


class LinearityPlot(Plot2D):
    """
    A basic plot for checking the linearity of x and y data.

    Default values are geared towards plotting peak area responses against sample times, but can be changed for a
    variety of purposes.
    """

    def __init__(self, y_value_name, x, y, title=None, limits=None, minor_ticks=None, major_ticks=None,
                 y_label_str='Peak Area', x_label_str='Sample Time (s)', save=False, show=False):
        """
        Create an instance with several defaults if they're not given.

        :param str y_value_name: name of the y axis data
        :param Sequence x: sequence of numeric data for the x axis
        :param Sequence y: sequence of numeric data for the y axis
        :param str title: title to be placed on plot; defaults to f'{y_value_name} Linearity Plot'
        :param dict limits: plot limits, containing any of 'top', 'bottom', 'right', 'left'
        :param Sequence minor_ticks: minor ticks for x axis
        :param Sequence major_ticks: major ticks for x axis
        :param str y_label_str: string label for the x axis
        :param str x_label_str: string label for the y axis
        :param bool save: save plot as png?
        :param bool show: show plot with figure.show()?
        """

        super().__init__()  # useless but keeps IDE quiet
        self.y_value_name = y_value_name
        self.x = x
        self.y = y
        self.minor_ticks = minor_ticks
        self.major_ticks = major_ticks
        self.x_label_str = x_label_str
        self.y_label_str = y_label_str
        self.save = save
        self.show = show

        if not title:
            title = f'{y_value_name} Linearity Plot'
        self.title = title

        if not limits:
            limits = {}
        self.limits = limits

        self.reg_formula = None

    def plot(self):
        """Perform all formatting and plot data before saving or showing plot."""
        self._get_axes()
        self._add_and_format_ticks()

        self._style_plot()

        self._plot_data()
        self._create_plot_regression()

        self._set_axes_limits()  # limits must be set after plotting for limits of None to auto-scale
        self.axis()
        self._set_legend()  # legend must be set after data is added and reg_formula is defined
        self._set_title()
        self._save_to_file()

    def _plot_data(self):
        """Scatter the x and y data without connecting."""
        self.primary_axis.scatter(self.x, self.y)

    def _create_plot_regression(self):
        """Fit a linear polynomial to the data and plot it's line. Save formula for use in legend."""
        b, m = polyfit(self.x, self.y, 1)  # fit linear equation to data
        y_regression = [m * x + b for x in self.x]  # create y data to plot regression line

        self.primary_axis.plot(self.x, y_regression, '-')  # plot regression line

        operator = '-' if b < 0 else '+'  # operator to put in formatted regression formula
        self.reg_formula = f'y={m:.2f}x {operator} {abs(b):.2f}'  # use abs(b) and operator to get proper spacing

    def _set_legend(self):
        """Set the legend to the y data's name (y_value_name) and append the regression formula"""
        self.primary_axis.legend([f'{self.y_value_name} | {self.reg_formula}'])


def zugspitze_mixing_plot(dates, compound_dict, limits=None, minor_ticks=None, major_ticks=None,
                          y_label_str='Mixing Ratio (pptv)', filename_suffix='', date_formatter_string='%Y-%m'):
    """
    Create a plot of the mixing ratios for a given set of compounds and data with optional axis limits and ticks.

    Dates can be supplied for all compounds at once by providing a Truthy dates kwarg value, or for each compound
    individually by providing a Falsy dates kwarg value and giving dates for each compound in compound_dict.

    If unspecified, limits, and ticks will be auto-determined by Matplotlib.

    :example:
    All dates supplied:
        zugspitze_mixing_plot((None, {'Ethane':[[date, date, date], [1, 2, 3]],
                                'Propane':[[date, date, date], [.5, 1, 1.5]]}))

    :example:
    Single date list supplied:
        zugspitze_mixing_plot([date, date, date], {'ethane':[None, [1, 2, 3]],
                                'propane':[None, [.5, 1, 1.5]]})

    :param list dates: list of Python datetimes; if set, this applies to all compounds.
        If None, each compound supplies its own date values
    :param dict compound_dict: dict of format {'compound_name':[dates, mrs]}
        - keys: str, the name to be plotted and put into filename
        - values: list, len(list) == 2, two parallel lists that are...
            dates: list, of Python datetimes. If None, dates come from dates input parameter (for all compounds)
            mrs: list, of [int/float/None]s; these are the mixing ratios to be plotted
    :param dict limits: optional dictionary of limits including ['top', 'bottom', 'right', 'left']
    :param list minor_ticks: list of major tick marks
    :param list major_ticks: list of minor tick marks
    :param str y_label_str: label for y-axis
    :param str filename_suffix: what, if anything to append to filename before the filetype
    :param str date_formatter_string: format string for the x-axis date labels, defaults to '%Y-%m'
    :return None: Saves plot to the working directory
    """
    register_matplotlib_converters()

    f1 = plt.figure()
    ax = f1.gca()

    if dates is None:  # dates supplied by individual compounds
        for compound, val_list in compound_dict.items():
            if val_list[0] and val_list[1]:
                assert len(val_list[0]) > 0 and len(val_list[0]) == len(
                    val_list[1]), 'Supplied dates were empty or lengths did not match'
                ax.plot(val_list[0], val_list[1], '-o')
            else:
                pass

    else:
        for compound, val_list in compound_dict.items():
            ax.plot(dates, val_list[1], '-o')

    compounds_safe = []
    for k, _ in compound_dict.items():
        # Create a filename-safe list using the given legend items
        compounds_safe.append(k.replace('/', '_')
                              .replace(' ', '_'))

    comp_list = ', '.join(compound_dict.keys())  # use real names for plot title
    fn_list = '_'.join(compounds_safe)  # use 'safe' names for filename

    if limits is not None:
        ax.set_xlim(right=limits.get('right'))
        ax.set_xlim(left=limits.get('left'))
        ax.set_ylim(top=limits.get('top'))
        ax.set_ylim(bottom=limits.get('bottom'))

    if major_ticks is not None:
        ax.set_xticks(major_ticks, minor=False)
    if minor_ticks is not None:
        ax.set_xticks(minor_ticks, minor=True)

    date_form = DateFormatter(date_formatter_string)
    ax.xaxis.set_major_formatter(date_form)

    [i.set_linewidth(2) for i in ax.spines.values()]
    ax.tick_params(axis='x', labelrotation=30)
    ax.tick_params(axis='both', which='major', size=8, width=2, labelsize=15)
    f1.set_size_inches(11.11, 7.406)

    ax.set_ylabel(y_label_str, fontsize=20)
    ax.set_title(f'Zugspitze {comp_list} Mixing Ratios', fontsize=24, y=1.02)
    ax.legend(compound_dict.keys())

    f1.subplots_adjust(bottom=.20)

    plot_name = f'{fn_list}_plot{filename_suffix}.png'
    f1.savefig(plot_name, dpi=150)
    plt.close(f1)

    return plot_name


def zugspitze_qc_plot(dates, compound_dict, limits=None, minor_ticks=None, major_ticks=None,
                      y_label_str='Mixing Ratio (pptv)', filename_suffix='', date_formatter_string='%Y-%m',
                      annotate_with=None, annotate_y=None):
    """
    Create quality-control oriented plot for a given set of compounds and data with optional axis limits and ticks.

    An offshoot of zugspitze_mixing_plot() that is designed specifically for quality control. Dates can be supplied
    for all compounds at once by providing a Truthy dates kwarg value, or for each compound individually by
    providing a Falsy dates kwarg value and giving dates for each compound in compound_dict. Annotations can be added
    for every point by supplying a list of annotations and an optional hieght at which to plot them. Additionally, a
    constant y-value can be specified and all annotations will be plotted at that y-value.

    :param list dates: list of datetimes; if set, this applies to all compounds.
        If None, each compound supplies its own date values
    :param dict compound_dict: dictionary of compound and values to plot, in the format of
        {'compound_name':[dates, mrs]}
        - keys: str, the name to be plotted and put into filename
        - values: list, len(list) == 2, two parallel lists that are...
            dates: list, of Python datetimes. If None, dates come from dates input parameter (for all compounds)
            mrs: list, of [int/float/None]s; these are the mixing ratios to be plotted
    :param dict limits: optional dictionary of limits including ['top','bottom','right','left']
    :param list minor_ticks: list of major tick marks
    :param list major_ticks: list of minor tick marks
    :param str y_label_str: label for y-axis
    :param str filename_suffix: what, if anything to append to filename before the filetype
    :param str date_formatter_string: format string for the x-axis date labels, defaults to 'yyyy-mm'
    :param list annotate_with: a list of str-able values that will be annotated onto the individual points
    :param float annotate_y: a single value to plot all annotations with; defaults to mixing ratio if not given
    :return: None
    """
    register_matplotlib_converters()

    f1 = plt.figure()
    ax = f1.gca()

    if dates is None:  # dates supplied by individual compounds
        for compound, val_list in compound_dict.items():

            if val_list[0] and val_list[1]:
                assert len(val_list[0]) > 0 and len(val_list[0]) == len(
                    val_list[1]), 'Supplied dates were empty or lengths did not match'
                ax.plot(val_list[0], val_list[1], '-o')

            else:
                pass

    else:
        for compound, val_list in compound_dict.items():
            ax.plot(dates, val_list[1], '-o')

    if len(compound_dict) is 1 and annotate_with is not None:
        # annotate if one compound plotted and annotations were provided
        compound = list(compound_dict.keys())[0]

        if not dates:
            dates = compound_dict[compound][0]

        mrs = compound_dict[compound][1]

        for num, label in enumerate(annotate_with):

            if annotate_y is not None:
                ax.annotate(str(label), (dates[num], annotate_y), rotation=80)
            else:
                if mrs[num] is not None:
                    ax.annotate(str(label), (dates[num], mrs[num]), rotation=80)

    compounds_safe = []
    for k, _ in compound_dict.items():
        """Create a filename-safe list using the given legend items"""
        compounds_safe.append(k.replace('/', '_')
                              .replace(' ', '_'))

    comp_list = ', '.join(compound_dict.keys())  # use real names for plot title
    fn_list = '_'.join(compounds_safe)  # use 'safe' names for filename

    if limits is not None:
        ax.set_xlim(right=limits.get('right'))
        ax.set_xlim(left=limits.get('left'))
        ax.set_ylim(top=limits.get('top'))
        ax.set_ylim(bottom=limits.get('bottom'))

    if major_ticks is not None:
        ax.set_xticks(major_ticks, minor=False)
    if minor_ticks is not None:
        ax.set_xticks(minor_ticks, minor=True)

    date_form = DateFormatter(date_formatter_string)
    ax.xaxis.set_major_formatter(date_form)

    [i.set_linewidth(2) for i in ax.spines.values()]
    ax.tick_params(axis='x', labelrotation=30)
    ax.tick_params(axis='both', which='major', size=8, width=2, labelsize=15)
    f1.set_size_inches(11.11, 7.406)

    ax.set_ylabel(y_label_str, fontsize=20)
    ax.set_title(f'Zugspitze {comp_list} Mixing Ratios', fontsize=24, y=1.02)
    ax.legend(compound_dict.keys())

    f1.subplots_adjust(bottom=.20)

    plot_name = f'{fn_list}_plot{filename_suffix}.png'
    f1.savefig(plot_name, dpi=150)
    plt.close(f1)

    return plot_name


def zugspitze_pa_plot(dates, compound_dict, limits=None, minor_ticks=None, major_ticks=None,
                      y_label_str='Peak Area', standard=False):
    """
    Create a plot of the peak areas for a given set of compounds and data with optional axis limits and ticks.

    Dates can be supplied for all compounds at once by providing a Truthy dates kwarg value, or for each compound
    individually by providing a Falsy dates kwarg value and giving dates for each compound in compound_dict. If
    standard is true

    If unspecified, limits, and ticks will be auto-determined by Matplotlib.

    :example:
    All dates supplied:
        zugspitze_pa_plot((None, {'Ethane':[[date, date, date], [1, 2, 3]],
                                'Propane':[[date, date, date], [.5, 1, 1.5]]}))

    :example:
    Single date list supplied:
        zugspitze_pa_plot([date, date, date], {'ethane':[None, [1, 2, 3]],
                                'propane':[None, [.5, 1, 1.5]]})

    :param list dates: list, of Python datetimes; if set, this applies to all compounds.
        If None, each compound supplies its own date values
    :param dict compound_dict: dict, {'compound_name':[dates, mrs]}
        keys: str, the name to be plotted and put into filename
        values: list, len(list) == 2, two parallel lists that are...
            dates: list of datetimes. If None, dates come from dates input parameter (for all compounds)
            mrs: list of [int/float/None]s; these are the mixing ratios to be plotted
    :param dict limits:optional dictionary of limits including ['top','bottom','right','left']
    :param list minor_ticks: of major tick marks
    :param list major_ticks: of minor tick marks
    :param str y_label_str: label for the y-axis
    :param bool standard: flag to change naming format for plots of standard peak areas instead of samples
    :return: None
    """
    register_matplotlib_converters()

    f1 = plt.figure()
    ax = f1.gca()

    if dates is None:  # dates supplied by individual compounds
        for compound, val_list in compound_dict.items():
            if val_list[0] and val_list[1]:
                assert len(val_list[0]) > 0 and len(val_list[0]) == len(
                    val_list[1]), 'Supplied dates were empty or lengths did not match'
                ax.plot(val_list[0], val_list[1], '-o')
            else:
                pass

    else:
        for compound, val_list in compound_dict.items():
            ax.plot(dates, val_list[1], '-o')

    compounds_safe = []
    for k, _ in compound_dict.items():
        """Create a filename-safe list using the given legend items"""
        compounds_safe.append(k.replace('/', '_')
                              .replace(' ', '_'))

    comp_list = ', '.join(compound_dict.keys())  # use real names for plot title
    fn_list = '_'.join(compounds_safe)  # use 'safe' names for filename

    if limits is not None:
        ax.set_xlim(right=limits.get('right'))
        ax.set_xlim(left=limits.get('left'))
        ax.set_ylim(top=limits.get('top'))
        ax.set_ylim(bottom=limits.get('bottom'))

    if major_ticks is not None:
        ax.set_xticks(major_ticks, minor=False)
    if minor_ticks is not None:
        ax.set_xticks(minor_ticks, minor=True)

    date_form = DateFormatter("%Y-%m")
    ax.xaxis.set_major_formatter(date_form)

    [i.set_linewidth(2) for i in ax.spines.values()]
    ax.tick_params(axis='x', labelrotation=30)
    ax.tick_params(axis='both', which='major', size=8, width=2, labelsize=15)
    f1.set_size_inches(11.11, 7.406)

    ax.set_ylabel(y_label_str, fontsize=20)
    if standard:
        ax.set_title(f'Zugspitze {comp_list} Standard Peak Areas', fontsize=24, y=1.02)
    else:
        ax.set_title(f'Zugspitze {comp_list} Peak Areas', fontsize=24, y=1.02)

    ax.legend(compound_dict.keys())

    f1.subplots_adjust(bottom=.20)

    if standard:
        plot_name = f'{fn_list}_plot.png'
    else:
        plot_name = f'{fn_list}_pa_plot.png'
    f1.savefig(plot_name, dpi=150)
    plt.close(f1)

    return plot_name


def zugspitze_parameter_plot(dates, param_dict, title, filename, limits=None, minor_ticks=None, major_ticks=None,
                             y_label_str='Temperature (\xb0C)'):
    """
    Create a plot of a instrument parameters.

    Dates can be supplied for all compounds at once by providing a Truthy dates kwarg value, or for each parameter
    individually by providing a Falsy dates kwarg value and giving dates for each compound in param_dict.

    :example:
    All dates supplied:
        zugspitze_parameter_plot((None, {'Temperature':[[date, date, date], [1, 2, 3]],
                                'Other Temp':[[date, date, date], [.5, 1, 1.5]]}))

    :example:
    Single date list supplied:
        zugspitze_parameter_plot([date, date, date], {'Temperature':[None, [1, 2, 3]],
                                'Other Temp':[None, [.5, 1, 1.5]]})

    :param list dates: list of datetimes; if set, this applies to all compounds.
    :param dict param_dict: dict of format {'compound_name':[dates, mrs]}
        keys: str, the name to be plotted and put into filename
        values: list, len(list) == 2, two parallel lists that are...
            dates: list, of Python datetimes. If None, dates come from dates input parameter (for all compounds)
            mrs: list, of [int/float/None]s; these are the mixing ratios to be plotted
    :param str title: title to be placed on plot
    :param str filename: filename to be saved; relative and absolute paths acceptable
    :param dict limits: optional dictionary of limits including ['top','bottom','right','left']
    :param list minor_ticks: list of major tick marks
    :param list major_ticks: list of minor tick marks
    :param str y_label_str: label for the y axis; defaults to 'Temperature (\xb0c)'
    :return None:
    """
    register_matplotlib_converters()

    f1 = plt.figure()
    ax = f1.gca()

    if dates is None:  # dates supplied by individual compounds
        for param, val_list in param_dict.items():
            if val_list[0] and val_list[1]:
                assert len(val_list[0]) > 0 and len(val_list[0]) == len(
                    val_list[1]), 'Supplied dates were empty or lengths did not match'
                ax.plot(val_list[0], val_list[1], '-o')
            else:
                pass

    else:
        for param, val_list in param_dict.items():
            ax.plot(dates, val_list[1], '-o')

    if limits is not None:
        ax.set_xlim(right=limits.get('right'))
        ax.set_xlim(left=limits.get('left'))
        ax.set_ylim(top=limits.get('top'))
        ax.set_ylim(bottom=limits.get('bottom'))

    if major_ticks is not None:
        ax.set_xticks(major_ticks, minor=False)
    if minor_ticks is not None:
        ax.set_xticks(minor_ticks, minor=True)

    date_form = DateFormatter("%Y-%m-%d")
    ax.xaxis.set_major_formatter(date_form)

    [i.set_linewidth(2) for i in ax.spines.values()]
    ax.tick_params(axis='x', labelrotation=30)
    ax.tick_params(axis='both', which='major', size=8, width=2, labelsize=15)
    f1.set_size_inches(11.11, 7.406)

    ax.set_ylabel(y_label_str, fontsize=20)
    ax.set_title(title, fontsize=24, y=1.02)
    ax.legend(param_dict.keys())

    f1.subplots_adjust(bottom=.20)

    f1.savefig(filename, dpi=150)
    plt.close(f1)


def zugspitze_twoaxis_parameter_plot(dates, param_dict1, param_dict2, title, filename, limits1=None, limits2=None,
                                     minor_ticks=None, major_ticks=None,
                                     y1_label_str='Temperature (\xb0C)',
                                     y2_label_str='Temperature (\xb0C)'):
    """
    Create a plot of a instrument parameters using two y axes.

    Dates can be supplied for all compounds at once by providing a Truthy dates kwarg value, or for each parameter
    individually by providing a Falsy dates kwarg value and giving dates for each compound in param_dict. Parameters
    for the left y axis should be provided in param_dict1, and the right y-axis in param_dict2. Limits for each axis
    can be supplied with limits1 and limits2.

    :example:
    All dates supplied:
        zugspitze_parameter_plot((None, {'Temperature':[[date, date, date], [1, 2, 3]]},
                                {'Other Temp':[[date, date, date], [.5, 1, 1.5]]}))

    :example:
    Single date list supplied:
        zugspitze_parameter_plot([date, date, date], {'Temperature':[None, [1, 2, 3]]},
                                {'Other Temp':[None, [.5, 1, 1.5]]})

    :param list dates: list of datetimes; if set, this applies to all compounds.
    :param dict param_dict1: dict of format {'param_name':[dates, param_values]} for left y-axis
    :param dict param_dict2: dict of format {'param_name':[dates, param_values]} for right y-axis
    :param str title: title to be added to plot
    :param str filename: filename to be saved; relative and absolute paths acceptable
    :param dict limits1: dict of limits for left y-axis, including any of ['top','bottom','right','left']
    :param dict limits2: dict of limits for right y-axis, including any of ['top','bottom','right','left']
    :param list minor_ticks: list of major tick marks
    :param list major_ticks: list of minor tick marks
    :param str y1_label_str: y-axis label for left y-axis
    :param str y2_label_str: y-axis label for right y-axis
    :return None:
    """
    register_matplotlib_converters()

    f1 = plt.figure()
    ax = f1.gca()
    ax2 = ax.twinx()

    if dates is None:  # dates supplied by individual compounds (for set 1)
        for param, val_list in param_dict1.items():
            if val_list[0] and val_list[1]:
                assert len(val_list[0]) > 0 and len(val_list[0]) == len(
                    val_list[1]), 'Supplied dates were empty or lengths did not match in parameter set 1.'
                ax.plot(val_list[0], val_list[1], '-o')
            else:
                pass

        for param, val_list in param_dict2.items():
            if val_list[0] and val_list[1]:
                assert len(val_list[0]) > 0 and len(val_list[0]) == len(
                    val_list[1]), 'Supplied dates were empty or lengths did not match in parameter set 2.'
                ax2.plot(val_list[0], val_list[1], '-o', color='orange')
            else:
                pass

    else:
        for param, val_list in param_dict1.items():
            ax.plot(dates, val_list[1], '-o')

        for param, val_list in param_dict2.items():
            ax2.plot(dates, val_list[1], '-o', color='orange')

    if limits1 is not None:
        ax.set_xlim(right=limits1.get('right'))
        ax.set_xlim(left=limits1.get('left'))
        ax.set_ylim(top=limits1.get('top'))
        ax.set_ylim(bottom=limits1.get('bottom'))

    if limits2 is not None:
        ax2.set_ylim(bottom=limits2.get('bottom'))
        ax2.set_ylim(top=limits2.get('top'))

    if major_ticks is not None:
        ax.set_xticks(major_ticks, minor=False)
    if minor_ticks is not None:
        ax.set_xticks(minor_ticks, minor=True)

    date_form = DateFormatter("%Y-%m-%d")
    ax.xaxis.set_major_formatter(date_form)

    [i.set_linewidth(2) for i in ax.spines.values()]
    ax.tick_params(axis='x', labelrotation=30)
    ax.tick_params(axis='both', which='major', size=8, width=2, labelsize=15)
    f1.set_size_inches(11.11, 7.406)

    ax.set_ylabel(y1_label_str, fontsize=20)
    ax2.set_ylabel(y2_label_str, fontsize=20)

    ax.set_title(title, fontsize=24, y=1.02)
    ax.legend(param_dict1.keys(), loc='upper left')
    ax2.legend(param_dict2.keys(), loc='upper right')

    f1.subplots_adjust(bottom=.20)

    f1.savefig(filename, dpi=150)
    plt.close(f1)


def zugspitze_linearity_plot(compound, sampletimes, peak_areas, limits=None, minor_ticks=None, major_ticks=None,
                             y_label_str='Peak Area'):
    """
    Create a plot of peak area responses vs. sample times with a linear fit.

    Plot sampling length over the x axis and instrument response for the given compound along the y axis. Fit a
    linear regression and plot along with the formula.

    :param str compound: name of compound values being plotted
    :param list sampletimes: list of int/floats, the sample times to plot as x values
    :param list peak_areas: list of ints/floats, the peak areas to plot as y values
    :param dict limits: dict, optional dictionary of limits including ['top','bottom','right','left']
    :param list minor_ticks: list, of major tick marks
    :param list major_ticks: list, of minor tick marks
    :param str y_label_str: string, name for y-axis label
    :return None:
    :return:
    """
    f1 = plt.figure()
    ax = f1.gca()

    ax.scatter(sampletimes, peak_areas)
    b, m = polyfit(sampletimes, peak_areas, 1)
    reg = f'y={m:.2f}x + {b:.2f}'

    ax.plot(sampletimes, (m * sampletimes + b), '-')

    if limits is not None:
        ax.set_xlim(right=limits.get('right'))
        ax.set_xlim(left=limits.get('left'))
        ax.set_ylim(top=limits.get('top'))
        ax.set_ylim(bottom=limits.get('bottom'))

    if major_ticks is not None:
        ax.set_xticks(major_ticks, minor=False)
    if minor_ticks is not None:
        ax.set_xticks(minor_ticks, minor=True)

    [i.set_linewidth(2) for i in ax.spines.values()]
    ax.tick_params(axis='x', labelrotation=30)
    ax.tick_params(axis='both', which='major', size=8, width=2, labelsize=15)
    f1.set_size_inches(11.11, 7.406)

    ax.set_xlabel('Sample Time (s)', fontsize=20)
    ax.legend([f'{compound} - {reg}'])
    ax.set_ylabel(y_label_str, fontsize=20)
    ax.set_title(f'Zugspitze {compound} Linearity Plot', fontsize=24, y=1.02)

    f1.subplots_adjust(bottom=.20)

    f1.savefig(f'{compound}_linearity_plot.jpeg', dpi=150)
    plt.close(f1)