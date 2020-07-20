import statistics as s

from settings import CORE_DIR
from IO.db import DBConnection, ambient_filters
from IO.db.utils import get_standard_quants
from reporting.reports import abstract_query
from IO.db.models import Compound, GcRun
from plotting.plots import TwoAxisResponsePlot

SAVE_DIR = CORE_DIR / 'analyses/blank_plots/plots'

with DBConnection() as session:
    compounds = get_standard_quants('quantlist', string=True, set_=False, session=session)

    for compound in compounds:
        ambients = abstract_query((GcRun.date, Compound.mr), filters=ambient_filters + [Compound.name == compound], order=GcRun.date)
        blanks = abstract_query((GcRun.date, Compound.mr), filters=[GcRun.type == 0, Compound.filtered == False, Compound.name == compound],
                                order=GcRun.date)

        ambient_dates = [a.date for a in ambients]
        ambient_mrs = [a.mr for a in ambients]

        blank_dates = [b.date for b in blanks]
        blank_mrs = [b.mr for b in blanks]

        existing_blanks = [mr for mr in blank_mrs if mr is not None]

        if existing_blanks:
            blank_plot_limit = s.mean(existing_blanks) * 4
        else:
            blank_plot_limit = None

        p = TwoAxisResponsePlot(
            {compound + ' Ambient': (ambient_dates, ambient_mrs)},
            {compound + ' Blank': (blank_dates, blank_mrs)},
            limits_y1={
                'bottom': 0
            },
            limits_y2={
                'bottom': 0,
                'top': blank_plot_limit
            },
            title=f'{compound} Ambients and Blanks',
            y_label_str='Ambient MR (pptv)',
            y2_label_str='Blank MR (pptv)',
            show=False,
            save=True,
            filepath=SAVE_DIR / f'{compound}_blanks.png'
        )

        p.plot()
