"""
A sequence of standards were run over three days to quantify and compare EMPA SX3555 vs CC416168.

The sequence was (CC416168, SX3555, Blank2500), which was run after normal runs for three days (2019-07-04 --> 06).
"""
__package__ = 'Z'
import datetime as dt
from datetime import datetime

from settings import CORE_DIR, DB_NAME
from IO.db import connect_to_db, GcRun, Integration, Standard, SampleQuant
from reporting import compile_quant_report

engine, session = connect_to_db(DB_NAME, CORE_DIR)

standard_to_quantify_with = session.query(Standard).filter(Standard.name == 'cc416168').one_or_none()
# get standard cert values for the quantifier
certified_values_of_sample = session.query(Standard).filter(Standard.name == 'sx3555').one().quantifications
# get standard cert values for the sample being quantified

days_with_standards = [datetime(2019, 7, 6), datetime(2019, 7, 7), datetime(2019, 7, 8)]

quant_runs = []

for day in days_with_standards:
    day_end = day + dt.timedelta(days=1)

    sample = (session.query(GcRun).join(Integration, Integration.run_id == GcRun.id)
              .filter(GcRun.date > day, GcRun.date < day_end)
              .filter(Integration.filename.like('%SX3555.D'))
              .order_by(GcRun.date)
              .one_or_none())

    quantifier = (session.query(GcRun).join(Integration, Integration.run_id == GcRun.id)
                  .filter(GcRun.date > day, GcRun.date < day_end)
                  .filter(Integration.filename.like('%CC416168.D'))
                  .order_by(GcRun.date)
                  .one_or_none())

    blank = (session.query(GcRun).join(Integration, Integration.run_id == GcRun.id)
             .filter(GcRun.date > day, GcRun.date < day_end)
             .filter(Integration.filename.like('%Blank2500.D'))
             .order_by(GcRun.date)
             .one_or_none())

    if not sample or not quantifier or not blank:
        print(f'Sample, standard or blank not found for {day}.')
        continue

    quant = SampleQuant(sample, quantifier, blank, standard_to_quantify_with)
    quant.quantify()

    quant_runs.append(quant)

compile_quant_report(quant_runs, 'SX3555', 'CC416168', certified_values_of_sample, date=datetime(2019, 7, 6))
# report for SX3555 Qx CC416168 finished, values to be re-assigned for vice versa

standard_to_quantify_with = session.query(Standard).filter(Standard.name == 'sx3555').one_or_none()
# get standard cert values for the quantifier
certified_values_of_sample = session.query(Standard).filter(Standard.name == 'cc416168').one().quantifications
# get standard cert values for the sample being quantified

quant_runs = []  # re-assign to quantify the other way around (CC4416168 Qx SX3555)
for day in days_with_standards:
    day_end = day + dt.timedelta(days=1)

    sample = (session.query(GcRun).join(Integration, Integration.run_id == GcRun.id)
              .filter(GcRun.date > day, GcRun.date < day_end)
              .filter(Integration.filename.like('%CC416168.D'))
              .order_by(GcRun.date)
              .one_or_none())

    quantifier = (session.query(GcRun).join(Integration, Integration.run_id == GcRun.id)
                  .filter(GcRun.date > day, GcRun.date < day_end)
                  .filter(Integration.filename.like('%SX3555.D'))
                  .order_by(GcRun.date)
                  .one_or_none())

    blank = (session.query(GcRun).join(Integration, Integration.run_id == GcRun.id)
             .filter(GcRun.date > day, GcRun.date < day_end)
             .filter(Integration.filename.like('%Blank2500.D'))
             .order_by(GcRun.date)
             .one_or_none())

    if not sample or not quantifier or not blank:
        print('Sample, standard or blank not found for {day}.')
        continue

    quant = SampleQuant(sample, quantifier, blank, standard_to_quantify_with)
    quant.quantify()

    quant_runs.append(quant)

compile_quant_report(quant_runs, 'CC416168', 'SX3555', certified_values_of_sample, date=datetime(2019, 7, 6))
