from pathlib import Path
from datetime import datetime

from abc import ABC, abstractmethod
from collections.abc import Sequence

import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from numpy.polynomial.polynomial import polyfit
from pandas.plotting import register_matplotlib_converters

__all__ = ['Plot2D', 'TimeSeries', 'ResponsePlot', 'AnnotatedResponsePlot', 'MixingRatioPlot', 'PeakAreaPlot',
           'StandardPeakAreaPlot', 'LogParameterPlot', 'TwoAxisTimeSeries', 'TwoAxisResponsePlot',
           'TwoAxisLogParameterPlot', 'LinearityPlot']


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
            axis.set_xlim(**{k: v for k, v in limits.items() if k in {'right', 'left'}})
            axis.set_ylim(**{k: v for k, v in limits.items() if k in {'top', 'bottom'}})

    def _label_axes(self):
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
        self._label_axes()
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
            title = f'Zugspitze {", ".join(series.keys())}'

            if type_:
                title = title + f' {type_}'

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
    PeakAreaPlots are the base for any plot of a compound's peak areas.
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


class AnnotatedResponsePlot(ResponsePlot):

    def __init__(self, series, limits=None, major_ticks=None, minor_ticks=None, x_label_str=None, y_label_str=None,
                 type_=None, title=None, date_format='%Y-%m-%d', filepath=None, save=True, show=False, annotations=None,
                 annotate_y=None):
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
        :param Sequence annotations: Sequence of any stringable data to annotate with.
        :param annotate_y: Single value on the y-scale to plot all annotations at. Otherwise plotted at the data point.
        :raises ValueError: if annotations is not of a matching length to first set of data in series
        """

        super().__init__(series, limits, major_ticks, minor_ticks, x_label_str, y_label_str, type_, title, date_format,
                         filepath, save, show)

        self.annotations = annotations
        self.annotate_y = annotate_y

    def _plot_all_series(self):
        """
        Call the super method to plot all data, then annotate using provided data.

        Does nothing except call the super _plot_all_series if no annotations were provided.

        :return:
        """
        super()._plot_all_series()

        if self.annotations:  # essentially pass if no annotations provided
            dates, ydata = next(iter(self.series.values()))  # get data of the plotted series

            if len(self.annotations) != len(dates):
                msg = 'Annotations sequence must be of same length as first set of provided data'
                raise ValueError(msg)

            if not self.annotate_y:
                self.annotate_y = ydata  # use ydata of the series if no set height was given
            elif self.annotate_y:
                y = self.annotate_y  # if a single value was given, create a list of them for plotting
                self.annotate_y = [y for _ in range(len(dates))]

            for i, anno in enumerate(self.annotations):  # add all annotations
                self.primary_axis.annotate(str(anno), (dates[i], self.annotate_y[i]), rotation=80)


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
        self.safe_names2 = []

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

    def _label_axes(self):
        """Set labels for both axes."""
        super()._label_axes()
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
                 y_label_str='Peak Area', x_label_str='Sample Time (s)', save=False, show=False, filepath=None,
                 format_spec='.2f'):
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

        self.save = save
        self.show = show

        if not title:
            title = f'{y_value_name} Linearity Plot'
        self.title = title

        if not limits:
            limits = {}
        self.limits = limits

        self.reg_formula = None
        self.filepath = filepath
        self.format_spec = format_spec

        self.x_label_str = x_label_str
        self.y_label_str = y_label_str

    def plot(self):
        """Perform all formatting and plot data before saving or showing plot."""
        self._get_axes()
        self._add_and_format_ticks()

        self._style_plot()

        self._plot_data()
        self._create_plot_regression()

        self._set_axes_limits()  # limits must be set after plotting for limits of None to auto-scale
        self._label_axes()
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
        # use abs(b) and operator to get proper spacing
        self.reg_formula = f'y={format(m, self.format_spec)}x {operator} {format(abs(b), self.format_spec)}'

    def _set_legend(self):
        """Set the legend to the y data's name (y_value_name) and append the regression formula"""
        self.primary_axis.legend([f'{self.y_value_name} | {self.reg_formula}'])


def test_annotated_plots():
    import datetime as dt
    from datetime import datetime
    from random import randint

    now = datetime.now()

    xdata = [now + dt.timedelta(days=x) for x in range(45)]
    ydata = [1000 + randint(-1000, 1000) for _ in range(45)]

    p1 = AnnotatedResponsePlot({'Data': (xdata, ydata)}, annotate_y=None, annotations=ydata, save=False, show=True)
    p1.plot()

    p2 = AnnotatedResponsePlot({'Data': (xdata, ydata)}, annotate_y=1000, annotations=ydata, save=False, show=True)
    p2.plot()

    p3 = AnnotatedResponsePlot({'Data': (xdata, ydata)}, annotate_y=None, annotations=ydata[:-3], save=False, show=True)

    try:
        p3.plot()
    except ValueError as e:
        print(f"ValueError expected and was caught: {e.args}")


if __name__ == '__main__':
    test_annotated_plots()
