"""
A sequence of ambients and standards was run to investigate the stability of the system with repeated runs.

The sequence was(Ambient, CC416168) x4, Blank2500
"""
__package__ = 'Z'

from datetime import datetime

import pandas as pd

from settings import CORE_DIR, DB_NAME
from IO.db import connect_to_db, GcRun, Integration, Standard, SampleQuant
from processing import blank_subtract
from reporting import get_df_with_filters, write_df_to_excel

engine, session = connect_to_db(DB_NAME, CORE_DIR)

standard_to_quantify_with = session.query(Standard).filter(Standard.name == 'cc416168').one_or_none()
vocs = session.query(Standard).filter(Standard.name == 'vocs').one_or_none()
vocs = [q.name for q in vocs.quantifications]

# get standard cert values for the quantifier

standard_runs = (session.query(GcRun).join(Integration, Integration.run_id == GcRun.id)
                 .filter(GcRun.date > datetime(2019, 11, 11, 16),
                         GcRun.date < datetime(2019, 11, 12, 6))
                 .filter(Integration.filename.like('%CC416168.D'))
                 .order_by(GcRun.date)
                 .all())

ambient_runs = (session.query(GcRun).join(Integration, Integration.run_id == GcRun.id)
                .filter(GcRun.date > datetime(2019, 11, 11, 16),
                        GcRun.date < datetime(2019, 11, 12, 6))
                .filter(Integration.filename.like('%Ambient.D'))
                .order_by(GcRun.date)
                .all())

blank_run = (session.query(GcRun).join(Integration, Integration.run_id == GcRun.id)
             .filter(GcRun.date > datetime(2019, 11, 12, 3),
                     GcRun.date < datetime(2019, 11, 12, 6))
             .filter(Integration.filename.like('%Blank2500.D'))
             .one_or_none())

assert len(standard_runs) == len(ambient_runs), "Unequal number of standard and ambient runs found!"

ambients = []
standards = []
# last_standard = None

for ambient_run, standard_run in zip(ambient_runs, standard_runs):
    blank_subtract(ambient_run, vocs, session, blank=blank_run)
    blank_subtract(standard_run, vocs, session, blank=blank_run)

    quant = SampleQuant(ambient_run, standard_run, blank_run, standard_to_quantify_with)
    quant.quantify()

    #
    # if last_standard:
    #     alt_quant = SampleQuant(ambient_run, last_standard, blank_run, standard_to_quantify_with)
    #     alt_quant.quantify()
    #
    # last_standard = standard_run

    ambient_run = session.merge(ambient_run)  # merge the quantified run, then add to list
    standard_run = session.merge(standard_run)
    ambients.append(ambient_run)
    standards.append(standard_run)

session.commit()  # save to DB so quantified values are kept for later use

# get ids of all the runs just quantified
ambient_run_ids = [run.id for run in ambients]
standard_run_ids = [run.id for run in standards]

ambient_id_filter = GcRun.id.in_(ambient_run_ids)
standard_id_filter = GcRun.id.in_(standard_run_ids)

# retrieve a dataframe of the ambient mixing ratios using the ids
ambient_df = get_df_with_filters(use_mrs=True, filters=[ambient_id_filter])

# retrieve a dataframe of the standard peak areas mixing ratios using the ids
standard_df = get_df_with_filters(use_mrs=False, filters=[standard_id_filter])

filename_add = 'ambient_cc416168_repeats_x4'
header = ['date'] + ambient_df.columns.tolist()

df = pd.concat([ambient_df, standard_df])

write_df_to_excel(df, header, filename_add, bold_row_0=True, bold_col_0=True)
