"""
A set of CC412022, CC416168 were run back to back without blanks on 2019-11-12.

Rough quantification is done by the below.
"""
__package__ = 'Z'

from datetime import datetime

from settings import CORE_DIR, DB_NAME
from IO.db import connect_to_db, GcRun, Integration, Standard, SampleQuant
from processing import blank_subtract
from reporting import compile_quant_report

engine, session = connect_to_db(DB_NAME, CORE_DIR)

standard_to_quantify_with = session.query(Standard).filter(Standard.name == 'cc416168').one_or_none()
# get standard cert values for the quantifier
certified_values_of_sample = (session.query(Standard)
                              .filter(Standard.name == 'cc412022_noaa_provided')
                              .one().quantifications)
# get standard cert values for the sample being quantified

vocs = session.query(Standard).filter(Standard.name == 'vocs').one_or_none()
vocs = [q.name for q in vocs.quantifications]

samples = (session.query(GcRun).join(Integration, Integration.run_id == GcRun.id)
           .filter(GcRun.date > datetime(2019, 11, 12), GcRun.date < datetime(2019, 11, 13))
           .filter(Integration.filename.like('%CC412022___.D'))
           .order_by(GcRun.date)
           .all())

standards = (session.query(GcRun).join(Integration, Integration.run_id == GcRun.id)
             .filter(GcRun.date > datetime(2019, 11, 12), GcRun.date < datetime(2019, 11, 13))
             .filter(Integration.filename.like('%CC416168___.D'))
             .order_by(GcRun.date)
             .all())
quants = []
for sample, standard in zip(samples, standards):
    blank_subtract(sample, vocs, session, blank=None, force_no_blank=True)
    blank_subtract(standard, vocs, session, blank=None, force_no_blank=True)

    quant = SampleQuant(sample, standard, None, standard_to_quantify_with)
    quant.quantify()

    quants.append(quant)

compile_quant_report(quants, 'CC412022', 'CC416168', certified_values_of_sample, date=datetime(2019, 11, 12))
