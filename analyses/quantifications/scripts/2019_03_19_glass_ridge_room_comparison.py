"""
A room air enhancement and ridgeline/glass stack comparison were run on 2019-03-19.

The room air was compared to it's nearest ambient sample, which was 2019_03_19a_02.D. The sequence was:

Standard (2019_03_19_03.D)
Ambient (2019_03_19a_02.D)
2500s Blank (2019_03_19_04.D)
Room Air (2019_03_19_Room2500.D)
Glass Stack (2019_03_19_GlassStack.D)
Ridge Air (2019_03_19_RidgeAir.D)
"""
__package__ = 'Z'

from datetime import datetime

from settings import CORE_DIR, DB_NAME
from IO.db import connect_to_db, GcRun, Integration, Standard
from processing import blank_subtract
from reporting import compile_enhancement_comparison

engine, session = connect_to_db(DB_NAME, CORE_DIR)

ridgeline = (session.query(GcRun)
             .join(Integration, Integration.run_id == GcRun.id)
             .filter(Integration.filename == '2019_03_19_RidgeAir.D')
             .one())

glass = (session.query(GcRun)
         .join(Integration, Integration.run_id == GcRun.id)
         .filter(Integration.filename == '2019_03_19_GlassStack.D')
         .one())

standard_run = (session.query(GcRun)
                .join(Integration, Integration.run_id == GcRun.id)
                .filter(Integration.filename == '2019_03_19_03.D')
                .one())

blank = (session.query(GcRun)
         .join(Integration, Integration.run_id == GcRun.id)
         .filter(Integration.filename == '2019_03_19_04.D')
         .one())

room = (session.query(GcRun)
        .join(Integration, Integration.run_id == GcRun.id)
        .filter(Integration.filename == '2019_03_19_Room2500.D')
        .one())

ambient = (session.query(GcRun)
           .join(Integration, Integration.run_id == GcRun.id)
           .filter(Integration.filename == '2019_03_19a_02.D')
           .one())

standard = session.query(Standard).filter(Standard.name == 'cc416168').one()

voc_standard_list = session.query(Standard).filter(Standard.name == 'vocs').one()
vocs = [q.name for q in voc_standard_list.quantifications]

ridgeline.working_std = standard_run
ridgeline.standard = standard

ridgeline = blank_subtract(ridgeline, vocs, session, blank=blank)

glass.working_std = standard_run
glass.standard = standard

glass = blank_subtract(glass, vocs, session, blank=blank)

room.working_std = standard_run
room.standard = standard

room = blank_subtract(room, vocs, session, blank=blank)
room.quantify()

ambient.working_std = standard_run
ambient.standard = standard

ambient = blank_subtract(ambient, vocs, session, blank=blank)
ambient.quantify()

for run in [ridgeline, glass, room, ambient]:
    session.merge(run)

session.commit()

compile_enhancement_comparison(ridgeline, glass, date=datetime(2019, 3, 19))

compile_enhancement_comparison(ambient, room, date=datetime(2019, 3, 19), names=('Ambient', 'Room Air'), use_mrs=True)
