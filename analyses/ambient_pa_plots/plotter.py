"""
We're still seeing issues in the response for CFC-11 and CFC-12, which is decreasing at an unexpectedly high rate.

This plots:
 1) The raw peak areas for both compounds in separate plots, for both the standards and ambient samples
 2) The ratio between the standard and ambient samples (s / a)

"""
from datetime import datetime

from plotting import PeakAreaPlot, LinearityPlot
from IO.db import DBConnection, GcRun, Compound, ambient_filters

for compound in ('CFC-11', 'CFC-12'):

    with DBConnection() as session:
        results = session.query(GcRun).join(Compound, GcRun.id == Compound.run_id)

        for f in ambient_filters:
            results = results.filter(f)

        results = results.all()

        dates = []
        ambient_pas = []
        standard_pas = []
        for r in results:
            if r.compound.get(compound) is None:
                continue

            if r.working_std is not None:
                s_integ = r.working_std.compound.get(compound)

                if s_integ is not None:
                    standard_pas.append(s_integ.pa)
                else:
                    standard_pas.append(None)
            else:
                standard_pas.append(None)

            dates.append(r.date)
            ambient_pas.append(r.compound[compound].pa)

    standard_ambient_ratios = []

    for s, a in zip(standard_pas, ambient_pas):
        if s is not None and a:
            standard_ambient_ratios.append(s / a)
        else:
            standard_ambient_ratios.append(None)

    #  Plot the standard / ambient peak area ratio over time
    PeakAreaPlot(
        {
            f'{compound} Standard Ratio': (dates, standard_ambient_ratios),
         },
        title=f'{compound} Standard / Ambient PA Ratio',
        y_label_str='Standard / Ambient PA Ratio',
        show=False,
        save=True,
        filepath=f'ratio_plots/{compound}_ratio.png'
    ).plot()

    #  Plot the raw standard and ambient peak areas over time for sanity
    PeakAreaPlot(
        {
            f'{compound} Standard PA': (dates, standard_pas),
            f'{compound} Ambient PA': (dates, ambient_pas),
        },
        title=f'{compound} Standard and Ambient PAs',
        show=False,
        save=True,
        filepath=f'ratio_plots/{compound}_peak_areas.png'
    ).plot()

    recent_data = {
        'dates': [],
        'standard_pas': [],
        'ambient_pas': [],
        'ratios': []
    }

    first_date = datetime(2020, 1, 1, 0, 0, 0)
    for date, s, a, r in zip(dates, standard_pas, ambient_pas, standard_ambient_ratios):
        if date >= first_date:
            recent_data['dates'].append((date - first_date).total_seconds() / (3600 * 24))
            recent_data['standard_pas'].append(s)
            recent_data['ambient_pas'].append(a)
            recent_data['ratios'].append(r)

    LinearityPlot(
        f'{compound} (Standard / Ambient) Peak Ratio',
        recent_data['dates'],
        recent_data['ratios'],
        x_label_str='Days since 2020-1-1',
        y_label_str=f'(Standard / Ambient) Peak Ratio',
        show=False,
        save=True,
        format_spec='.6f',
        filepath=f'ratio_plots/{compound}_ratio_linearity.png'
    ).plot()
