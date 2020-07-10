"""
Quantify the two ambient runs on 2019_11_11, 2019_11_11_Ambient_[1/2] using the standard between them,
2019_11_11_CC416168. These were run without the water trap drying between runs to test a theory about the cause
of the regular amplitude between early and later day runs in H/CFCs.

Print a rough version to be edited in Excel.
"""
__package__ = 'Z'

from datetime import datetime

from settings import CORE_DIR, DB_NAME
from IO.db import connect_to_db, GcRun, Integration, Standard, SampleQuant

engine, session = connect_to_db(DB_NAME, CORE_DIR)


standard_to_quantify_with = session.query(Standard).filter(Standard.name == 'cc416168').one_or_none()
# get standard cert values for the quantifier

quantifier = (session.query(GcRun).join(Integration, Integration.run_id == GcRun.id)
              .filter(GcRun.date > datetime(2019, 11, 11), GcRun.date < datetime(2019, 11, 12))
              .filter(Integration.filename == '2019_11_11_CC416168.D')
              .order_by(GcRun.date)
              .one_or_none())

ambient_1 = (session.query(GcRun).join(Integration, Integration.run_id == GcRun.id)
             .filter(GcRun.date > datetime(2019, 11, 11), GcRun.date < datetime(2019, 11, 12))
             .filter(Integration.filename.like('%Ambient_1.D'))
             .order_by(GcRun.date)
             .one_or_none())

ambient_2 = (session.query(GcRun).join(Integration, Integration.run_id == GcRun.id)
             .filter(GcRun.date > datetime(2019, 11, 11), GcRun.date < datetime(2019, 11, 12))
             .filter(Integration.filename.like('%Ambient_2.D'))
             .order_by(GcRun.date)
             .one_or_none())

quant1 = SampleQuant(ambient_1, quantifier, None, standard_to_quantify_with)
quant1.quantify()

quant2 = SampleQuant(ambient_2, quantifier, None, standard_to_quantify_with)
quant2.quantify()

ambient_1 = session.merge(ambient_1)
ambient_2 = session.merge(ambient_2)

session.commit()  # save to DB so quantified values are kept for later use

file = CORE_DIR / 'analyses/quantifications/scripts/2019_11_11_no_trap_dry.csv'

# Quick and dirty file IO for this...
with file.open('w') as f:
    f.write(f' \tAmbient: {ambient_1.date}\tAmbient: {ambient_2.date}\n')
    for compound1, compound2 in zip(ambient_1.compounds, ambient_2.compounds):
        f.write(f'{compound1.name}\t{compound1.mr}\t{compound2.mr}\n')
