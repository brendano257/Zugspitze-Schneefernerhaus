from sqlalchemy.sql.expression import extract, not_

from IO.db.models import GcRun, Compound, Integration

__all__ = ['ambient_filters', 'final_data_first_sample_only_filter']

ambient_filters = [
    GcRun.type == 5,
    Compound.filtered == False,
]

final_data_first_sample_only_filter = [
    extract('hour', Integration.date) < 5,
    not_(Integration.filename.ilike('%/___a/_02.D', escape='/')),
    GcRun.type == 5
]
