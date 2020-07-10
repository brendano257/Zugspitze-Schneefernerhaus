"""
A sequence of Zero-Air, NIST VOC Standard, TrapBlank, NIST VOC Standard, Zero-Air were run to test the residuals left on
the trap. The first Zero-air is technically a part of the night runs, but is included anyway.
"""
from settings import CORE_DIR, DB_NAME
from IO.db import connect_to_db, GcRun, Standard, Integration
from reporting import get_df_with_filters, write_df_to_excel, abstract_query
from processing.constants import ALL_COMPOUNDS

engine, session = connect_to_db(DB_NAME, CORE_DIR)

standard_to_quantify_with = session.query(Standard).filter(Standard.name == 'cc416168').one_or_none()
vocs = session.query(Standard).filter(Standard.name == 'vocs').one_or_none()
vocs = [q.name for q in vocs.quantifications]

samples = {"2019_12_24a_02.D", "2019_12_24_Blank2500.D", "2019_12_24_CC464566_02.D", "2019_12_24_Trap600.D",
           "2019_12_24_CC464566_01.D", "2019_12_24_04.D"}

filters = (GcRun.integration.has(Integration.filename.in_(samples)),)

runs = abstract_query((GcRun,), filters, GcRun.date)

for run in runs:
    run.blank_subtract(session=session, blank=None, compounds_to_subtract=ALL_COMPOUNDS)
    # force "blank subtraction" with no values; this means all samples are now "as is" when they were integrated

session.commit()

session.close()
engine.dispose()

df = get_df_with_filters(use_mrs=False, filters=filters, compounds=ALL_COMPOUNDS)
head = [''] + df.columns.tolist()

write_df_to_excel(df, filename_end='NIST_blank_test', header=head, bold_col_0=True, bold_row_0=True)
