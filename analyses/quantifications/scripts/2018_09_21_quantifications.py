"""
This quantifies the EMPA standard (SX3555) using CC416168 and CC464566, as well as quantifying CC416168 with CC464566.

Three sets of (CC416168, CC464566, Blank1000, SX3555) were run. The Blank1000 run is used to blank-subtract the
CC464566 run, which was done at 1000s sample time. A final Blank2500 run at the end is used for all other samples in all
sequences.
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
              .filter(Integration.filename == '2018_09_21_Blank2500.D')
              .one())

blank_1000_set = (session.query(GcRun)
                  .join(Integration, Integration.run_id == GcRun.id)
                  .filter(GcRun.date > datetime(2018, 9, 21), GcRun.date < datetime(2018, 9, 22))
                  .filter(Integration.filename.like('%Blank1000%.D'))
                  .order_by(Integration.date)
                  .all())

cc416168_set = (session.query(GcRun)
                .join(Integration, Integration.run_id == GcRun.id)
                .filter(GcRun.date > datetime(2018, 9, 21), GcRun.date < datetime(2018, 9, 22))
                .filter(Integration.filename.like('%CC416168%.D'))
                .order_by(Integration.date)
                .all())

cc464566_set = (session.query(GcRun)
                .join(Integration, Integration.run_id == GcRun.id)
                .filter(GcRun.date > datetime(2018, 9, 21), GcRun.date < datetime(2018, 9, 22))
                .filter(Integration.filename.like('%CC464566%.D'))
                .order_by(Integration.date)
                .all())

sx3555_set = (session.query(GcRun)
              .join(Integration, Integration.run_id == GcRun.id)
              .filter(GcRun.date > datetime(2018, 9, 21), GcRun.date < datetime(2018, 9, 22))
              .filter(Integration.filename.like('%SX3555%.D'))
              .order_by(Integration.date)
              .all())

vocs = session.query(Standard).filter(Standard.name == 'vocs').one()
vocs = [q.name for q in vocs.quantifications]

cc416168_certification = session.query(Standard).filter(Standard.name == 'cc416168').one()

cc464566_certification = session.query(Standard).filter(Standard.name == 'cc464566').one()

sx3555_certification = session.query(Standard).filter(Standard.name == 'sx3555').one()

# quantify VOCs in SX3555 with CC464566
vocs_in_sx3555 = []

for blank_1000, cc464566, sx3555 in zip(blank_1000_set, cc464566_set, sx3555_set):

    cc464566 = blank_subtract(cc464566, vocs, session, blank=blank_1000)
    sx3555 = blank_subtract(sx3555, vocs, session, blank=blank_2500)

    # VOC standard CC464566 is 1000s sample, needs 1000s blank
    voc_quant = SampleQuant(sx3555, cc464566, blank_2500, cc464566_certification, standard_blank=blank_1000)
    voc_quant.quantify()

    vocs_in_sx3555.append(voc_quant)

compile_quant_report(vocs_in_sx3555, 'SX3555', 'CC464566', sx3555_certification.quantifications,
                     date=datetime(2018, 9, 21))

# quantify all compounds in SX3555 with CC416168
all_in_sx3555 = []

for cc416168, sx3555 in zip(cc416168_set, sx3555_set):
    cc416168 = blank_subtract(cc416168, vocs, session, blank=blank_2500)
    sx3555 = blank_subtract(sx3555, vocs, session, blank=blank_2500)

    # CC416168 defaults to using the same blank as the sample -- OK here
    all_quant = SampleQuant(sx3555, cc416168, blank_2500, cc416168_certification)
    all_quant.quantify()

    all_in_sx3555.append(all_quant)

compile_quant_report(all_in_sx3555, 'SX3555', 'CC416168', sx3555_certification.quantifications,
                     date=datetime(2018, 9, 21))


# quantify VOCs in CC416168 with CC464566
vocs_in_cc416168 = []

for blank_1000, cc464566, cc416168 in zip(blank_1000_set, cc464566_set, cc416168_set):

    cc464566 = blank_subtract(cc464566, vocs, session, blank=blank_1000)
    cc416168 = blank_subtract(cc416168, vocs, session, blank=blank_2500)

    # VOC standard CC464566 is 1000s sample, needs 1000s blank
    voc_quant = SampleQuant(cc416168, cc464566, blank_2500, cc464566_certification, standard_blank=blank_1000)
    voc_quant.quantify()

    vocs_in_cc416168.append(voc_quant)

compile_quant_report(vocs_in_cc416168, 'CC416168', 'CC464566', cc416168_certification.quantifications,
                     date=datetime(2018, 9, 21))

# quantify all compounds in CC416168 with SX3555
all_in_cc416168 = []

for cc416168, sx3555 in zip(cc416168_set, sx3555_set):
    cc416168 = blank_subtract(cc416168, vocs, session, blank=blank_2500)
    sx3555 = blank_subtract(sx3555, vocs, session, blank=blank_2500)

    # SX3555 defaults to using the same blank as the sample -- OK here
    all_quant = SampleQuant(cc416168, sx3555, blank_2500, sx3555_certification)
    all_quant.quantify()

    all_in_cc416168.append(all_quant)

compile_quant_report(all_in_cc416168, 'CC416168', 'SX3555', cc416168_certification.quantifications,
                     date=datetime(2018, 9, 21))
