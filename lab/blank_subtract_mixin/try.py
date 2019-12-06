from settings import DB_NAME, CORE_DIR
from IO.db import connect_to_db, GcRun


def test_blank_subtract_mixin():

    engine, session = connect_to_db(DB_NAME, CORE_DIR)

    runs = session.query(GcRun).filter(GcRun.quantified == True).all()[:100:4]

    for run in runs:
        run.blank_subtract(session=session)


if __name__ == '__main__':
    test_blank_subtract_mixin()