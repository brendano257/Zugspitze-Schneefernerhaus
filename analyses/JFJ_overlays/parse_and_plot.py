import json
from collections import namedtuple
from datetime import datetime

from finalization.finalization import get_all_final_data_as_dict
from processing.constants import ALL_COMPOUNDS
from settings import CORE_DIR, JSON_PUBLIC_DIR
from plotting import create_monthly_ticks, MixingRatioPlot

FULL_START_DATE = datetime(2013, 1, 1)
NEW_START_DATE = datetime(2018, 1, 1)
END_DATE = datetime(2021, 1, 1)

COMPOUND_NAME_LOOKUP = {
    'methyl_chloride': 'CH3Cl',
    'methyl_bromide': 'CH3Br',
    'chloroform': 'CHCl3',
    'perchloroethylene': 'PCE',
    'methyl_chloroform': 'CH3CCl3'
}


def clean_flagged_data(conv, field, clean=False):
    """
    Use the given converter on field, and except ValueErrors as returning None
    ValueErrors will occur when values are flagged, eg conv('12.11P') will fail and return None for that value
    :param conv:
    :param field:
    :param clean: if False, don't strip data field on ValueError, just return None; otherwise strip and return float
    :return:
    """
    try:
        return conv(field.strip())
    except ValueError:
        return None if not clean else conv(field.strip().rstrip('P'))


def read_jfj_file(filepath, clean=False):
    converters = [lambda x, f=func: f(x) for func in
                  (float, int, int, int, int, int, *([float] * 40))]

    with open(filepath, 'r') as file:
        t = namedtuple('data', [fieldname.strip().replace('-', '_') for fieldname in next(file).split()])

        data = [
            t(*[clean_flagged_data(conv, field, clean) for field, conv in zip(line.split(), converters)])
            for line in file
        ]

    jfj_data = dict.fromkeys(['date'] + list(ALL_COMPOUNDS), None)

    for k in jfj_data:
        jfj_data[k] = []

    for d in data:
        jfj_data['date'].append(datetime(d.YYYY, d.MM, d.DD, d.hh, d.min, 0))

        for compound in ALL_COMPOUNDS:
            # get the name if there's an alias, otherwise use the name
            compound_looked_up = COMPOUND_NAME_LOOKUP.get(compound, compound)
            datum = getattr(d, compound_looked_up.replace('-', '_'), None)
            jfj_data[compound].append(datum)

    empty = []
    for k, v in jfj_data.items():
        if not any(v):
            empty.append(k)

    for k in empty:
        del jfj_data[k]

    return jfj_data


def plot_jfj_overlays(jfj_data, full_plot_dir, new_plot_dir, full=True, new=True):
    PLOT_INFO = JSON_PUBLIC_DIR / 'zug_long_plot_info.json'

    if full and not full_plot_dir.exists():
        full_plot_dir.mkdir()

    if new and not new_plot_dir.exists():
        new_plot_dir.mkdir()

    with PLOT_INFO.open('r') as file:
        compound_limits = json.loads(file.read())

    final_data = get_all_final_data_as_dict()

    if full:
        months = (END_DATE - FULL_START_DATE).days // 30  # dirty int division that probably works
        date_limits, major_ticks, minor_ticks = create_monthly_ticks(months, days_per_minor=0, start=FULL_START_DATE)

        major_ticks = major_ticks[::12]

        for compound in ALL_COMPOUNDS:
            if compound not in compound_limits:
                print(f"Compound (full) {compound} not plotted.")
                continue

            jfj_compound = [d if d else None for d in jfj_data.get(compound, [])]  # clean lists to None if 0/None/NaN etc
            jfj_dates = jfj_data['date'] if jfj_compound else []

            MixingRatioPlot(
                {compound: final_data[compound], 'JFJ ' + compound: [jfj_dates, jfj_compound]},
                title=f'Zugspitze and JFJ {compound} Plot',
                limits={**date_limits, **compound_limits[compound]},
                major_ticks=major_ticks,
                minor_ticks=minor_ticks,
                filepath=FULL_PLOTDIR / f'{compound}_plot.png'
            ).plot()

    if new:
        months = (END_DATE - NEW_START_DATE).days // 30  # dirty int division that probably works
        date_limits, major_ticks, minor_ticks = create_monthly_ticks(months, days_per_minor=0, start=NEW_START_DATE)

        major_ticks = major_ticks[::4]

        for compound in ALL_COMPOUNDS:
            if compound not in compound_limits:
                print(f"Compound (new) {compound} not plotted.")
                continue

            jfj_compound = [d if d else None for d in jfj_data.get(compound, [])]  # clean lists to None if 0/None/NaN etc
            jfj_dates = jfj_data['date'] if jfj_compound else []

            MixingRatioPlot(
                {compound: final_data[compound], 'JFJ ' + compound: [jfj_dates, jfj_compound]},
                title=f'Zugspitze and JFJ {compound} Plot',
                limits={**date_limits, **compound_limits[compound]},
                major_ticks=major_ticks,
                minor_ticks=minor_ticks,
                filepath=NEW_PLOTDIR / f'{compound}_plot.png'
            ).plot()


if __name__ == '__main__':

    unfiltered_jfj_data = read_jfj_file('JFJ.txt', clean=True)
    filtered_jfj_data = read_jfj_file('JFJ.txt', clean=False)

    FULL_PLOTDIR = CORE_DIR / 'analyses/JFJ_overlays/plots/unfiltered_JFJ/full'
    NEW_PLOTDIR = CORE_DIR / 'analyses/JFJ_overlays/plots/unfiltered_JFJ/new'

    plot_jfj_overlays(unfiltered_jfj_data, full_plot_dir=FULL_PLOTDIR, new_plot_dir=NEW_PLOTDIR, full=True, new=True,)

    FULL_PLOTDIR = CORE_DIR / 'analyses/JFJ_overlays/plots/filtered_JFJ/full'
    NEW_PLOTDIR = CORE_DIR / 'analyses/JFJ_overlays/plots/filtered_JFJ/new'
    plot_jfj_overlays(filtered_jfj_data, full_plot_dir=FULL_PLOTDIR, new_plot_dir=NEW_PLOTDIR, full=True, new=True,)
