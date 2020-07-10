"""
This quantifies and compares a room air run against an ambient run from just after it.
"""
__package__ = 'Z'

from datetime import datetime

from settings import CORE_DIR, DB_NAME
from IO.db import connect_to_db, GcRun, Integration, Standard
from processing import blank_subtract
from reporting import compile_enhancement_comparison

engine, session = connect_to_db(DB_NAME, CORE_DIR)

standard_run = (session.query(GcRun)
                .join(Integration, Integration.run_id == GcRun.id)
                .filter(Integration.filename == '2018_10_15_03.D')
                .one())

blank = (session.query(GcRun)
         .join(Integration, Integration.run_id == GcRun.id)
         .filter(Integration.filename == '2018_10_15_04.D')
         .one())

room = (session.query(GcRun)
        .join(Integration, Integration.run_id == GcRun.id)
        .filter(Integration.filename == '2018_10_15_room_2500.D')
        .one())

ambient = (session.query(GcRun)
           .join(Integration, Integration.run_id == GcRun.id)
           .filter(Integration.filename == '2018_10_15_ambient.D')
           .one())

standard = session.query(Standard).filter(Standard.name == 'cc416168').one()

voc_standard_list = session.query(Standard).filter(Standard.name == 'vocs').one()
vocs = [q.name for q in voc_standard_list.quantifications]

room.working_std = standard_run
room.standard = standard

room = blank_subtract(room, vocs, session, blank=blank)
room.quantify()

ambient.working_std = standard_run
ambient.standard = standard

ambient = blank_subtract(ambient, vocs, session, blank=blank)
ambient.quantify()

for run in [room, ambient]:
    session.merge(run)

session.commit()

compile_enhancement_comparison(ambient, room, date=datetime(2018, 10, 15), names=('Ambient', 'Room Air'), use_mrs=True)
