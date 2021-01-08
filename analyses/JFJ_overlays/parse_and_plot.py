import json
from datetime import datetime

from finalization.runtime import get_all_final_data_as_dict
from processing.constants import EBAS_REPORTING_COMPOUNDS
from settings import CORE_DIR, JSON_PUBLIC_DIR
from plotting import create_monthly_ticks, MixingRatioPlot

from analyses.JFJ_overlays.parsers import read_jfj_all_compounds_file, read_jfj_cfc_file

FULL_START_DATE = datetime(2013, 1, 1)
NEW_START_DATE = datetime(2018, 1, 1)
END_DATE = datetime(2021, 1, 1)


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


def plot_jfj_overlays(jfj_data, compounds, full_plot_dir, new_plot_dir, full=True, new=True):
    PLOT_INFO = JSON_PUBLIC_DIR / 'zug_long_plot_info.json'

    if full and not full_plot_dir.exists():
        full_plot_dir.mkdir()

    if new and not new_plot_dir.exists():
        new_plot_dir.mkdir()

    with PLOT_INFO.open('r') as file:
        compound_limits = json.loads(file.read())

    final_clean_data, _ = get_all_final_data_as_dict()

    if full:
        months = (END_DATE - FULL_START_DATE).days // 30  # dirty int division that probably works
        date_limits, major_ticks, minor_ticks = create_monthly_ticks(months, days_per_minor=0, start=FULL_START_DATE)

        major_ticks = major_ticks[::12]

        for compound in compounds:
            if compound not in compound_limits:
                print(f"Compound (full) {compound} not plotted.")
                continue

            jfj_compound = [d if d else None for d in jfj_data.get(compound, [])]  # clean lists to None if 0/None/NaN etc
            jfj_dates = jfj_data['date'] if jfj_compound else []

            MixingRatioPlot(
                {compound: final_clean_data[compound], 'JFJ ' + compound: [jfj_dates, jfj_compound]},
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

        for compound in compounds:
            if compound not in compound_limits:
                print(f"Compound (new) {compound} not plotted.")
                continue

            jfj_compound = [d if d else None for d in jfj_data.get(compound, [])]  # clean lists to None if 0/None/NaN etc
            jfj_dates = jfj_data['date'] if jfj_compound else []

            MixingRatioPlot(
                {compound: final_clean_data[compound], 'JFJ ' + compound: [jfj_dates, jfj_compound]},
                title=f'Zugspitze and JFJ {compound} Plot',
                limits={**date_limits, **compound_limits[compound]},
                major_ticks=major_ticks,
                minor_ticks=minor_ticks,
                filepath=NEW_PLOTDIR / f'{compound}_plot.png'
            ).plot()


if __name__ == '__main__':

    file_choice = input(
        '''Pick file to read:\n\t1: JFJ.txt -- all compounds up to 2020-9-30\n
        \t2: JFJ_CFC_Helmig_2020.txt -- CFC-11 and 12 until 2021\n'''
    )

    filename = 'JFJ.txt' if file_choice == "1" else 'JFJ_CFC_Helmig_2020.txt'
    reader = read_jfj_all_compounds_file if file_choice == "1" else read_jfj_cfc_file
    compounds = EBAS_REPORTING_COMPOUNDS if file_choice == "1" else ('CFC-11', 'CFC-12')

    unfiltered_jfj_data = reader(filename, clean=True)
    filtered_jfj_data = reader(filename, clean=False)

    FULL_PLOTDIR = CORE_DIR / 'analyses/JFJ_overlays/plots/unfiltered_JFJ/full'
    NEW_PLOTDIR = CORE_DIR / 'analyses/JFJ_overlays/plots/unfiltered_JFJ/new'

    plot_jfj_overlays(unfiltered_jfj_data, compounds=compounds, full_plot_dir=FULL_PLOTDIR, new_plot_dir=NEW_PLOTDIR, full=True, new=True,)

    FULL_PLOTDIR = CORE_DIR / 'analyses/JFJ_overlays/plots/filtered_JFJ/full'
    NEW_PLOTDIR = CORE_DIR / 'analyses/JFJ_overlays/plots/filtered_JFJ/new'
    plot_jfj_overlays(filtered_jfj_data, compounds=compounds, full_plot_dir=FULL_PLOTDIR, new_plot_dir=NEW_PLOTDIR, full=True, new=True,)
