import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from numpy.polynomial.polynomial import polyfit
from pandas.plotting import register_matplotlib_converters

# TODO: Room to simplify with classes/subclasses? Plenty of duplicate code.


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