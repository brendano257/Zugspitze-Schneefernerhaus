__package__ = 'Z'

from datetime import datetime

from settings import CORE_DIR, DB_NAME
from IO.db import connect_to_db, GcRun, Integration, Standard
from processing import blank_subtract
from reporting import compile_enhancement_comparison

engine, session = connect_to_db(DB_NAME, CORE_DIR)

standard_run = (session.query(GcRun)
                .join(Integration, Integration.run_id == GcRun.id)
                .filter(Integration.filename == '2019_11_12f_CC416168.D')
                .one())

room = (session.query(GcRun)
        .join(Integration, Integration.run_id == GcRun.id)
        .filter(Integration.filename == '2019_11_12f_RoomAir.D')
        .one())

ambient = (session.query(GcRun)
           .join(Integration, Integration.run_id == GcRun.id)
           .filter(Integration.filename == '2019_11_13a_02.D')
           .one())

standard = session.query(Standard).filter(Standard.name == 'cc416168').one()

voc_standard_list = session.query(Standard).filter(Standard.name == 'vocs').one()
vocs = [q.name for q in voc_standard_list.quantifications]

quantlist = session.query(Standard).filter(Standard.name == 'quantlist').one().quantifications
quantlist = [q.name for q in quantlist]

room.working_std = standard_run
room.standard = standard

standard_run = blank_subtract(standard_run, vocs, session, blank=None, force_no_blank=True)

room = blank_subtract(room, vocs, session, blank=None, force_no_blank=True)
room.quantify()

ambient.working_std = standard_run
ambient.standard = standard

ambient = blank_subtract(ambient, vocs, session, blank=None, force_no_blank=True)
ambient.quantify()

compile_enhancement_comparison(ambient, room,
                               date=datetime(2019, 11, 12),
                               names=('Ambient', 'Room Air'),
                               use_mrs=True)
