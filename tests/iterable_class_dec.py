from IO.db import connect_to_db, Integration, GcRun, Standard
from settings import DB_NAME, CORE_DIR

_, session = connect_to_db(DB_NAME, CORE_DIR)

for typ in (Integration, GcRun, Standard):
    print(f'\n\n{typ.__name__}s')
    instances = session.query(typ).limit(3).all()  # get a couple test types

    for instance in instances:
        print(f'\n{instance}')
        instance_iter = iter(instance)
        for _ in range(5):  # small iteration to show it works
            print(next(instance_iter))
