"""
Three sets of (EMPA SX3555, CC464566) were run to quantify the EMPA VOCs and vice-versa.

Blanks were run in a set of three consecutive blanks for some reason. A single 1250s blank was also run in the middle of
the sequence to blank-subtract the NIST vocs. This method is not particularly reliable as the blanks are in sequence.
"""
__package__ = 'Z'

from datetime import datetime

from settings import CORE_DIR, DB_NAME
from IO.db import connect_to_db, GcRun, Integration, Standard, SampleQuant
from processing import blank_subtract
from reporting import compile_quant_report

engine, session = connect_to_db(DB_NAME, CORE_DIR)

blank_1250 = (session.query(GcRun)
              .join(Integration, Integration.run_id == GcRun.id)
              .filter(Integration.filename == '2019_03_19_Blank1250_01.D')
              .one())

blank_2500_set = (session.query(GcRun)
                  .join(Integration, Integration.run_id == GcRun.id)
                  .filter(GcRun.date > datetime(2019, 3, 19), GcRun.date < datetime(2019, 3, 20))
                  .filter(Integration.filename.like('%Blank2500%.D'))
                  .order_by(Integration.date)
                  .all())

cc464566_set = (session.query(GcRun)
                .join(Integration, Integration.run_id == GcRun.id)
                .filter(GcRun.date > datetime(2019, 3, 19), GcRun.date < datetime(2019, 3, 20))
                .filter(Integration.filename.like('%CC464566%.D'))
                .order_by(Integration.date)
                .all())

sx3555_set = (session.query(GcRun)
              .join(Integration, Integration.run_id == GcRun.id)
              .filter(GcRun.date > datetime(2019, 3, 19), GcRun.date < datetime(2019, 3, 20))
              .filter(Integration.filename.like('%SX3555%.D'))
              .order_by(Integration.date)
              .all())

vocs = session.query(Standard).filter(Standard.name == 'vocs').one()
vocs = [q.name for q in vocs.quantifications]


cc464566_certification = session.query(Standard).filter(Standard.name == 'cc464566').one()

sx3555_certification = session.query(Standard).filter(Standard.name == 'sx3555').one()

# quantify VOCs in SX3555 with CC464566
vocs_in_sx3555 = []

for blank_2500, cc464566, sx3555 in zip(blank_2500_set, cc464566_set, sx3555_set):

    cc464566 = blank_subtract(cc464566, vocs, session, blank=blank_1250)
    sx3555 = blank_subtract(sx3555, vocs, session, blank=blank_2500)

    # VOC standard CC464566 is 1000s sample, needs 1000s blank
    voc_quant = SampleQuant(sx3555, cc464566, blank_2500, cc464566_certification, standard_blank=blank_1250)
    voc_quant.quantify()

    vocs_in_sx3555.append(voc_quant)

compile_quant_report(vocs_in_sx3555, 'SX3555', 'CC464566', sx3555_certification.quantifications,
                     date=datetime(2019, 3, 19))
