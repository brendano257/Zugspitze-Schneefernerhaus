"""
This script quantifies SX3556 using the new working standard (CC416168) and CC464566.

Sequences of standards were run three times on 2018-05-16. These were (CC416168, CC464566, Blank, SX3556) x 3.
"""
__package__ = 'Z'

from datetime import datetime

from settings import CORE_DIR, DB_NAME
from IO.db import connect_to_db, GcRun, Integration, SampleQuant, Standard
from processing import blank_subtract
from reporting import compile_quant_report

engine, session = connect_to_db(DB_NAME, CORE_DIR)

blank_2500 = (session.query(GcRun)
              .join(Integration, Integration.run_id == GcRun.id)
              .filter(Integration.filename == '2018_05_16_04.D')
              .one())

blank_1000_set = (session.query(GcRun)
                  .join(Integration, Integration.run_id == GcRun.id)
                  .filter(GcRun.date > datetime(2018,5,16), GcRun.date < datetime(2018, 5, 17))
                  .filter(Integration.filename.like('%Blank1000%.D'))
                  .order_by(Integration.date)
                  .all())

cc416168_set = (session.query(GcRun)
                .join(Integration, Integration.run_id == GcRun.id)
                .filter(GcRun.date > datetime(2018,5,16), GcRun.date < datetime(2018, 5, 17))
                .filter(Integration.filename.like('%CC416168%.D'))
                .order_by(Integration.date)
                .all())

cc464566_set = (session.query(GcRun)
                .join(Integration, Integration.run_id == GcRun.id)
                .filter(GcRun.date > datetime(2018,5,16), GcRun.date < datetime(2018, 5, 17))
                .filter(Integration.filename.like('%CC464566%.D'))
                .order_by(Integration.date)
                .all())

sx3556_set = (session.query(GcRun)
              .join(Integration, Integration.run_id == GcRun.id)
              .filter(GcRun.date > datetime(2018,5,16), GcRun.date < datetime(2018, 5, 17))
              .filter(Integration.filename.like('%SX3556%.D'))
              .order_by(Integration.date)
              .all())

vocs = session.query(Standard).filter(Standard.name == 'vocs').one()
vocs = [q.name for q in vocs.quantifications]

cc416168_certification = session.query(Standard).filter(Standard.name == 'cc416168').one()

cc464566_certification = session.query(Standard).filter(Standard.name == 'cc464566').one()

sx3556_certification = session.query(Standard).filter(Standard.name == 'sx3556').one()

# quantify VOCs in SX3556 with CC464566, and quantify all in SX3556 with CC416168
vocs_in_sx3556 = []
all_in_sx3556 = []

for blank_1000, cc464566, sx3556 in zip(blank_1000_set, cc464566_set, sx3556_set):

    cc464566 = blank_subtract(cc464566, vocs, session, blank=blank_1000)
    sx3556 = blank_subtract(sx3556, vocs, session, blank=blank_2500)

    # VOC standard CC464566 is 1000s sample, needs 1000s blank
    voc_quant = SampleQuant(sx3556, cc464566, blank_2500, cc464566_certification, standard_blank=blank_1000)
    voc_quant.quantify()

    vocs_in_sx3556.append(voc_quant)

compile_quant_report(vocs_in_sx3556, 'SX3556', 'CC464566', sx3556_certification.quantifications,
                     date=datetime(2018, 5, 16))

for cc416168, sx3556 in zip(cc416168_set, sx3556_set):
    cc416168 = blank_subtract(cc416168, vocs, session, blank=blank_2500)
    sx3556 = blank_subtract(sx3556, vocs, session, blank=blank_2500)

    # CC416168 defaults to using the same blank as the sample -- OK here
    all_quant = SampleQuant(sx3556, cc416168, blank_2500, cc416168_certification)
    all_quant.quantify()

    all_in_sx3556.append(all_quant)

compile_quant_report(all_in_sx3556, 'SX3556', 'CC416168', sx3556_certification.quantifications,
                     date=datetime(2018, 5, 16))


