"""
A sequence of standards were run over three days to quantify and compare CC412022 vs CC416168 and vice versa.

The sequence was (CC412022, CC416168, Blank2500), which was run after normal runs for three days (2019-11-16 --> 18).
"""
__package__ = 'Z'

import datetime as dt
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

voc_standard_list = session.query(Standard).filter(Standard.name == 'vocs').one()
vocs = [q.name for q in voc_standard_list.quantifications]

days_with_standards = [datetime(2019, 11, 16), datetime(2019, 11, 17), datetime(2019, 11, 18)]

quant_runs = []

for day in days_with_standards:
    day_end = day + dt.timedelta(days=1)

    sample = (session.query(GcRun).join(Integration, Integration.run_id == GcRun.id)
              .filter(GcRun.date > day, GcRun.date < day_end)
              .filter(Integration.filename.like('%CC412022.D'))
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

    # print(sample.date)
    # print(f'Toluene sample: {search_for_attr_value(sample.compounds, "name", "toluene").pa}')
    # print(f'Toluene standard: {search_for_attr_value(quantifier.compounds, "name", "toluene").pa}')
    # print(f'Toluene blank: {search_for_attr_value(blank.compounds, "name", "toluene").pa}\n')

    if not sample or not quantifier or not blank:
        print(f'Sample, standard or blank not found for {day}.')
        continue

    sample = blank_subtract(sample, vocs, session, blank)
    quantifier = blank_subtract(quantifier, vocs, session, blank)

    quant = SampleQuant(sample, quantifier, blank, standard_to_quantify_with)
    quant.quantify()

    quant_runs.append(quant)

compile_quant_report(quant_runs, 'CC412022', 'CC416168', certified_values_of_sample, date=datetime(2019, 11, 16))
# report for CC412022 Qx CC416168 finished, values to be re-assigned for vice versa

standard_to_quantify_with = session.query(Standard).filter(Standard.name == 'cc412022_noaa_provided').one_or_none()
# get standard cert values for the quantifier
certified_values_of_sample = session.query(Standard).filter(Standard.name == 'cc416168').one().quantifications
# get standard cert values for the sample being quantified

quant_runs = []  # re-assign to quantify the other way around (CC416168 Qx CC412022)
for day in days_with_standards:
    day_end = day + dt.timedelta(days=1)

    sample = (session.query(GcRun).join(Integration, Integration.run_id == GcRun.id)
              .filter(GcRun.date > day, GcRun.date < day_end)
              .filter(Integration.filename.like('%CC416168.D'))
              .order_by(GcRun.date)
              .one_or_none())


    quantifier = (session.query(GcRun).join(Integration, Integration.run_id == GcRun.id)
                  .filter(GcRun.date > day, GcRun.date < day_end)
                  .filter(Integration.filename.like('%CC412022.D'))
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

    sample = blank_subtract(sample, vocs, session, blank)
    quantifier = blank_subtract(quantifier, vocs, session, blank)

    quant = SampleQuant(sample, quantifier, blank, standard_to_quantify_with)
    quant.quantify()

    quant_runs.append(quant)

compile_quant_report(quant_runs, 'CC416168', 'CC412022', certified_values_of_sample, date=datetime(2019, 11, 16))
