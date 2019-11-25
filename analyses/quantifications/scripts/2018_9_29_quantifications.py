"""
This quantifies the new EMPA cylinder (SX3555) by the current working standard (CC416168) three times and vice-versa.

Three sets of runs were conducted on 2019-09-29 as (SX3555, CC416168, Blank) x 3.
"""
__package__ = 'Z'

from datetime import datetime

from settings import CORE_DIR, DB_NAME
from IO.db import connect_to_db, GcRun, Integration, SampleQuant, Standard
from processing import blank_subtract
from reporting import compile_quant_report

engine, session = connect_to_db(DB_NAME, CORE_DIR)

blank_2500_set = (session.query(GcRun)
                  .join(Integration, Integration.run_id == GcRun.id)
                  .filter(GcRun.date > datetime(2018, 9, 29), GcRun.date < datetime(2018, 9, 30))
                  .filter(Integration.filename.like('%Blank2500%.D'))
                  .order_by(Integration.date)
                  .all())

cc416168_set = (session.query(GcRun)
                .join(Integration, Integration.run_id == GcRun.id)
                .filter(GcRun.date > datetime(2018, 9, 29), GcRun.date < datetime(2018, 9, 30))
                .filter(Integration.filename.like('%CC416168%.D'))
                .order_by(Integration.date)
                .all())

sx3555_set = (session.query(GcRun)
              .join(Integration, Integration.run_id == GcRun.id)
              .filter(GcRun.date > datetime(2018, 9, 29), GcRun.date < datetime(2018, 9, 30))
              .filter(Integration.filename.like('%SX3555%.D'))
              .order_by(Integration.date)
              .all())

vocs = session.query(Standard).filter(Standard.name == 'vocs').one()
vocs = [q.name for q in vocs.quantifications]

cc416168_certification = session.query(Standard).filter(Standard.name == 'cc416168').one()

sx3555_certification = session.query(Standard).filter(Standard.name == 'sx3555').one()

# quantify all compounds in SX3555 with CC416168
all_in_sx3555 = []

for cc416168, sx3555, blank_2500 in zip(cc416168_set, sx3555_set, blank_2500_set):
    cc416168 = blank_subtract(cc416168, vocs, session, blank=blank_2500)
    sx3555 = blank_subtract(sx3555, vocs, session, blank=blank_2500)

    # CC416168 defaults to using the same blank as the sample -- OK here
    all_quant = SampleQuant(sx3555, cc416168, blank_2500, cc416168_certification)
    all_quant.quantify()

    all_in_sx3555.append(all_quant)

compile_quant_report(all_in_sx3555, 'SX3555', 'CC416168', sx3555_certification.quantifications,
                     date=datetime(2018, 9, 29))


# quantify all compounds in CC416168 with SX3555
all_in_cc416168 = []

for cc416168, sx3555, blank_2500 in zip(cc416168_set, sx3555_set, blank_2500_set):
    cc416168 = blank_subtract(cc416168, vocs, session, blank=blank_2500)
    sx3555 = blank_subtract(sx3555, vocs, session, blank=blank_2500)

    # SX3555 defaults to using the same blank as the sample -- OK here
    all_quant = SampleQuant(cc416168, sx3555, blank_2500, sx3555_certification)
    all_quant.quantify()

    all_in_cc416168.append(all_quant)

compile_quant_report(all_in_cc416168, 'CC416168', 'SX3555', cc416168_certification.quantifications,
                     date=datetime(2018, 9, 29))
